from __future__ import annotations


class QueryBuilder:
    """
    Converts the reasoning/query plan into safe read-only SQL.

    This component does not use an LLM.
    It relies on:
        - Intent Engine
        - Entity Engine
        - Metric Engine
        - Reasoning Engine
        - Query Planner
        - Database schema
    """

    def build(
        self,
        question: str,
        intent_result: dict,
        entity_result: dict,
        reasoning_result: dict,
        schema: dict,
        metric_result: dict | None = None,
        query_plan: dict | None = None,
    ) -> dict:

        intent = intent_result.get(
            "intent",
            "UNKNOWN",
        )

        limit = entity_result.get(
            "limit"
        )

        selected_table = reasoning_result.get(
            "selected_table"
        )

        if not selected_table:
            return self._failure(
                "No suitable table was found."
            )

        table_name = selected_table.get(
            "table_name"
        )

        columns = selected_table.get(
            "columns",
            [],
        )

        if not table_name:
            return self._failure(
                "Selected table has no name."
            )

        if not self._safe_identifier(
            table_name
        ):
            return self._failure(
                "Unsafe table name."
            )

        metric = None

        if metric_result:
            metric = metric_result.get(
                "metric"
            )

        # =========================================================
        # 1. Relationship query
        # =========================================================

        if query_plan:

            plan_type = query_plan.get(
                "plan_type"
            )

            if plan_type == "RELATIONSHIP":

                return self._build_relationship_query(
                    question=question,
                    intent=intent,
                    entity_result=entity_result,
                    query_plan=query_plan,
                    schema=schema,
                )

            if plan_type == "DERIVED_METRIC":

                return self._build_derived_metric_query(
                    intent=intent,
                    entity_result=entity_result,
                    query_plan=query_plan,
                    schema=schema,
                )

                # =========================================================
        # 2. COUNT / QUANTITY
        # =========================================================

        if intent == "COUNT":

            # The Query Planner may change COUNT into SUM when
            # the question asks for a business quantity.
            #
            # Example:
            #   "How many sarees were produced?"
            #
            # means:
            #   SUM(num_sarees)
            #
            # while:
            #   "How many production orders are there?"
            #
            # means:
            #   COUNT(*)

            aggregation = None

            if query_plan:
                aggregation = query_plan.get(
                    "aggregation"
                )

            if (
                aggregation == "SUM"
                and metric
            ):

                numeric_column = (
                    self._resolve_metric_column(
                        metric=metric,
                        columns=columns,
                        question=question,
                    )
                )

                if not numeric_column:

                    return self._failure(
                        "I could not determine which numeric "
                        "column should be totaled."
                    )

                sql = (
                    f"SELECT SUM({numeric_column}) "
                    f"AS total_{numeric_column} "
                    f"FROM {table_name}"
                )

                return self._success(
                    sql
                )

            sql = (
                f"SELECT COUNT(*) AS record_count "
                f"FROM {table_name}"
            )

            return self._success(
                sql
            )

        # =========================================================
        # 3. TOTAL
        # =========================================================

        if intent == "TOTAL":

            numeric_column = (
                self._resolve_metric_column(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not numeric_column:

                return self._failure(
                    "I could not determine which numeric "
                    "column should be totaled."
                )

            sql = (
                f"SELECT SUM({numeric_column}) "
                f"AS total_{numeric_column} "
                f"FROM {table_name}"
            )

            return self._success(
                sql
            )

        # =========================================================
        # 4. AVERAGE
        # =========================================================

        if intent == "AVERAGE":

            numeric_column = (
                self._resolve_metric_column(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not numeric_column:

                return self._failure(
                    "I could not determine which numeric "
                    "column should be averaged."
                )

            sql = (
                f"SELECT AVG({numeric_column}) "
                f"AS average_{numeric_column} "
                f"FROM {table_name}"
            )

            return self._success(
                sql
            )

                # =========================================================
        # 5. MAXIMUM
        # =========================================================

        if intent == "MAXIMUM":

            numeric_column = (
                self._resolve_metric_column(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not numeric_column:

                return self._failure(
                    "I could not determine which numeric "
                    "column should be maximized."
                )

            # Questions such as:
            #   "Who has the highest balance?"
            #   "Which employee has the highest salary?"
            #
            # need the identity together with the value.
            if self._asks_for_identity(question):

                display_columns = (
                    self._select_identity_columns(
                        columns
                    )
                )

                if not display_columns:
                    display_columns = ["id"]

                if numeric_column not in display_columns:
                    display_columns.append(
                        numeric_column
                    )

                sql = (
                    f"SELECT "
                    f"{', '.join(display_columns)} "
                    f"FROM {table_name} "
                    f"ORDER BY {numeric_column} DESC "
                    f"LIMIT 1"
                )

                return self._success(
                    sql
                )

            sql = (
                f"SELECT MAX({numeric_column}) "
                f"AS maximum_{numeric_column} "
                f"FROM {table_name}"
            )

            return self._success(
                sql
            )

                # =========================================================
        # 6. MINIMUM
        # =========================================================

        if intent == "MINIMUM":

            numeric_column = (
                self._resolve_metric_column(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not numeric_column:

                return self._failure(
                    "I could not determine which numeric "
                    "column should be minimized."
                )

            # Questions such as:
            #   "Who has the lowest balance?"
            #   "Which employee has the lowest salary?"
            #
            # need the identity together with the value.
            if self._asks_for_identity(question):

                display_columns = (
                    self._select_identity_columns(
                        columns
                    )
                )

                if not display_columns:
                    display_columns = ["id"]

                if numeric_column not in display_columns:
                    display_columns.append(
                        numeric_column
                    )

                sql = (
                    f"SELECT "
                    f"{', '.join(display_columns)} "
                    f"FROM {table_name} "
                    f"ORDER BY {numeric_column} ASC "
                    f"LIMIT 1"
                )

                return self._success(
                    sql
                )

            sql = (
                f"SELECT MIN({numeric_column}) "
                f"AS minimum_{numeric_column} "
                f"FROM {table_name}"
            )

            return self._success(
                sql
            )

        # =========================================================
        # 7. TOP
        # =========================================================

        if intent == "TOP":

            return self._build_rank_query(
                table_name=table_name,
                columns=columns,
                limit=limit or 5,
                descending=True,
                metric=metric,
                question=question,
            )

        # =========================================================
        # 8. BOTTOM
        # =========================================================

        if intent == "BOTTOM":

            return self._build_rank_query(
                table_name=table_name,
                columns=columns,
                limit=limit or 5,
                descending=False,
                metric=metric,
                question=question,
            )

        # =========================================================
        # 9. LIST
        # =========================================================

        if intent == "LIST":

            selected_columns = (
                self._select_display_columns(
                    columns
                )
            )

            if not selected_columns:

                return self._failure(
                    "No usable columns were found."
                )

            sql = (
                f"SELECT "
                f"{', '.join(selected_columns)} "
                f"FROM {table_name}"
            )

            if limit:

                sql += (
                    f" LIMIT {int(limit)}"
                )

            else:

                sql += " LIMIT 50"

            return self._success(
                sql
            )

        return self._failure(
            "I understand the database structure, "
            f"but I do not yet know how to answer "
            f"the intent '{intent}'."
        )

    # =============================================================
    # RELATIONSHIP QUERY
    # =============================================================

    def _build_relationship_query(
        self,
        question: str,
        intent: str,
        entity_result: dict,
        query_plan: dict,
        schema: dict,
    ) -> dict:

        tables = query_plan.get(
            "tables",
            [],
        )

        joins = query_plan.get(
            "joins",
            [],
        )

        if not tables:

            return self._failure(
                "No tables were provided by the query planner."
            )

        if not joins:

            return self._failure(
                "No relationships were provided by the query planner."
            )

        primary_table = query_plan.get(
            "primary_table"
        )

        if not primary_table:

            primary_table = tables[0]

        if not self._safe_identifier(
            primary_table
        ):

            return self._failure(
                "Unsafe primary table name."
            )

        # ---------------------------------------------------------
        # Determine useful columns
        # ---------------------------------------------------------

        select_columns = []

        for table_name in tables:

            if not self._safe_identifier(
                table_name
            ):
                return self._failure(
                    "Unsafe relationship table name."
                )

            table = self._find_table(
                schema,
                table_name,
            )

            if not table:
                continue

            columns = table.get(
                "columns",
                [],
            )

            identity_columns = (
                self._select_identity_columns(
                    columns
                )
            )

            for column in identity_columns:

                if not self._safe_identifier(
                    column
                ):
                    continue

                select_columns.append(
                    f"{table_name}.{column}"
                )

        # ---------------------------------------------------------
        # Fallback to IDs
        # ---------------------------------------------------------

        if not select_columns:

            for table_name in tables:

                table = self._find_table(
                    schema,
                    table_name,
                )

                if not table:
                    continue

                column_names = [
                    column["name"]
                    for column in table.get(
                        "columns",
                        [],
                    )
                ]

                if "id" in column_names:

                    select_columns.append(
                        f"{table_name}.id"
                    )

        if not select_columns:

            return self._failure(
                "No usable columns were found "
                "for the relationship query."
            )

        # ---------------------------------------------------------
        # FROM
        # ---------------------------------------------------------

        sql = (
            "SELECT "
            + ", ".join(select_columns)
            + f" FROM {primary_table}"
        )

        # ---------------------------------------------------------
        # JOINs
        # ---------------------------------------------------------

        joined_tables = {
            primary_table
        }

        for join in joins:

            left_table = join.get(
                "left_table"
            )

            right_table = join.get(
                "right_table"
            )

            left_columns = join.get(
                "left_columns",
                [],
            )

            right_columns = join.get(
                "right_columns",
                [],
            )

            if not left_table or not right_table:

                return self._failure(
                    "Invalid relationship definition."
                )

            if not left_columns or not right_columns:

                return self._failure(
                    "Relationship columns are missing."
                )

            if len(left_columns) != len(
                right_columns
            ):

                return self._failure(
                    "Relationship column counts do not match."
                )

            if not self._safe_identifier(
                left_table
            ):

                return self._failure(
                    "Unsafe left table name."
                )

            if not self._safe_identifier(
                right_table
            ):

                return self._failure(
                    "Unsafe right table name."
                )

            conditions = []

            for index in range(
                len(left_columns)
            ):

                left_column = left_columns[
                    index
                ]

                right_column = right_columns[
                    index
                ]

                if not self._safe_identifier(
                    left_column
                ):

                    return self._failure(
                        "Unsafe relationship column."
                    )

                if not self._safe_identifier(
                    right_column
                ):

                    return self._failure(
                        "Unsafe relationship column."
                    )

                conditions.append(
                    f"{left_table}.{left_column} = "
                    f"{right_table}.{right_column}"
                )

            if right_table not in joined_tables:

                sql += (
                    f" JOIN {right_table}"
                    f" ON {' AND '.join(conditions)}"
                )

                joined_tables.add(
                    right_table
                )

        # ---------------------------------------------------------
        # Limit
        # ---------------------------------------------------------

        limit = entity_result.get(
            "limit"
        )

        if limit:

            sql += (
                f" LIMIT {int(limit)}"
            )

        else:

            sql += " LIMIT 50"

        return self._success(
            sql
        )

    # =============================================================
    # DERIVED METRIC QUERY
    # =============================================================

    def _build_derived_metric_query(
        self,
        intent: str,
        entity_result: dict,
        query_plan: dict,
        schema: dict,
    ) -> dict:

        table_name = query_plan.get(
            "primary_table"
        )

        expression = query_plan.get(
            "metric_expression"
        )

        metric = query_plan.get(
            "metric"
        )

        if not table_name:

            return self._failure(
                "Derived metric table is missing."
            )

        if not expression:

            return self._failure(
                "Derived metric expression is missing."
            )

        if not self._safe_identifier(
            table_name
        ):

            return self._failure(
                "Unsafe derived metric table."
            )

        # ---------------------------------------------------------
        # Revenue
        # ---------------------------------------------------------

        if metric == "revenue":

            if intent == "TOTAL":

                sql = (
                    "SELECT "
                    "SUM(quantity * price) "
                    "AS total_revenue "
                    "FROM sales"
                )

                return self._success(
                    sql
                )

            if intent == "AVERAGE":

                sql = (
                    "SELECT "
                    "AVG(quantity * price) "
                    "AS average_revenue "
                    "FROM sales"
                )

                return self._success(
                    sql
                )

            if intent == "MAXIMUM":

                sql = (
                    "SELECT "
                    "MAX(quantity * price) "
                    "AS maximum_revenue "
                    "FROM sales"
                )

                return self._success(
                    sql
                )

            if intent == "MINIMUM":

                sql = (
                    "SELECT "
                    "MIN(quantity * price) "
                    "AS minimum_revenue "
                    "FROM sales"
                )

                return self._success(
                    sql
                )

        return self._failure(
            "The derived metric is not yet supported "
            f"for intent '{intent}'."
        )


        # =============================================================
    # IDENTITY QUESTION DETECTION
    # =============================================================

    @staticmethod
    def _asks_for_identity(
        question: str,
    ) -> bool:

        normalized = (
            str(question)
            .lower()
            .strip()
        )

        identity_phrases = [
            "who ",
            "who has",
            "who had",
            "who is",
            "who was",
            "which employee",
            "which employees",
            "which weaver",
            "which weavers",
            "which customer",
            "which customers",
            "which product",
            "which products",
            "which loom",
            "which looms",
            "which person",
            "which people",
        ]

        return any(
            phrase in normalized
            for phrase in identity_phrases
        )

    # =============================================================
    # RANK QUERY
    # =============================================================

    def _build_rank_query(
        self,
        table_name: str,
        columns: list,
        limit: int,
        descending: bool,
        metric: str | None,
        question: str = "",
    ) -> dict:

        numeric_column = (
            self._resolve_metric_column(
                metric=metric,
                columns=columns,
                question=question,
            )
        )

        if not numeric_column:

            return self._failure(
                "I could not determine which numeric "
                "metric should be used for ranking."
            )

        display_columns = (
            self._select_identity_columns(
                columns
            )
        )

        if not display_columns:

            display_columns = [
                "id"
            ]

        if numeric_column not in display_columns:

            display_columns.append(
                numeric_column
            )

        direction = (
            "DESC"
            if descending
            else "ASC"
        )

        sql = (
            f"SELECT "
            f"{', '.join(display_columns)} "
            f"FROM {table_name} "
            f"ORDER BY "
            f"{numeric_column} "
            f"{direction} "
            f"LIMIT {int(limit)}"
        )

        return self._success(
            sql
        )

    # =============================================================
    # METRIC COLUMN RESOLUTION
    # =============================================================

    def _resolve_metric_column(
        self,
        metric: str | None,
        columns: list,
        question: str = "",
    ) -> str | None:

        if not metric:
            return None

        column_names = [
            column["name"]
            for column in columns
        ]

        # ---------------------------------------------------------
        # 1. Exact metric-column match
        # ---------------------------------------------------------

        for column_name in column_names:

            if (
                column_name.lower()
                == metric.lower()
            ):

                if self._is_numeric_type(
                    self._get_column_type(
                        columns,
                        column_name,
                    )
                ):

                    return column_name

        # ---------------------------------------------------------
        # 2. Business metric aliases
        # ---------------------------------------------------------

        aliases = {

            "total_balance": [
                "total_balance",
                "balance",
                "outstanding_balance",
                "remaining_balance",
                "amount_due",
                "due_amount",
            ],

            "total_credit": [
                "total_credit",
                "amount_credit",
                "credit",
                "credited_amount",
                "credit_amount",
            ],

            "total_debit": [
                "total_debit",
                "amount_debit",
                "debit",
                "debited_amount",
                "debit_amount",
            ],

            "advance_amount": [
                "advance_amount",
                "advance",
                "advance_money",
            ],

            "quantity": [
                "quantity",
                "qty",
            ],

            "price": [
                "price",
                "unit_price",
                "cost",
            ],

            "salary": [
                "salary",
                "wage",
                "wages",
                "pay",
                "compensation",
            ],

            "revenue": [
                "revenue",
                "amount",
                "total_sales",
            ],

            "amount": [
                "amount",
                "price",
                "total_amount",
            ],

            "num_sarees": [
                "num_sarees",
                "no_of_sarees",
                "saree_count",
                "sarees_count",
                "production_quantity",
            ],
        }

        possible_names = aliases.get(
            metric,
            [],
        )

        # ---------------------------------------------------------
        # 3. Find exact alias in schema
        # ---------------------------------------------------------

        for possible_name in possible_names:

            for column_name in column_names:

                if (
                    column_name.lower()
                    == possible_name.lower()
                ):

                    if self._is_numeric_type(
                        self._get_column_type(
                            columns,
                            column_name,
                        )
                    ):

                        return column_name

        # ---------------------------------------------------------
        # 4. Business-language fallback
        # ---------------------------------------------------------

        normalized_question = (
            str(question)
            .lower()
            .strip()
        )

        # Debit
        if metric == "total_debit":

            debit_candidates = [
                "amount_debit",
                "debit",
                "debit_amount",
                "debited_amount",
            ]

            result = self._find_numeric_candidate(
                debit_candidates,
                columns,
            )

            if result:
                return result

        # Credit
        if metric == "total_credit":

            credit_candidates = [
                "amount_credit",
                "credit",
                "credit_amount",
                "credited_amount",
            ]

            result = self._find_numeric_candidate(
                credit_candidates,
                columns,
            )

            if result:
                return result

        # Balance
        if metric == "total_balance":

            balance_candidates = [
                "total_balance",
                "balance",
                "outstanding_balance",
                "remaining_balance",
                "amount_due",
                "due_amount",
            ]

            result = self._find_numeric_candidate(
                balance_candidates,
                columns,
            )

            if result:
                return result

        # Advance
        if metric == "advance_amount":

            advance_candidates = [
                "advance_amount",
                "advance",
                "advance_money",
            ]

            result = self._find_numeric_candidate(
                advance_candidates,
                columns,
            )

            if result:
                return result

        # Salary
        if metric == "salary":

            salary_candidates = [
                "salary",
                "wage",
                "wages",
                "pay",
                "compensation",
            ]

            result = self._find_numeric_candidate(
                salary_candidates,
                columns,
            )

            if result:
                return result

        # Saree production
        if metric == "num_sarees":

            saree_candidates = [
                "num_sarees",
                "no_of_sarees",
                "saree_count",
                "sarees_count",
                "production_quantity",
            ]

            result = self._find_numeric_candidate(
                saree_candidates,
                columns,
            )

            if result:
                return result

        # Quantity
        if metric == "quantity":

            quantity_candidates = [
                "quantity",
                "qty",
            ]

            result = self._find_numeric_candidate(
                quantity_candidates,
                columns,
            )

            if result:
                return result

        # Price
        if metric == "price":

            price_candidates = [
                "price",
                "unit_price",
                "cost",
            ]

            result = self._find_numeric_candidate(
                price_candidates,
                columns,
            )

            if result:
                return result

        # Generic amount only as a final fallback.
        if metric == "amount":

            amount_candidates = [
                "amount",
                "total_amount",
                "value",
            ]

            result = self._find_numeric_candidate(
                amount_candidates,
                columns,
            )

            if result:
                return result

        # Keep variable intentionally available for
        # future business-language expansion.
        _ = normalized_question

        return None

    # =============================================================
    # FIND NUMERIC CANDIDATE
    # =============================================================

    def _find_numeric_candidate(
        self,
        candidates: list[str],
        columns: list,
    ) -> str | None:

        for candidate in candidates:

            for column in columns:

                column_name = column.get(
                    "name"
                )

                if not column_name:
                    continue

                if (
                    column_name.lower()
                    != candidate.lower()
                ):
                    continue

                if self._is_numeric_type(
                    self._get_column_type(
                        columns,
                        column_name,
                    )
                ):

                    return column_name

        return None

    # =============================================================
    # IDENTITY COLUMNS
    # =============================================================

    @staticmethod
    def _select_identity_columns(
        columns: list,
    ) -> list[str]:

        preferred = [

            "id",

            "weavername",
            "weaver_name",

            "loom_no",
            "loom_number",

            "saree_number",
            "saree_name",

            "customer_name",

            "product_name",

            "employee_name",

            "department",

            "name",
        ]

        available = [
            column["name"]
            for column in columns
        ]

        selected = []

        for preferred_name in preferred:

            for actual_name in available:

                if (
                    actual_name.lower()
                    == preferred_name.lower()
                ):

                    if actual_name not in selected:

                        selected.append(
                            actual_name
                        )

        return selected[:5]

    # =============================================================
    # DISPLAY COLUMNS
    # =============================================================

    @staticmethod
    def _select_display_columns(
        columns: list,
    ) -> list[str]:

        selected = []

        sensitive_words = [

            "password",
            "password_hash",

            "aadhar",

            "account_number",

            "ifsc",
        ]

        for column in columns:

            name = column["name"]

            if any(
                word in name.lower()
                for word in sensitive_words
            ):
                continue

            if not QueryBuilder._safe_identifier(
                name
            ):
                continue

            selected.append(
                name
            )

        return selected[:10]

    # =============================================================
    # FIND TABLE
    # =============================================================

    @staticmethod
    def _find_table(
        schema: dict,
        table_name: str,
    ) -> dict | None:

        for table in schema.get(
            "tables",
            [],
        ):

            if (
                table["table_name"]
                == table_name
            ):

                return table

        return None

    # =============================================================
    # COLUMN TYPE
    # =============================================================

    @staticmethod
    def _get_column_type(
        columns: list,
        column_name: str,
    ) -> str:

        for column in columns:

            if (
                column["name"].lower()
                == column_name.lower()
            ):

                return str(
                    column["type"]
                )

        return ""

    # =============================================================
    # NUMERIC TYPE
    # =============================================================

    @staticmethod
    def _is_numeric_type(
        column_type: str,
    ) -> bool:

        numeric_types = [

            "INTEGER",
            "BIGINT",
            "SMALLINT",

            "DECIMAL",
            "NUMERIC",

            "REAL",
            "DOUBLE",
            "FLOAT",
        ]

        value = str(
            column_type
        ).upper()

        return any(
            numeric_type in value
            for numeric_type
            in numeric_types
        )

    # =============================================================
    # SAFE IDENTIFIER
    # =============================================================

    @staticmethod
    def _safe_identifier(
        identifier: str,
    ) -> bool:

        if not identifier:
            return False

        return all(
            character.isalnum()
            or character == "_"
            for character in identifier
        )

    # =============================================================
    # SUCCESS
    # =============================================================

    @staticmethod
    def _success(
        sql: str,
    ) -> dict:

        return {
            "success": True,
            "sql": sql,
            "params": {},
            "reason": None,
        }

    # =============================================================
    # FAILURE
    # =============================================================

    @staticmethod
    def _failure(
        reason: str,
    ) -> dict:

        return {
            "success": False,
            "sql": None,
            "params": {},
            "reason": reason,
        }


query_builder = QueryBuilder()