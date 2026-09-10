"""
Ollama-powered database AI engine.

Flow:

Question
   ↓
Schema discovery
   ↓
Ollama understands question
   ↓
Ollama creates SQL
   ↓
SQL safety validation
   ↓
Database
   ↓
Ollama explains result
"""

from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from app.ollama_client import ollama_client
from app.custom_ai.database_knowledge_cache import (
    database_knowledge_cache,
)


# ============================================================
# SQL SAFETY
# ============================================================

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

    if not sql:

        raise ValueError(
            "The AI did not generate SQL."
        )

    sql = sql.strip()

    # Remove markdown code fences.
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

    sql = sql.strip()

    # Only one statement.
    if ";" in sql[:-1]:

        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

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

    return sql.rstrip(";").strip()


# ============================================================
# JSON SERIALIZATION
# ============================================================

def safe_value(value):

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    try:
        json.dumps(value)
        return value

    except Exception:
        return str(value)


# ============================================================
# ENGINE
# ============================================================

class CustomAIEngine:

    # ========================================================
    # SCHEMA
    # ========================================================

    def get_schema(
        self,
        engine,
        database_id=None,
    ):

        cache_key = (
            database_id
            if database_id is not None
            else f"engine:{id(engine)}"
        )

        knowledge = (
            database_knowledge_cache.get_or_build(
                cache_key,
                engine,
            )
        )

        return knowledge

    # ========================================================
    # FORMAT SCHEMA FOR OLLAMA
    # ========================================================

    def schema_text(
        self,
        knowledge,
    ) -> str:

        tables = knowledge.get(
            "tables",
            {},
        )

        relationships = knowledge.get(
            "relationships",
            [],
        )

        parts = []

        for table_name, info in tables.items():

            columns = info.get(
                "columns",
                [],
            )

            column_lines = []

            for column in columns:

                if isinstance(column, dict):

                    name = column.get(
                        "name",
                        "",
                    )

                    data_type = column.get(
                        "type",
                        "",
                    )

                else:

                    name = str(column)
                    data_type = ""

                column_lines.append(
                    f"- {name} ({data_type})"
                )

            parts.append(
                f"TABLE: {table_name}\n"
                + "\n".join(column_lines)
            )

        if relationships:

            parts.append(
                "RELATIONSHIPS:\n"
                + json.dumps(
                    relationships,
                    indent=2,
                    default=str,
                )
            )

        return "\n\n".join(parts)

    # ========================================================
    # ASK OLLAMA FOR SQL
    # ========================================================

    def generate_sql_with_ollama(
        self,
        question,
        schema_text,
    ):

        system_prompt = """
You are an expert PostgreSQL query planner.

Your job is to translate a user's natural-language question
into a SAFE read-only PostgreSQL query.

You have access only to the schema supplied by the application.

IMPORTANT:

1. Use only tables and columns present in the schema.
2. Never invent a table.
3. Never invent a column.
4. Only generate SELECT or WITH queries.
5. Never generate INSERT.
6. Never generate UPDATE.
7. Never generate DELETE.
8. Never generate DROP.
9. Never generate ALTER.
10. Never generate CREATE.
11. Never generate TRUNCATE.
12. Use JOINs when the schema relationships require them.
13. Understand natural language dates such as:
    - today
    - yesterday
    - this month
    - last month
    - this year
    - last year
    - this quarter
    - last quarter
14. Understand:
    - total
    - sum
    - average
    - minimum
    - maximum
    - highest
    - lowest
    - count
    - top
    - bottom
    - percentage
    - comparison
    - growth
    - difference
15. If the question asks for a ranking, use ORDER BY and LIMIT.
16. If grouping is required, use GROUP BY.
17. Use PostgreSQL syntax.
18. Return ONLY JSON.

JSON format:

{
    "sql": "SELECT ...",
    "intent": "short description",
    "tables": ["table1"],
    "columns": ["column1"],
    "explanation": "short explanation"
}
"""

        user_prompt = f"""
DATABASE SCHEMA:

{schema_text}

USER QUESTION:

{question}

Generate the safest and most accurate PostgreSQL query.
"""

        result = ollama_client.generate_json(
            system_prompt,
            user_prompt,
        )

        return result

    # ========================================================
    # EXECUTE
    # ========================================================

    def execute_sql(
        self,
        engine,
        sql,
    ):

        sql = validate_sql(sql)

        with engine.connect() as connection:

            result = connection.execute(
                text(sql)
            )

            columns = list(
                result.keys()
            )

            rows = []

            for row in result.fetchmany(100):

                rows.append(
                    {
                        column: safe_value(value)
                        for column, value
                        in zip(
                            columns,
                            row,
                        )
                    }
                )

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "sql": sql,
        }

    # ========================================================
    # ANSWER
    # ========================================================

    def generate_answer(
        self,
        question,
        execution,
        sql,
        language="en-US",
    ):

        rows = execution.get(
            "rows",
            [],
        )

        if not rows:

            return (
                "I couldn't find any records matching "
                "your question."
            )

        result_text = json.dumps(
            rows,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        return ollama_client.generate(
            """
You are an enterprise database answer assistant.

Answer the user's question using ONLY the query result.

Be natural and concise.

Rules:

- Do not invent facts.
- Do not change numbers.
- If the result contains one value, clearly state it.
- If the result contains multiple rows, summarize them.
- If appropriate, use bullets.
- Do not explain SQL unless asked.
""",
            f"""
USER QUESTION:

{question}

SQL:

{sql}

QUERY RESULT:

{result_text}

Give the final answer.
""",
            temperature=0.1,
        )

    # ========================================================
    # PROCESS
    # ========================================================

    def process(
        self,
        question,
        engine,
        database_id=None,
        language="en-US",
    ):

        started = time.perf_counter()

        # ----------------------------------------------------
        # OLLAMA CHECK
        # ----------------------------------------------------

        if not ollama_client.is_available():

            return {
                "success": False,
                "answer": (
                    "The local Ollama service is not running. "
                    "Please start Ollama and try again."
                ),
                "sql": None,
                "execution": {
                    "success": False,
                    "reason": "Ollama unavailable",
                },
                "processing_time": round(
                    time.perf_counter() - started,
                    3,
                ),
            }

        # ----------------------------------------------------
        # EXPLICIT SQL
        # ----------------------------------------------------

        if re.match(
            r"^\s*(select|with)\b",
            question,
            flags=re.IGNORECASE,
        ):

            try:

                sql = validate_sql(
                    question
                )

                execution = self.execute_sql(
                    engine,
                    sql,
                )

                answer = self.generate_answer(
                    question,
                    execution,
                    sql,
                    language,
                )

                return {
                    "success": True,
                    "question": question,
                    "sql": sql,
                    "answer": answer,
                    "execution": execution,
                    "query": {
                        "sql": sql,
                    },
                    "intent": "explicit SQL query",
                    "entities": [],
                    "metric": None,
                    "query_plan": {
                        "type": "explicit_sql",
                    },
                    "database_knowledge_cached": True,
                    "processing_time": round(
                        time.perf_counter() - started,
                        3,
                    ),
                }

            except Exception as exc:

                return {
                    "success": False,
                    "answer": str(exc),
                    "sql": question,
                    "execution": {
                        "success": False,
                        "reason": str(exc),
                    },
                    "processing_time": round(
                        time.perf_counter() - started,
                        3,
                    ),
                }

        # ----------------------------------------------------
        # SCHEMA
        # ----------------------------------------------------

        knowledge = self.get_schema(
            engine,
            database_id,
        )

        schema_text = self.schema_text(
            knowledge
        )

        # ----------------------------------------------------
        # SQL GENERATION
        # ----------------------------------------------------

        try:

            plan = self.generate_sql_with_ollama(
                question,
                schema_text,
            )

        except Exception as exc:

            return {
                "success": False,
                "answer": (
                    "I could not understand the database "
                    "question using the local AI model."
                ),
                "sql": None,
                "execution": {
                    "success": False,
                    "reason": str(exc),
                },
                "processing_time": round(
                    time.perf_counter() - started,
                    3,
                ),
            }

        sql = plan.get(
            "sql"
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        try:

            sql = validate_sql(
                sql
            )

        except Exception as exc:

            return {
                "success": False,
                "answer": (
                    "The AI generated an invalid or "
                    "unsafe database query."
                ),
                "sql": sql,
                "execution": {
                    "success": False,
                    "reason": str(exc),
                },
                "query": plan,
                "processing_time": round(
                    time.perf_counter() - started,
                    3,
                ),
            }

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

        try:

            execution = self.execute_sql(
                engine,
                sql,
            )

        except Exception as exc:

            return {
                "success": False,
                "answer": (
                    "I generated a database query, "
                    "but the database could not execute it."
                ),
                "sql": sql,
                "execution": {
                    "success": False,
                    "reason": str(exc),
                },
                "query": plan,
                "processing_time": round(
                    time.perf_counter() - started,
                    3,
                ),
            }

        # ----------------------------------------------------
        # ANSWER
        # ----------------------------------------------------

        try:

            answer = self.generate_answer(
                question,
                execution,
                sql,
                language,
            )

        except Exception as exc:

            print(
                "Ollama answer generation error:",
                exc,
            )

            answer = (
                f"Query completed successfully and "
                f"returned {execution['row_count']} "
                f"record(s)."
            )

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        elapsed = (
            time.perf_counter() - started
        )

        return {
            "success": True,

            "question": question,

            "sql": sql,

            "answer": answer,

            "execution": execution,

            "query": plan,

            "intent": plan.get(
                "intent"
            ),

            "entities": plan.get(
                "columns",
                [],
            ),

            "metric": None,

            "query_plan": plan,

            "database_knowledge_cached": True,

            "processing_time": round(
                elapsed,
                3,
            ),
        }

    # ========================================================
    # COMPATIBILITY
    # ========================================================

    def answer(
        self,
        question,
        engine,
        database_id=None,
    ):

        return self.process(
            question,
            engine,
            database_id=database_id,
        )


# ============================================================
# GLOBAL ENGINE
# ============================================================

custom_ai_engine = CustomAIEngine()