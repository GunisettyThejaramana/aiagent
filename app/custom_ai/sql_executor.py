from sqlalchemy import text


class SQLExecutor:

    MAX_ROWS = 100

    ALLOWED_START = (
        "SELECT",
        "WITH",
    )

    BLOCKED_KEYWORDS = [
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
        "REPLACE",
    ]

    def execute(
        self,
        engine,
        query_result: dict,
    ) -> dict:

        if not query_result:
            return self._failure(
                "No query was provided."
            )

        if not query_result.get("success"):
            return self._failure(
                query_result.get(
                    "reason",
                    "Query generation failed.",
                )
            )

        sql = query_result.get("sql")

        if not sql:
            return self._failure(
                "Generated SQL is empty."
            )

        validation = self.validate_sql(sql)

        if not validation["safe"]:
            return self._failure(
                validation["reason"]
            )

        try:

            return self._execute_query(
                engine=engine,
                sql=sql,
                params=query_result.get(
                    "params",
                    {},
                ),
            )

        except Exception as exc:

            return self._failure(
                f"Database query failed: {exc}"
            )

    # =============================================================
    # SQL VALIDATION
    # =============================================================

    def validate_sql(
        self,
        sql: str,
    ) -> dict:

        if not sql or not sql.strip():

            return {
                "safe": False,
                "reason": "SQL query is empty.",
            }

        normalized = (
            sql.strip()
            .upper()
        )

        # ---------------------------------------------------------
        # Only SELECT / WITH queries are allowed
        # ---------------------------------------------------------

        if not normalized.startswith(
            self.ALLOWED_START
        ):

            return {
                "safe": False,
                "reason": (
                    "Only read-only SELECT queries "
                    "are allowed."
                ),
            }

        # ---------------------------------------------------------
        # Block multiple statements
        # ---------------------------------------------------------

        cleaned_sql = normalized.rstrip()

        if ";" in cleaned_sql[:-1]:

            return {
                "safe": False,
                "reason": (
                    "Multiple SQL statements are "
                    "not allowed."
                ),
            }

        # ---------------------------------------------------------
        # Block dangerous operations
        # ---------------------------------------------------------

        for keyword in self.BLOCKED_KEYWORDS:

            if self._contains_keyword(
                normalized,
                keyword,
            ):

                return {
                    "safe": False,
                    "reason": (
                        f"SQL operation '{keyword}' "
                        "is not allowed."
                    ),
                }

        return {
            "safe": True,
            "reason": None,
        }

    # =============================================================
    # EXECUTE QUERY
    # =============================================================

    def _execute_query(
        self,
        engine,
        sql: str,
        params: dict,
    ) -> dict:

        statement = text(
            sql
        )

        with engine.connect() as connection:

            result = connection.execute(
                statement,
                params,
            )

            columns = list(
                result.keys()
            )

            rows = []

            for row in result:

                rows.append(
                    dict(
                        row._mapping
                    )
                )

                if len(rows) >= self.MAX_ROWS:
                    break

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(rows)
            >= self.MAX_ROWS,
            "sql": sql,
            "reason": None,
        }

    # =============================================================
    # KEYWORD DETECTION
    # =============================================================

    @staticmethod
    def _contains_keyword(
        sql: str,
        keyword: str,
    ) -> bool:

        words = sql.replace(
            "(",
            " ",
        ).replace(
            ")",
            " ",
        ).replace(
            ",",
            " ",
        ).replace(
            ".",
            " ",
        ).split()

        return keyword in words

    # =============================================================
    # FAILURE
    # =============================================================

    @staticmethod
    def _failure(
        reason: str,
    ) -> dict:

        return {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "truncated": False,
            "sql": None,
            "reason": reason,
        }


sql_executor = SQLExecutor()