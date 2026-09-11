"""Fast local database AI engine.

Design goal: one small Ollama call at most for a database question.
Schema selection and result formatting are handled locally.
"""
from __future__ import annotations

import json
import re
import time
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text

from app.ollama_client import ollama_client
from app.config import settings
from app.custom_ai.database_knowledge_cache import database_knowledge_cache

FORBIDDEN_SQL = {
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "grant", "revoke", "merge", "replace",
}


def validate_sql(sql: str) -> str:
    if not sql:
        raise ValueError("The AI did not generate SQL.")
    sql = str(sql).strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.I)
    sql = re.sub(r"\s*```$", "", sql, flags=re.I).strip()
    sql = sql.rstrip(";").strip()
    if ";" in sql:
        raise ValueError("Multiple SQL statements are not allowed.")
    if not re.match(r"^(select|with)\b", sql, flags=re.I):
        raise ValueError("Only SELECT/WITH queries are allowed.")
    lowered = sql.lower()
    for keyword in FORBIDDEN_SQL:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            raise ValueError(f"Unsafe SQL keyword detected: {keyword}")
    return sql


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


class CustomAIEngine:
    SQL_MODEL = getattr(settings, "OLLAMA_SQL_MODEL", "qwen3:4b")
    SQL_CONTEXT = getattr(settings, "OLLAMA_SQL_CONTEXT", 2048)
    SQL_TIMEOUT = getattr(settings, "OLLAMA_SQL_TIMEOUT", 30)

    def get_schema(self, engine, database_id=None):
        key = database_id if database_id is not None else f"engine:{id(engine)}"
        return database_knowledge_cache.get_or_build(key, engine)

    @staticmethod
    def _tokens(value: str) -> set[str]:
        return {
            x for x in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]+", str(value).lower())
            if len(x) > 1
        }

    def select_relevant_tables(self, knowledge, question, max_tables=3):
        """Select only tables useful for the question, then add one-hop FK neighbors."""
        tables = knowledge.get("tables", {}) or {}
        relationships = knowledge.get("relationships", []) or []
        q = str(question).lower()
        q_tokens = self._tokens(q)
        stop = {
            "what", "which", "where", "when", "who", "show", "give", "tell",
            "the", "all", "for", "from", "with", "about", "does", "are", "is",
            "how", "many", "can", "you", "please", "last", "this", "that",
            "total", "get", "list", "me", "and", "or", "of", "in", "on",
        }
        q_tokens -= stop
        scored = []
        for table_name, info in tables.items():
            score = 0
            tn = str(table_name).lower()
            tt = self._tokens(tn)
            if tn in q:
                score += 12
            score += 6 * len(q_tokens & tt)
            for col in (info.get("columns", []) or []):
                name = col.get("name", "") if isinstance(col, dict) else str(col)
                cn = str(name).lower()
                ct = self._tokens(cn)
                if cn and cn in q:
                    score += 9
                score += 4 * len(q_tokens & ct)
            if score:
                scored.append((score, table_name))
        scored.sort(key=lambda x: (-x[0], str(x[1])))
        selected = [name for _, name in scored[:max_tables]]

        if not selected:
            # Conservative fallback: tables whose names are common business concepts.
            preferred = [
                "sales", "orders", "customers", "employees", "weavers",
                "payments", "revenue", "inventory", "stock", "users",
            ]
            for name in preferred:
                if name in tables and name not in selected:
                    selected.append(name)
                if len(selected) >= max_tables:
                    break
        if not selected:
            selected = list(tables.keys())[:max_tables]

        # Add only direct FK neighbors when there is room.
        for rel in relationships:
            a = rel.get("source_table") or rel.get("from_table")
            b = rel.get("target_table") or rel.get("to_table")
            if a in selected and b in tables and b not in selected and len(selected) < max_tables:
                selected.append(b)
            elif b in selected and a in tables and a not in selected and len(selected) < max_tables:
                selected.append(a)
        return selected

    def schema_text(self, knowledge, table_names=None) -> str:
        tables = knowledge.get("tables", {}) or {}
        relationships = knowledge.get("relationships", []) or []
        selected = set(table_names or tables.keys())
        parts = []
        for table_name in table_names or tables.keys():
            info = tables.get(table_name, {})
            cols = []
            for col in info.get("columns", []) or []:
                if isinstance(col, dict):
                    cols.append(f"{col.get('name','')}:{col.get('type','')}")
                else:
                    cols.append(str(col))
            parts.append(f"TABLE {table_name}: " + ", ".join(cols))
        rels = []
        for rel in relationships:
            a = rel.get("source_table") or rel.get("from_table")
            b = rel.get("target_table") or rel.get("to_table")
            if a in selected and b in selected:
                ac = rel.get("source_column") or rel.get("from_column") or ""
                bc = rel.get("target_column") or rel.get("to_column") or ""
                rels.append(f"{a}.{ac}={b}.{bc}")
        if rels:
            parts.append("FK: " + "; ".join(rels))
        return "\n".join(parts)

    def _simple_schema_answer(self, question, knowledge):
        """Handle requests that require no SQL/LLM."""
        q = str(question).lower().strip()
        tables = list((knowledge.get("tables", {}) or {}).keys())
        patterns = (
            "show all the database", "show all database", "list all tables",
            "list the tables", "what tables are there", "show database tables",
            "show all tables", "list tables", "what are the tables",
        )
        if any(p in q for p in patterns):
            if not tables:
                return "The selected database has no readable tables.", None
            return "Tables in the selected database:\n\n" + "\n".join(
                f"{i}. {name}" for i, name in enumerate(tables, 1)
            ), {"type": "list_tables", "tables": tables}
        return None, None

    def generate_sql_with_ollama(self, question, schema_text):
        system_prompt = (
            "Convert the user's question into ONE safe PostgreSQL SELECT query. "
            "Use only the supplied schema. Never invent tables or columns. "
            "Use JOINs only when needed. Return JSON only: "
            '{"sql":"SELECT ..."}. Do not explain. Do not use INSERT, UPDATE, '
            "DELETE, DROP, ALTER, CREATE, TRUNCATE, GRANT, REVOKE or multiple statements."
        )
        user_prompt = f"SCHEMA:\n{schema_text}\n\nQUESTION:\n{question}"
        return ollama_client.generate_json(
            system_prompt,
            user_prompt,
            think=False,
            model=self.SQL_MODEL,
            num_ctx=self.SQL_CONTEXT,
            num_predict=96,
            timeout=self.SQL_TIMEOUT,
        )

    def execute_sql(self, engine, sql):
        sql = validate_sql(sql)
        with engine.connect() as connection:
            result = connection.execute(text(sql))
            columns = list(result.keys())
            rows = [
                {column: safe_value(value) for column, value in zip(columns, row)}
                for row in result.fetchmany(100)
            ]
        return {"success": True, "columns": columns, "rows": rows,
                "row_count": len(rows), "sql": sql}

    @staticmethod
    def local_answer(question, rows):
        if not rows:
            return "I couldn't find any matching records for your question."
        if len(rows) == 1:
            row = rows[0]
            if len(row) == 1:
                key, value = next(iter(row.items()))
                if value is None:
                    return "No value was found for that calculation."
                label = re.sub(r"_+", " ", str(key)).strip().capitalize()
                return f"{label}: {value}"
            parts = []
            for key, value in row.items():
                label = re.sub(r"_+", " ", str(key)).strip().capitalize()
                parts.append(f"{label}: {value}")
            return "\n".join(parts)
        return f"The database returned {len(rows)} records."

    def generate_answer(self, question, execution, sql, language="en-US"):
        # Never call Ollama for simple/single-row database results.
        return self.local_answer(question, execution.get("rows", []))

    def _result(self, started, **kwargs):
        kwargs["processing_time"] = round(time.perf_counter() - started, 3)
        return kwargs

    def process(self, question, engine, database_id=None, language="en-US"):
        started = time.perf_counter()
        question = str(question or "").strip()
        if not question:
            return self._result(started, success=False, answer="Please enter a database question.",
                                sql=None, execution={"success": False, "reason": "Empty question"})
        try:
            knowledge = self.get_schema(engine, database_id)
        except Exception as exc:
            print("Database schema error:", exc)
            return self._result(started, success=False,
                                answer="I could not read the database schema.", sql=None,
                                execution={"success": False, "reason": str(exc)})

        instant, instant_meta = self._simple_schema_answer(question, knowledge)
        if instant is not None:
            return self._result(started, success=True, question=question, sql=None,
                                answer=instant, execution={"success": True, "rows": [], "columns": []},
                                query_plan=instant_meta, database_knowledge_cached=True)

        relevant = self.select_relevant_tables(knowledge, question, max_tables=3)
        schema = self.schema_text(knowledge, relevant)
        print("\n========================================")
        print("FAST RELEVANT DATABASE SCHEMA")
        print("Question:", question)
        print("Tables:", relevant)
        print("Schema chars:", len(schema))
        print("========================================\n")
        try:
            plan = self.generate_sql_with_ollama(question, schema)
        except Exception as exc:
            print("Ollama SQL generation error:", exc)
            return self._result(started, success=False, question=question,
                                answer="The local SQL model could not generate the query quickly enough. Please try a more specific question.",
                                sql=None, execution={"success": False, "reason": str(exc)},
                                query_plan={"relevant_tables": relevant})
        sql = plan.get("sql") if isinstance(plan, dict) else None
        if not sql:
            return self._result(started, success=False, question=question,
                                answer="I could not generate a database query for that question.",
                                sql=None, execution={"success": False, "reason": "No SQL generated"},
                                query=plan, query_plan={"relevant_tables": relevant})
        try:
            sql = validate_sql(sql)
            execution = self.execute_sql(engine, sql)
        except Exception as exc:
            print("Database execution/validation error:", exc)
            return self._result(started, success=False, question=question,
                                answer="The generated database query could not be executed safely.",
                                sql=sql, execution={"success": False, "reason": str(exc)}, query=plan)
        rows = execution.get("rows", [])
        answer = self.generate_answer(question, execution, sql, language)
        print("Generated SQL:", sql)
        print("Rows returned:", len(rows))
        print("LOCAL DATABASE ANSWER - Ollama skipped")
        return self._result(started, success=True, question=question, sql=sql,
                            answer=answer, execution=execution, query=plan,
                            intent=plan.get("intent") if isinstance(plan, dict) else None,
                            entities=plan.get("entities") if isinstance(plan, dict) else [],
                            metric=plan.get("metric") if isinstance(plan, dict) else None,
                            query_plan={"relevant_tables": relevant},
                            database_knowledge_cached=True)


custom_ai_engine = CustomAIEngine()
