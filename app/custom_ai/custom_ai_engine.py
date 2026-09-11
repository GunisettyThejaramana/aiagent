"""
Fast local database AI engine.

Architecture:

    Question
        ↓
    MetricEngine
        ↓
    IntentEngine
        ↓
    EntityEngine
        ↓
    ReasoningEngine
        ↓
    QueryBuilder
        ↓
    PostgreSQL

Only when the deterministic pipeline cannot build a query:
        ↓
    Small local Ollama SQL fallback

Important:
    Ollama is NOT used for database routing.
    Ollama is NOT used for simple database answers.
    Deterministic SQL generation is preferred.
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from app.config import settings
from app.ollama_client import ollama_client

from app.custom_ai.database_knowledge_cache import (
    database_knowledge_cache,
)

from app.custom_ai.metric_engine import (
    MetricEngine,
)

from app.custom_ai.intent_engine import (
    IntentEngine,
)

from app.custom_ai.entity_engine import (
    EntityEngine,
)

from app.custom_ai.reasoning_engine import (
    ReasoningEngine,
)

from app.custom_ai.query_builder import (
    QueryBuilder,
)


# ================================================================
# SQL SAFETY
# ================================================================

FORBIDDEN_SQL = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "merge",
    "replace",
}


def validate_sql(sql: str) -> str:
    """
    Validate generated SQL.

    Only SELECT/WITH statements are permitted.
    Multiple statements are rejected.
    """

    if not sql:
        raise ValueError(
            "The AI did not generate SQL."
        )

    sql = str(sql).strip()

    # Remove markdown fences.
    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = re.sub(
        r"\s*```$",
        "",
        sql,
        flags=re.IGNORECASE,
    )

    sql = sql.rstrip(";").strip()

    # No multiple statements.
    if ";" in sql:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    # Only SELECT / WITH.
    if not re.match(
        r"^(select|with)\b",
        sql,
        flags=re.IGNORECASE,
    ):
        raise ValueError(
            "Only SELECT/WITH queries are allowed."
        )

    lowered = sql.lower()

    for keyword in FORBIDDEN_SQL:

        if re.search(
            rf"\b{re.escape(keyword)}\b",
            lowered,
        ):
            raise ValueError(
                f"Unsafe SQL keyword detected: {keyword}"
            )

    return sql


# ================================================================
# SAFE VALUE
# ================================================================

def safe_value(value):

    if isinstance(
        value,
        Decimal,
    ):
        return float(value)

    if isinstance(
        value,
        (date, datetime),
    ):
        return value.isoformat()

    try:
        json.dumps(value)
        return value

    except Exception:
        return str(value)


# ================================================================
# DATABASE AI ENGINE
# ================================================================

class CustomAIEngine:

    # ------------------------------------------------------------
    # Ollama fallback settings
    # ------------------------------------------------------------

    SQL_MODEL = getattr(
        settings,
        "OLLAMA_SQL_MODEL",
        getattr(
            settings,
            "OLLAMA_MODEL",
            "qwen3:4b",
        ),
    )

    SQL_CONTEXT = getattr(
        settings,
        "OLLAMA_SQL_CONTEXT",
        2048,
    )

    SQL_TIMEOUT = getattr(
        settings,
        "OLLAMA_SQL_TIMEOUT",
        30,
    )

    # ------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------

    def __init__(self):

        self.metric_engine = MetricEngine()

        self.intent_engine = IntentEngine()

        self.entity_engine = EntityEngine()

        self.reasoning_engine = ReasoningEngine()

        self.query_builder = QueryBuilder()

    # ============================================================
    # DATABASE SCHEMA
    # ============================================================

    def get_schema(
        self,
        engine,
        database_id=None,
    ):
        """
        Read schema from the local database knowledge cache.
        """

        key = (
            database_id
            if database_id is not None
            else f"engine:{id(engine)}"
        )

        return database_knowledge_cache.get_or_build(
            key,
            engine,
        )

    # ============================================================
    # SCHEMA ADAPTER
    # ============================================================

    @staticmethod
    def _convert_schema_for_engines(
        knowledge: dict,
    ) -> dict:
        """
        DatabaseKnowledgeCache uses:

            {
                "tables": {
                    "table_name": {
                        "table_name": "...",
                        "columns": [...]
                    }
                }
            }

        ReasoningEngine / QueryBuilder use:

            {
                "tables": [
                    {
                        "table_name": "...",
                        "columns": [...]
                    }
                ]
            }

        This adapter keeps both systems compatible.
        """

        if not isinstance(
            knowledge,
            dict,
        ):
            return {
                "tables": [],
                "relationships": [],
            }

        raw_tables = knowledge.get(
            "tables",
            {},
        )

        converted_tables = []

        # --------------------------------------------------------
        # Cache dictionary format
        # --------------------------------------------------------

        if isinstance(
            raw_tables,
            dict,
        ):

            for table_name, info in raw_tables.items():

                if not isinstance(
                    info,
                    dict,
                ):
                    info = {}

                columns = info.get(
                    "columns",
                    [],
                )

                normalized_columns = []

                for column in columns:

                    if isinstance(
                        column,
                        dict,
                    ):

                        normalized_columns.append(
                            {
                                "name": column.get(
                                    "name",
                                    "",
                                ),
                                "type": column.get(
                                    "type",
                                    "",
                                ),
                            }
                        )

                    else:

                        normalized_columns.append(
                            {
                                "name": str(column),
                                "type": "",
                            }
                        )

                converted_tables.append(
                    {
                        "table_name": str(
                            info.get(
                                "table_name",
                                table_name,
                            )
                        ),
                        "columns": normalized_columns,
                    }
                )

        # --------------------------------------------------------
        # Already-converted list format
        # --------------------------------------------------------

        elif isinstance(
            raw_tables,
            list,
        ):

            for info in raw_tables:

                if not isinstance(
                    info,
                    dict,
                ):
                    continue

                converted_tables.append(
                    {
                        "table_name": str(
                            info.get(
                                "table_name",
                                "",
                            )
                        ),
                        "columns": info.get(
                            "columns",
                            [],
                        ),
                    }
                )

        # --------------------------------------------------------
        # Relationships
        # --------------------------------------------------------

        relationships = knowledge.get(
            "relationships",
            [],
        )

        if not isinstance(
            relationships,
            list,
        ):
            relationships = []

        return {
            "tables": converted_tables,
            "relationships": relationships,
        }

    # ============================================================
    # SIMPLE DATABASE REQUESTS
    # ============================================================

    @staticmethod
    def _simple_schema_answer(
        question,
        knowledge,
    ):
        """
        Handle questions that don't require SQL.
        """

        q = str(
            question or ""
        ).lower().strip()

        raw_tables = knowledge.get(
            "tables",
            {},
        )

        if isinstance(
            raw_tables,
            dict,
        ):
            tables = list(
                raw_tables.keys()
            )

        elif isinstance(
            raw_tables,
            list,
        ):
            tables = [
                item.get(
                    "table_name"
                )
                for item in raw_tables
                if isinstance(
                    item,
                    dict,
                )
                and item.get(
                    "table_name"
                )
            ]

        else:
            tables = []

        patterns = (
            "show all the database",
            "show all database",
            "list all tables",
            "list the tables",
            "what tables are there",
            "show database tables",
            "show all tables",
            "list tables",
            "what are the tables",
            "what tables exist",
        )

        if any(
            pattern in q
            for pattern in patterns
        ):

            if not tables:

                return (
                    "The selected database has no readable tables.",
                    {
                        "type": "list_tables",
                        "tables": [],
                    },
                )

            answer = (
                "Tables in the selected database:\n\n"
                + "\n".join(
                    f"{index}. {name}"
                    for index, name in enumerate(
                        tables,
                        1,
                    )
                )
            )

            return (
                answer,
                {
                    "type": "list_tables",
                    "tables": tables,
                },
            )

        return (
            None,
            None,
        )

    # ============================================================
    # OLLAMA SQL FALLBACK
    # ============================================================

    def generate_sql_with_ollama(
        self,
        question,
        schema_text,
    ):
        """
        Ollama is used ONLY when deterministic SQL generation
        cannot resolve the question.
        """

        system_prompt = (
            "Convert the user's question into ONE safe PostgreSQL "
            "SELECT query. "
            "Use only the supplied schema. "
            "Never invent tables or columns. "
            "Use SUM for total/overall questions. "
            "Use COUNT for record-count questions. "
            "Use AVG for average questions. "
            "Use MAX for maximum questions. "
            "Use MIN for minimum questions. "
            "Return JSON only: "
            '{"sql":"SELECT ..."}'
            ". "
            "Do not explain. "
            "Do not use INSERT, UPDATE, DELETE, DROP, ALTER, "
            "CREATE, TRUNCATE, GRANT, REVOKE, or multiple statements."
        )

        user_prompt = (
            f"SCHEMA:\n"
            f"{schema_text}\n\n"
            f"QUESTION:\n"
            f"{question}"
        )

        return ollama_client.generate_json(
            system_prompt,
            user_prompt,
            think=False,
            model=self.SQL_MODEL,
            num_ctx=self.SQL_CONTEXT,
            num_predict=96,
            timeout=self.SQL_TIMEOUT,
        )

    # ============================================================
    # SQL EXECUTION
    # ============================================================


    def execute_sql(
        self,
        engine,
        sql,
        params=None,
    ):
        """
        Safely execute a SELECT/WITH query.

        QueryBuilder may generate named parameters such as
        :date_start and :date_end. Those parameters are passed
        directly to SQLAlchemy.
        """
        sql = validate_sql(sql)
        params = params or {}

        with engine.connect() as connection:
            result = connection.execute(
                text(sql),
                params,
            )

            columns = list(result.keys())
            rows = []

            for row in result.fetchmany(100):
                rows.append(
                    {
                        column: safe_value(value)
                        for column, value in zip(columns, row)
                    }
                )

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "sql": sql,
        }

    # ============================================================
    # LOCAL ANSWER FORMATTER
    # ============================================================

    @staticmethod
    def local_answer(
        question,
        rows,
    ):
        """
        Format database results without another LLM call.

        This is especially important for aggregate queries.

        Example:

            SELECT SUM(total_balance)
            -> 12500

        Answer:

            Total balance: 12500
        """

        if not rows:

            return (
                "I couldn't find any matching records "
                "for your question."
            )

        # --------------------------------------------------------
        # Single aggregate row
        # --------------------------------------------------------

        if len(rows) == 1:

            row = rows[0]

            if len(row) == 1:

                key, value = next(
                    iter(
                        row.items()
                    )
                )

                if value is None:

                    return (
                        "No value was found "
                        "for that calculation."
                    )

                label = re.sub(
                    r"_+",
                    " ",
                    str(key),
                ).strip()

                label = label.capitalize()

                return (
                    f"{label}: {value}"
                )

            parts = []

            for key, value in row.items():

                label = re.sub(
                    r"_+",
                    " ",
                    str(key),
                ).strip()

                label = label.capitalize()

                parts.append(
                    f"{label}: {value}"
                )

            return "\n".join(
                parts
            )

        # --------------------------------------------------------
        # Multiple records
        # --------------------------------------------------------

        parts = []

        for row in rows[:20]:

            row_parts = []

            for key, value in row.items():

                label = re.sub(
                    r"_+",
                    " ",
                    str(key),
                ).strip()

                label = label.capitalize()

                row_parts.append(
                    f"{label}: {value}"
                )

            parts.append(
                " | ".join(
                    row_parts
                )
            )

        if parts:

            return "\n".join(
                parts
            )

        return (
            f"The database returned "
            f"{len(rows)} records."
        )

    # ============================================================
    # FINAL DATABASE ANSWER
    # ============================================================

    def generate_answer(
        self,
        question,
        execution,
        sql,
        language="en-US",
    ):
        """
        Database answers are formatted locally.

        No Ollama call is required for normal database results.
        """

        return self.local_answer(
            question,
            execution.get(
                "rows",
                [],
            ),
        )

    # ============================================================
    # RESULT HELPER
    # ============================================================

    @staticmethod
    def _result(
        started,
        **kwargs,
    ):

        kwargs[
            "processing_time"
        ] = round(
            time.perf_counter()
            - started,
            3,
        )

        return kwargs

    # ============================================================
    # DETERMINISTIC DATABASE PIPELINE
    # ============================================================

    def _deterministic_query(
        self,
        question,
        knowledge,
    ):
        """
        Run:

            MetricEngine
            IntentEngine
            EntityEngine
            ReasoningEngine
            QueryBuilder

        Returns:

            {
                metric,
                intent,
                entities,
                reasoning,
                query
            }
        """

        schema = (
            self._convert_schema_for_engines(
                knowledge
            )
        )

        # --------------------------------------------------------
        # Metric
        # --------------------------------------------------------

        metric_result = (
            self.metric_engine.understand(
                question
            )
        )

        print(
            "Metric result:",
            metric_result,
        )

        # --------------------------------------------------------
        # Intent
        # --------------------------------------------------------

        intent_result = (
            self.intent_engine.understand(
                question
            )
        )

        print(
            "Intent result:",
            intent_result,
        )

        # --------------------------------------------------------
        # Entities
        # --------------------------------------------------------

        entity_result = (
            self.entity_engine.extract(
                question
            )
        )

        print(
            "Entity result:",
            entity_result,
        )

        # --------------------------------------------------------
        # Reasoning
        # --------------------------------------------------------

        reasoning_result = (
            self.reasoning_engine.reason(
                question=question,
                intent_result=intent_result,
                entity_result=entity_result,
                schema=schema,
                metric_result=metric_result,
                business_context_result=None,
            )
        )

        selected_table = (
            reasoning_result.get(
                "selected_table"
            )
        )

        print(
            "Selected table:",
            (
                selected_table.get(
                    "table_name"
                )
                if selected_table
                else None
            ),
        )

        # --------------------------------------------------------
        # Query Builder
        # --------------------------------------------------------

        query_result = (
            self.query_builder.build(
                question=question,
                intent_result=intent_result,
                entity_result=entity_result,
                reasoning_result=reasoning_result,
                schema=schema,
                metric_result=metric_result,
                query_plan=None,
            )
        )

        print(
            "Query builder result:",
            query_result,
        )

        return {
            "schema": schema,
            "metric": metric_result,
            "intent": intent_result,
            "entities": entity_result,
            "reasoning": reasoning_result,
            "query": query_result,
        }



































    # ============================================================
    # MAIN PROCESS
    # ============================================================

    def process(
        self,
        question,
        engine,
        database_id=None,
        language="en-US",
        allow_ollama_fallback=True,
    ):

        started = time.perf_counter()

        question = str(
            question or ""
        ).strip()

        # --------------------------------------------------------
        # Empty question
        # --------------------------------------------------------

        if not question:

            return self._result(
                started,
                success=False,
                question=question,
                answer=(
                    "Please enter a database question."
                ),
                sql=None,
                execution={
                    "success": False,
                    "reason": "Empty question",
                },
            )

        # --------------------------------------------------------
        # Schema
        # --------------------------------------------------------

        try:

            knowledge = self.get_schema(
                engine,
                database_id,
            )

        except Exception as exc:

            print(
                "Database schema error:",
                exc,
            )

            return self._result(
                started,
                success=False,
                question=question,
                answer=(
                    "I could not read the "
                    "database schema."
                ),
                sql=None,
                execution={
                    "success": False,
                    "reason": str(exc),
                },
            )

        # --------------------------------------------------------
        # Instant schema requests
        # --------------------------------------------------------

        instant_answer, instant_meta = (
            self._simple_schema_answer(
                question,
                knowledge,
            )
        )

        if instant_answer is not None:

            return self._result(
                started,
                success=True,
                question=question,
                sql=None,
                answer=instant_answer,
                execution={
                    "success": True,
                    "rows": [],
                    "columns": [],
                },
                query_plan=instant_meta,
                database_knowledge_cached=True,
                ai_engine="deterministic",
            )

        # --------------------------------------------------------
        # DETERMINISTIC PIPELINE
        # --------------------------------------------------------

        try:

            pipeline = (
                self._deterministic_query(
                    question,
                    knowledge,
                )
            )

            query_result = pipeline[
                "query"
            ]

        except Exception as exc:

            print(
                "Deterministic database pipeline error:",
                exc,
            )

            pipeline = None

            query_result = {
                "success": False,
                "reason": str(exc),
            }

        # --------------------------------------------------------
        # Successful deterministic SQL
        # --------------------------------------------------------

        if (
            isinstance(
                query_result,
                dict,
            )
            and query_result.get(
                "success"
            )
            and query_result.get(
                "sql"
            )
        ):

            sql = query_result[
                "sql"
            ]

            print()
            print(
                "========================================"
            )
            print(
                "DETERMINISTIC SQL"
            )
            print(
                "========================================"
            )
            print(
                sql
            )
            print(
                "========================================"
            )

            # ----------------------------------------------------
            # Execute
            # ----------------------------------------------------

            try:

                execution = (
                    self.execute_sql(
                        engine,
                        sql,
                        query_result.get(
                            "params",
                            {},
                        ),
                    )
                )

            except Exception as exc:

                print(
                    "Deterministic SQL execution error:",
                    exc,
                )

                execution = {
                    "success": False,
                    "reason": str(exc),
                    "rows": [],
                    "columns": [],
                }

            # ----------------------------------------------------
            # Successful execution
            # ----------------------------------------------------

            if execution.get(
                "success"
            ):

                rows = execution.get(
                    "rows",
                    [],
                )

                answer = (
                    self.generate_answer(
                        question,
                        execution,
                        sql,
                        language,
                    )
                )

                print(
                    "Rows returned:",
                    len(rows),
                )

                print(
                    "LOCAL DATABASE ANSWER - "
                    "Ollama skipped"
                )

                return self._result(
                    started,
                    success=True,
                    question=question,
                    sql=sql,
                    answer=answer,
                    execution=execution,
                    metric=pipeline[
                        "metric"
                    ],
                    intent=pipeline[
                        "intent"
                    ],
                    entities=pipeline[
                        "entities"
                    ],
                    reasoning=pipeline[
                        "reasoning"
                    ],
                    query_plan={
                        "type": "deterministic",
                    },
                    database_knowledge_cached=True,
                    ai_engine="deterministic",
                )

        # --------------------------------------------------------
        # DETERMINISTIC PIPELINE FAILED
        # --------------------------------------------------------

        # AUTO source detection uses the deterministic database pipeline
        # as a capability probe. Never call Ollama merely to decide whether
        # a question belongs to the database.
        if not allow_ollama_fallback:
            return self._result(
                started,
                success=False,
                question=question,
                sql=None,
                answer="Database deterministic pipeline could not resolve this question.",
                execution={
                    "success": False,
                    "reason": "Deterministic database pipeline could not resolve the question.",
                    "rows": [],
                    "columns": [],
                },
                query=pipeline,
                query_plan={
                    "type": "deterministic_probe_failed",
                },
                database_knowledge_cached=True,
                ai_engine="deterministic_probe",
            )

        print()
        print(
            "Deterministic SQL generation "
            "could not resolve the question."
        )

        # --------------------------------------------------------
        # Build small schema for Ollama
        # --------------------------------------------------------

        try:

            schema = (
                self._convert_schema_for_engines(
                    knowledge
                )
            )

            selected_tables = []

            if pipeline:

                reasoning = pipeline.get(
                    "reasoning",
                    {},
                )

                candidates = reasoning.get(
                    "candidate_tables",
                    [],
                )

                for candidate in candidates[:3]:

                    table_name = candidate.get(
                        "table_name"
                    )

                    if table_name:
                        selected_tables.append(
                            table_name
                        )

            if not selected_tables:

                selected_tables = [
                    table.get(
                        "table_name"
                    )
                    for table in schema.get(
                        "tables",
                        [],
                    )[:3]
                    if table.get(
                        "table_name"
                    )
                ]

            schema_text_parts = []

            for table in schema.get(
                "tables",
                [],
            ):

                table_name = table.get(
                    "table_name"
                )

                if table_name not in selected_tables:
                    continue

                columns = table.get(
                    "columns",
                    [],
                )

                column_text = ", ".join(
                    f"{column.get('name')}:{column.get('type','')}"
                    for column in columns
                )

                schema_text_parts.append(
                    f"TABLE {table_name}: "
                    f"{column_text}"
                )

            schema_text = "\n".join(
                schema_text_parts
            )

            if not schema_text:

                return self._result(
                    started,
                    success=False,
                    question=question,
                    sql=None,
                    answer=(
                        "I could not determine "
                        "which database information "
                        "is required for that question."
                    ),
                    execution={
                        "success": False,
                        "reason": (
                            "No suitable schema "
                            "was found."
                        ),
                    },
                    ai_engine="deterministic",
                )

            print()
            print(
                "========================================"
            )
            print(
                "OLLAMA SQL FALLBACK"
            )
            print(
                "Schema chars:",
                len(schema_text),
            )
            print(
                "========================================"
            )

            # ----------------------------------------------------
            # Ollama fallback
            # ----------------------------------------------------

            plan = (
                self.generate_sql_with_ollama(
                    question,
                    schema_text,
                )
            )

            sql = (
                plan.get("sql")
                if isinstance(
                    plan,
                    dict,
                )
                else None
            )

            if not sql:

                return self._result(
                    started,
                    success=False,
                    question=question,
                    answer=(
                        "I could not generate "
                        "a database query for "
                        "that question."
                    ),
                    sql=None,
                    execution={
                        "success": False,
                        "reason": (
                            "Ollama returned "
                            "no SQL."
                        ),
                    },
                    query=plan,
                    ai_engine="ollama_fallback",
                )

            # ----------------------------------------------------
            # Validate
            # ----------------------------------------------------

            sql = validate_sql(
                sql
            )

            # ----------------------------------------------------
            # Execute fallback SQL
            # ----------------------------------------------------

            execution = (
                self.execute_sql(
                    engine,
                    sql,
                    {},
                )
            )

            rows = execution.get(
                "rows",
                [],
            )

            answer = (
                self.local_answer(
                    question,
                    rows,
                )
            )

            print(
                "Fallback SQL:",
                sql,
            )

            print(
                "Rows returned:",
                len(rows),
            )

            return self._result(
                started,
                success=True,
                question=question,
                sql=sql,
                answer=answer,
                execution=execution,
                query=plan,
                query_plan={
                    "type": "ollama_fallback",
                },
                database_knowledge_cached=True,
                ai_engine="ollama_fallback",
            )

        except Exception as exc:

            print(
                "Ollama SQL fallback error:",
                exc,
            )

            return self._result(
                started,
                success=False,
                question=question,
                sql=None,
                answer=(
                    "I could not determine a safe "
                    "database query for that question."
                ),
                execution={
                    "success": False,
                    "reason": str(exc),
                },
                ai_engine="ollama_fallback",
            )


# ================================================================
# GLOBAL ENGINE
# ================================================================

custom_ai_engine = CustomAIEngine()