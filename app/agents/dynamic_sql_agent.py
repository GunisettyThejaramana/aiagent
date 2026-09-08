import re

from sqlalchemy import inspect

from app.llm.client import llm_client


FORBIDDEN_SQL_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "GRANT",
    "REVOKE",
    "MERGE",
    "EXEC",
    "EXECUTE",
    "CALL",
]


def get_database_schema(engine):

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    schema = []

    for table_name in tables:

        columns = inspector.get_columns(
            table_name
        )

        column_names = [
            str(column["name"])
            for column in columns
        ]

        schema.append(
            {
                "table": table_name,
                "columns": column_names
            }
        )

    return schema


def format_schema(schema):

    if not schema:
        return "No tables were found."

    lines = []

    for table in schema:

        table_name = table["table"]

        columns = ", ".join(
            table["columns"]
        )

        lines.append(
            f"TABLE {table_name}: {columns}"
        )

    return "\n".join(lines)


def clean_sql(sql: str) -> str:

    sql = sql.strip()

    sql = sql.replace(
        "```sql",
        ""
    )

    sql = sql.replace(
        "```SQL",
        ""
    )

    sql = sql.replace(
        "```",
        ""
    )

    sql = sql.strip()

    match = re.search(
        r"\b(SELECT|WITH)\b",
        sql,
        re.IGNORECASE
    )

    if match:
        sql = sql[match.start():]

    return sql.strip()


def validate_sql(sql: str):

    sql = clean_sql(sql)

    if not sql:
        raise ValueError(
            "AI did not generate SQL."
        )

    upper_sql = sql.upper()

    if not (
        upper_sql.startswith("SELECT")
        or upper_sql.startswith("WITH")
    ):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    for keyword in FORBIDDEN_SQL_KEYWORDS:

        pattern = rf"\b{keyword}\b"

        if re.search(
            pattern,
            upper_sql
        ):
            raise ValueError(
                f"Unsafe SQL keyword detected: {keyword}"
            )

    statements = [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]

    if len(statements) > 1:
        raise ValueError(
            "Multiple SQL statements are not allowed."
        )

    sql = sql.rstrip(";").strip()

    return sql


def generate_dynamic_sql(
    question: str,
    engine
):

    schema = get_database_schema(
        engine
    )

    schema_text = format_schema(
        schema
    )

    dialect = engine.dialect.name

    system_prompt = f"""
You are an enterprise database SQL assistant.

Generate ONE read-only SQL query for the user's question.

Database dialect:

{dialect}

Available database schema:

{schema_text}

Rules:

1. Generate only SELECT or WITH queries.
2. Never generate INSERT, UPDATE, DELETE, DROP,
   ALTER, CREATE, TRUNCATE, GRANT, REVOKE,
   EXEC, EXECUTE, CALL, or MERGE.
3. Use only tables and columns present in the schema.
4. Never invent table names.
5. Never invent column names.
6. Do not modify database data.
7. Return ONLY SQL.
8. Do not use markdown code fences.
9. Keep the query reasonably efficient.
10. For ordinary list queries, return at most 50 rows.
"""

    user_prompt = f"""
User question:

{question}
"""

    sql = llm_client.generate(
        system_prompt,
        user_prompt
    )

    return validate_sql(
        sql
    )