
from __future__ import annotations

import re
from datetime import date


class QueryBuilder:
    """
    Build safe read-only SQL from the actual database schema.

    IMPORTANT:

    This builder does NOT require:

        sales -> sales table
        revenue -> revenue column
        balance -> balance column

    Instead it searches the actual selected table's columns.

    Example:

        revenue

        can resolve to:

            revenue
            sales_amount
            grand_total
            net_amount
            invoice_total
            total_value
            amount

        or:

            quantity * price
    """

    METRIC_ALIASES = {

        "revenue": [
            "revenue",
            "sales",
            "sale",
            "turnover",
            "income",
            "amount",
            "total",
            "value",
            "money",
            "receipt",
            "receipts",
            "collection",
            "collections",
            "net_sales",
            "gross_sales",
            "sales_amount",
            "sales_value",
            "invoice_amount",
            "invoice_total",
            "bill_amount",
            "grand_total",
            "net_amount",
            "gross_amount",
        ],

        "total_balance": [
            "balance",
            "total_balance",
            "outstanding",
            "remaining",
            "due",
            "receivable",
            "payable",
            "pending",
        ],

        "total_credit": [
            "credit",
            "credited",
            "credit_amount",
            "amount_credit",
        ],

        "total_debit": [
            "debit",
            "debited",
            "debit_amount",
            "amount_debit",
        ],

        "advance_amount": [
            "advance",
            "advanced",
            "prepayment",
        ],

        "salary": [
            "salary",
            "wage",
            "wages",
            "pay",
            "compensation",
            "payroll",
        ],

        "quantity": [
            "quantity",
            "qty",
            "units",
            "unit_count",
            "volume",
            "count",
        ],

        "num_sarees": [
            "num_sarees",
            "saree_count",
            "sarees_count",
            "no_of_sarees",
            "production_quantity",
        ],

        "price": [
            "price",
            "unit_price",
            "selling_price",
            "rate",
            "cost",
        ],

        "amount": [
            "amount",
            "total_amount",
            "net_amount",
            "gross_amount",
            "value",
            "money",
        ],

        "profit": [
            "profit",
            "profit_amount",
            "net_profit",
            "gross_profit",
            "margin",
        ],

        "loss": [
            "loss",
            "loss_amount",
            "net_loss",
            "gross_loss",
        ],
    }

    SENSITIVE_WORDS = {
        "password",
        "password_hash",
        "token",
        "secret",
        "api_key",
        "aadhar",
        "aadhaar",
        "ifsc",
        "account_number",
    }

    # =============================================================
    # MAIN
    # =============================================================

    def build(
        self,
        question,
        intent_result,
        entity_result,
        reasoning_result,
        schema,
        metric_result=None,
        query_plan=None,
    ):

        intent = intent_result.get(
            "intent",
            "UNKNOWN",
        )

        metric = (
            metric_result.get("metric")
            if metric_result
            else None
        )

        selected_table = (
            reasoning_result.get(
                "selected_table"
            )
        )

        if not selected_table:

            return self._failure(
                "No suitable table was found for this question."
            )

        table_name = selected_table.get(
            "table_name"
        )

        columns = selected_table.get(
            "columns",
            [],
        )

        if (
            not table_name
            or not self._safe_identifier(
                table_name
            )
        ):

            return self._failure(
                "Selected table has an invalid name."
            )

        # ---------------------------------------------------------
        # Existing relationship support
        # ---------------------------------------------------------

        if (
            query_plan
            and query_plan.get(
                "plan_type"
            ) == "RELATIONSHIP"
        ):

            return self._build_relationship_query(
                question=question,
                intent=intent,
                entity_result=entity_result,
                metric=metric,
                query_plan=query_plan,
                schema=schema,
            )

        # ---------------------------------------------------------
        # Normal single-table query
        # ---------------------------------------------------------

        return self._build_single_table(
            question=question,
            intent=intent,
            metric=metric,
            table_name=table_name,
            columns=columns,
            entity_result=entity_result,
        )

    # =============================================================
    # SINGLE TABLE
    # =============================================================

    def _build_single_table(
        self,
        question,
        intent,
        metric,
        table_name,
        columns,
        entity_result,
    ):

        date_range = entity_result.get(
            "date_range"
        )

        date_column = None

        if date_range:

            date_column = (
                self._resolve_date_column(
                    columns,
                    question,
                )
            )

            if not date_column:

                return self._failure(
                    "I found the requested time period, "
                    "but the selected table has no usable date column."
                )

        where_sql, params = (
            self._date_filter(
                date_column,
                date_range,
            )
        )

        # =========================================================
        # TOTAL
        # =========================================================

        if intent == "TOTAL":

            expression, label = (
                self._resolve_aggregate_expression(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not expression:

                return self._failure(
                    "I could not determine which database "
                    "column represents the requested value."
                )

            sql = (
                f"SELECT SUM({expression}) "
                f"AS {label} "
                f"FROM {table_name}"
                f"{where_sql}"
            )

            return self._success(
                sql,
                params,
            )

        # =========================================================
        # AVERAGE
        # =========================================================

        if intent == "AVERAGE":

            expression, label = (
                self._resolve_aggregate_expression(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not expression:

                return self._failure(
                    "I could not determine which numeric "
                    "column should be averaged."
                )

            clean_label = (
                label.replace(
                    "total_",
                    "",
                    1,
                )
            )

            sql = (
                f"SELECT AVG({expression}) "
                f"AS average_{clean_label} "
                f"FROM {table_name}"
                f"{where_sql}"
            )

            return self._success(
                sql,
                params,
            )

        # =========================================================
        # COUNT
        # =========================================================

        if intent == "COUNT":

            if metric in {
                "quantity",
                "num_sarees",
            }:

                expression, _ = (
                    self._resolve_aggregate_expression(
                        metric=metric,
                        columns=columns,
                        question=question,
                    )
                )

                if expression:

                    alias = (
                        "total_"
                        + self._safe_alias(
                            metric
                        )
                    )

                    sql = (
                        f"SELECT SUM({expression}) "
                        f"AS {alias} "
                        f"FROM {table_name}"
                        f"{where_sql}"
                    )

                    return self._success(
                        sql,
                        params,
                    )

            sql = (
                f"SELECT COUNT(*) "
                f"AS record_count "
                f"FROM {table_name}"
                f"{where_sql}"
            )

            return self._success(
                sql,
                params,
            )

        # =========================================================
        # MAXIMUM / MINIMUM
        # =========================================================

        if intent in {
            "MAXIMUM",
            "MINIMUM",
        }:

            expression, label = (
                self._resolve_aggregate_expression(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not expression:

                return self._failure(
                    "I could not determine which numeric "
                    "column should be compared."
                )

            direction = (
                "DESC"
                if intent == "MAXIMUM"
                else "ASC"
            )

            if self._asks_for_identity(
                question
            ):

                display = (
                    self._select_identity_columns(
                        columns
                    )
                )

                if (
                    expression
                    and self._safe_identifier(
                        expression
                    )
                    and expression not in display
                ):

                    display.append(
                        expression
                    )

                if not display:

                    display = [
                        expression
                    ]

                sql = (
                    f"SELECT "
                    f"{', '.join(display)} "
                    f"FROM {table_name}"
                    f"{where_sql} "
                    f"ORDER BY {expression} "
                    f"{direction} "
                    f"LIMIT 1"
                )

                return self._success(
                    sql,
                    params,
                )

            aggregate = (
                "MAX"
                if intent == "MAXIMUM"
                else "MIN"
            )

            prefix = (
                "maximum_"
                if intent == "MAXIMUM"
                else "minimum_"
            )

            alias = (
                prefix
                + self._safe_alias(
                    metric
                    or expression
                )
            )

            sql = (
                f"SELECT {aggregate}({expression}) "
                f"AS {alias} "
                f"FROM {table_name}"
                f"{where_sql}"
            )

            return self._success(
                sql,
                params,
            )

        # =========================================================
        # TOP / BOTTOM
        # =========================================================

        if intent in {
            "TOP",
            "BOTTOM",
        }:

            expression, _ = (
                self._resolve_aggregate_expression(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if not expression:

                return self._failure(
                    "I could not determine which numeric "
                    "value should be used for ranking."
                )

            identity = (
                self._select_identity_columns(
                    columns
                )
            )

            if not identity:

                identity = (
                    self._select_display_columns(
                        columns
                    )[:2]
                )

            if (
                self._safe_identifier(
                    expression
                )
                and expression not in identity
            ):

                identity.append(
                    expression
                )

            limit = max(
                1,
                min(
                    int(
                        entity_result.get(
                            "limit"
                        )
                        or 5
                    ),
                    100,
                ),
            )

            direction = (
                "DESC"
                if intent == "TOP"
                else "ASC"
            )

            sql = (
                f"SELECT "
                f"{', '.join(identity)} "
                f"FROM {table_name}"
                f"{where_sql} "
                f"ORDER BY {expression} "
                f"{direction} "
                f"LIMIT {limit}"
            )

            return self._success(
                sql,
                params,
            )

        # =========================================================
        # LIST / FILTER / GROUP
        # =========================================================

        if intent in {
            "LIST",
            "FILTER",
            "GROUP_BY",
        }:

            display = (
                self._select_display_columns(
                    columns
                )
            )

            if not display:

                return self._failure(
                    "No safe display columns were found."
                )

            sql = (
                f"SELECT "
                f"{', '.join(display)} "
                f"FROM {table_name}"
                f"{where_sql}"
            )

            if intent == "GROUP_BY":

                question_lower = (
                    question.lower()
                )

                if (
                    "by month"
                    in question_lower
                    or "monthly"
                    in question_lower
                ):

                    if not date_column:

                        return self._failure(
                            "I could not find a date column "
                            "for monthly grouping."
                        )

                    month_expression = (
                        self._month_expression(
                            date_column
                        )
                    )

                    sql = (
                        f"SELECT "
                        f"{month_expression} AS month, "
                        f"COUNT(*) AS record_count "
                        f"FROM {table_name}"
                        f"{where_sql} "
                        f"GROUP BY {month_expression} "
                        f"ORDER BY {month_expression}"
                    )

                elif (
                    "by year"
                    in question_lower
                    and date_column
                ):

                    year_expression = (
                        self._year_expression(
                            date_column
                        )
                    )

                    sql = (
                        f"SELECT "
                        f"{year_expression} AS year, "
                        f"COUNT(*) AS record_count "
                        f"FROM {table_name}"
                        f"{where_sql} "
                        f"GROUP BY {year_expression} "
                        f"ORDER BY {year_expression}"
                    )

            sql += " LIMIT 100"

            return self._success(
                sql,
                params,
            )

        # =========================================================
        # FALLBACK
        # =========================================================

        # If a metric exists, try a total rather than returning
        # SQL=None for a natural business question.

        if metric:

            expression, label = (
                self._resolve_aggregate_expression(
                    metric=metric,
                    columns=columns,
                    question=question,
                )
            )

            if expression:

                sql = (
                    f"SELECT SUM({expression}) "
                    f"AS {label} "
                    f"FROM {table_name}"
                    f"{where_sql}"
                )

                return self._success(
                    sql,
                    params,
                )

        return self._failure(
            f"I understand the question, but the intent "
            f"'{intent}' is not supported."
        )

    # =============================================================
    # METRIC RESOLUTION
    # =============================================================

    def _resolve_aggregate_expression(
        self,
        metric,
        columns,
        question,
    ):

        metric = (
            metric
            or self._metric_from_question(
                question
            )
        )

        numeric_columns = [
            column
            for column in columns
            if (
                self._is_numeric_type(
                    column.get(
                        "type",
                        "",
                    )
                )
                and self._safe_identifier(
                    column.get(
                        "name",
                        "",
                    )
                )
            )
        ]

        if not numeric_columns:

            return None, None

        aliases = set(
            self.METRIC_ALIASES.get(
                metric,
                [],
            )
        )

        question_tokens = (
            self._tokens(question)
        )

        scored = []

        for column in numeric_columns:

            name = column[
                "name"
            ]

            tokens = self._tokens(
                name
            )

            compact = (
                name.lower()
            )

            score = 0

            # Exact alias.
            if compact in aliases:

                score += 100

            # Token alias.
            score += (
                len(
                    tokens & aliases
                )
                * 18
            )

            # Question vocabulary.
            score += (
                len(
                    tokens
                    & question_tokens
                )
                * 8
            )

            # -----------------------------------------------------
            # Revenue
            # -----------------------------------------------------

            if metric == "revenue":

                if tokens & {
                    "sales",
                    "sale",
                    "revenue",
                    "turnover",
                    "income",
                    "amount",
                    "total",
                    "value",
                    "receipts",
                    "collection",
                    "collections",
                    "net",
                    "gross",
                }:

                    score += 35

                if tokens & {
                    "id",
                    "number",
                    "code",
                }:

                    score -= 40

            # -----------------------------------------------------
            # Balance
            # -----------------------------------------------------

            elif (
                metric
                == "total_balance"
            ):

                if tokens & {
                    "balance",
                    "outstanding",
                    "remaining",
                    "due",
                    "pending",
                    "receivable",
                    "payable",
                }:

                    score += 70

            # -----------------------------------------------------
            # Salary
            # -----------------------------------------------------

            elif metric == "salary":

                if tokens & {
                    "salary",
                    "wage",
                    "wages",
                    "pay",
                    "compensation",
                    "payroll",
                }:

                    score += 70

            # -----------------------------------------------------
            # Quantity
            # -----------------------------------------------------

            elif metric in {
                "quantity",
                "num_sarees",
            }:

                if tokens & {
                    "quantity",
                    "qty",
                    "units",
                    "count",
                    "volume",
                    "saree",
                    "production",
                }:

                    score += 70

            # -----------------------------------------------------
            # Price
            # -----------------------------------------------------

            elif metric == "price":

                if tokens & {
                    "price",
                    "rate",
                    "cost",
                    "selling",
                }:

                    score += 70

            # -----------------------------------------------------
            # Profit
            # -----------------------------------------------------

            elif metric == "profit":

                if tokens & {
                    "profit",
                    "margin",
                    "gain",
                }:

                    score += 70

            # -----------------------------------------------------
            # Loss
            # -----------------------------------------------------

            elif metric == "loss":

                if "loss" in tokens:

                    score += 70

            scored.append(
                (
                    score,
                    name,
                )
            )

        scored.sort(
            reverse=True
        )

        # Strong direct column.
        if (
            scored
            and scored[0][0] >= 25
        ):

            return (
                scored[0][1],
                self._aggregate_label(
                    metric,
                    scored[0][1],
                ),
            )

        # ---------------------------------------------------------
        # Revenue = quantity * price
        # ---------------------------------------------------------

        if metric == "revenue":

            quantity = (
                self._find_by_alias(
                    numeric_columns,
                    {
                        "quantity",
                        "qty",
                        "units",
                        "unit_count",
                    },
                )
            )

            price = (
                self._find_by_alias(
                    numeric_columns,
                    {
                        "price",
                        "unit_price",
                        "selling_price",
                        "rate",
                        "cost",
                    },
                )
            )

            if quantity and price:

                return (
                    f"({quantity} * {price})",
                    "total_revenue",
                )

        # ---------------------------------------------------------
        # Generic amount fallback
        # ---------------------------------------------------------

        generic = (
            self._find_by_alias(
                numeric_columns,
                {
                    "amount",
                    "total_amount",
                    "value",
                    "money",
                    "total",
                },
            )
        )

        if (
            generic
            and metric in {
                "revenue",
                "amount",
            }
        ):

            return (
                generic,
                self._aggregate_label(
                    metric,
                    generic,
                ),
            )

        return None, None

    # =============================================================
    # ALIAS FINDER
    # =============================================================

    def _find_by_alias(
        self,
        columns,
        aliases,
    ):

        best = None

        best_score = -1

        for column in columns:

            name = column[
                "name"
            ]

            tokens = self._tokens(
                name
            )

            score = (
                len(
                    tokens & aliases
                )
                * 10
            )

            if (
                name.lower()
                in aliases
            ):

                score += 30

            if score > best_score:

                best_score = score

                best = name

        if best_score > 0:

            return best

        return None

    # =============================================================
    # METRIC FROM QUESTION
    # =============================================================

    @staticmethod
    def _metric_from_question(
        question,
    ):

        q = question.lower()

        if any(
            term in q
            for term in (
                "sales",
                "sale",
                "revenue",
                "turnover",
                "income",
            )
        ):

            return "revenue"

        if (
            "balance" in q
            or "outstanding" in q
            or "due" in q
        ):

            return "total_balance"

        if (
            "salary" in q
            or "wage" in q
        ):

            return "salary"

        if (
            "quantity" in q
            or "qty" in q
        ):

            return "quantity"

        if (
            "profit" in q
            or "margin" in q
        ):

            return "profit"

        if "loss" in q:

            return "loss"

        return "amount"

    # =============================================================
    # LABEL
    # =============================================================

    @staticmethod
    def _aggregate_label(
        metric,
        column,
    ):

        return {

            "revenue":
                "total_revenue",

            "total_balance":
                "total_balance",

            "total_credit":
                "total_credit",

            "total_debit":
                "total_debit",

            "advance_amount":
                "total_advance_amount",

            "salary":
                "total_salary",

            "quantity":
                "total_quantity",

            "num_sarees":
                "total_num_sarees",

            "price":
                "total_price",

            "profit":
                "total_profit",

            "loss":
                "total_loss",

            "amount":
                "total_amount",

        }.get(
            metric,
            "total_"
            + QueryBuilder._safe_alias(
                column
            ),
        )

    # =============================================================
    # DATE COLUMN
    # =============================================================

    def _resolve_date_column(
        self,
        columns,
        question,
    ):

        candidates = []

        question_tokens = (
            self._tokens(question)
        )

        for column in columns:

            name = column.get(
                "name",
                "",
            )

            if not self._safe_identifier(
                name
            ):

                continue

            column_type = str(
                column.get(
                    "type",
                    "",
                )
            ).upper()

            tokens = self._tokens(
                name
            )

            score = 0

            if any(
                x in column_type
                for x in (
                    "DATE",
                    "TIMESTAMP",
                    "DATETIME",
                    "TIME",
                )
            ):

                score += 100

            if tokens & {
                "date",
                "datetime",
                "timestamp",
            }:

                score += 80

            if tokens & {
                "created",
                "updated",
                "sold",
                "issued",
                "posted",
                "recorded",
            }:

                score += 30

            score += (
                len(
                    tokens
                    & question_tokens
                )
                * 5
            )

            if tokens & {
                "id",
                "number",
                "code",
            }:

                score -= 50

            if score > 0:

                candidates.append(
                    (
                        score,
                        name,
                    )
                )

        candidates.sort(
            reverse=True
        )

        if candidates:

            return candidates[0][1]

        return None

    # =============================================================
    # DATE FILTER
    # =============================================================

    @staticmethod
    def _date_filter(
        date_column,
        date_range,
    ):

        if (
            not date_column
            or not date_range
        ):

            return "", {}

        start = date_range.get(
            "start"
        )

        end = date_range.get(
            "end"
        )

        if not start or not end:

            return "", {}

        return (
            (
                f" WHERE {date_column} "
                f">= :date_start "
                f"AND {date_column} "
                f"< :date_end"
            ),
            {
                "date_start":
                    date.fromisoformat(
                        start
                    ),

                "date_end":
                    date.fromisoformat(
                        end
                    ),
            },
        )

    # =============================================================
    # GROUPING
    # =============================================================

    @staticmethod
    def _month_expression(
        column,
    ):

        return (
            f"strftime('%Y-%m', {column})"
        )

    @staticmethod
    def _year_expression(
        column,
    ):

        return (
            f"strftime('%Y', {column})"
        )

    # =============================================================
    # RELATIONSHIP QUERY
    # =============================================================

    def _build_relationship_query(
        self,
        question,
        intent,
        entity_result,
        metric,
        query_plan,
        schema,
    ):

        tables = query_plan.get(
            "tables",
            [],
        )

        joins = query_plan.get(
            "joins",
            [],
        )

        primary = (
            query_plan.get(
                "primary_table"
            )
            or (
                tables[0]
                if tables
                else None
            )
        )

        if not primary or not joins:

            return self._failure(
                "The relationship plan is incomplete."
            )

        if any(
            not self._safe_identifier(
                table
            )
            for table in tables
        ):

            return self._failure(
                "Unsafe table name in relationship plan."
            )

        selected = []

        for table_name in tables:

            table = self._find_table(
                schema,
                table_name,
            )

            if not table:

                continue

            identities = (
                self._select_identity_columns(
                    table.get(
                        "columns",
                        [],
                    )
                )
            )

            for column in identities:

                selected.append(
                    f"{table_name}.{column}"
                )

        if not selected:

            selected = [
                f"{primary}.*"
            ]

        sql = (
            f"SELECT "
            f"{', '.join(selected)} "
            f"FROM {primary}"
        )

        joined = {
            primary
        }

        for join in joins:

            left = join.get(
                "left_table"
            )

            right = join.get(
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

            if (
                not left
                or not right
                or len(left_columns)
                != len(right_columns)
            ):

                return self._failure(
                    "Invalid relationship definition."
                )

            conditions = []

            for (
                left_column,
                right_column,
            ) in zip(
                left_columns,
                right_columns,
            ):

                if (
                    not self._safe_identifier(
                        left_column
                    )
                    or
                    not self._safe_identifier(
                        right_column
                    )
                ):

                    return self._failure(
                        "Unsafe relationship column."
                    )

                conditions.append(
                    f"{left}.{left_column} = "
                    f"{right}.{right_column}"
                )

            if right not in joined:

                sql += (
                    f" JOIN {right} "
                    f"ON "
                    f"{' AND '.join(conditions)}"
                )

                joined.add(
                    right
                )

        limit = max(
            1,
            min(
                int(
                    entity_result.get(
                        "limit"
                    )
                    or 100
                ),
                100,
            ),
        )

        sql += (
            f" LIMIT {limit}"
        )

        return self._success(
            sql,
            {},
        )

    # =============================================================
    # TABLE FINDER
    # =============================================================

    @staticmethod
    def _find_table(
        schema,
        name,
    ):

        for table in schema.get(
            "tables",
            [],
        ):

            if (
                table.get(
                    "table_name"
                )
                == name
            ):

                return table

        return None

    # =============================================================
    # IDENTITY COLUMNS
    # =============================================================

    @staticmethod
    def _select_identity_columns(
        columns,
    ):

        result = []

        identity_tokens = {
            "name",
            "number",
            "code",
            "title",
            "description",
            "email",
        }

        for column in columns:

            name = column.get(
                "name",
                "",
            )

            if not QueryBuilder._safe_identifier(
                name
            ):

                continue

            lower = name.lower()

            if any(
                word in lower
                for word in QueryBuilder.SENSITIVE_WORDS
            ):

                continue

            tokens = QueryBuilder._tokens(
                name
            )

            if (
                tokens
                & identity_tokens
                or lower == "id"
            ):

                result.append(
                    name
                )

            if len(result) >= 5:

                break

        return result

    # =============================================================
    # DISPLAY COLUMNS
    # =============================================================

    @staticmethod
    def _select_display_columns(
        columns,
    ):

        result = []

        for column in columns:

            name = column.get(
                "name",
                "",
            )

            lower = name.lower()

            if not QueryBuilder._safe_identifier(
                name
            ):

                continue

            if any(
                word in lower
                for word in QueryBuilder.SENSITIVE_WORDS
            ):

                continue

            result.append(
                name
            )

            if len(result) >= 10:

                break

        return result

    # =============================================================
    # IDENTITY QUESTION
    # =============================================================

    @staticmethod
    def _asks_for_identity(
        question,
    ):

        return bool(
            re.search(
                r"\b("
                r"who|which|name|person|"
                r"employee|customer|weaver|"
                r"loom|product"
                r")\b",
                question.lower(),
            )
        )

    # =============================================================
    # TOKENS
    # =============================================================

    @staticmethod
    def _tokens(
        value,
    ):

        value = re.sub(
            r"([a-z])([A-Z])",
            r"\1 \2",
            str(value),
        ).lower()

        return set(
            re.findall(
                r"[a-z0-9]+",
                value.replace(
                    "_",
                    " ",
                ),
            )
        )

    # =============================================================
    # NUMERIC TYPE
    # =============================================================

    @staticmethod
    def _is_numeric_type(
        value,
    ):

        text = str(
            value
        ).upper()

        return any(
            name in text
            for name in (
                "INTEGER",
                "BIGINT",
                "SMALLINT",
                "DECIMAL",
                "NUMERIC",
                "REAL",
                "DOUBLE",
                "FLOAT",
                "MONEY",
            )
        )

    # =============================================================
    # SAFE ALIAS
    # =============================================================

    @staticmethod
    def _safe_alias(
        value,
    ):

        value = re.sub(
            r"[^a-zA-Z0-9_]",
            "_",
            str(value),
        )

        return (
            value.strip("_")
            or "value"
        )

    # =============================================================
    # SAFE IDENTIFIER
    # =============================================================

    @staticmethod
    def _safe_identifier(
        identifier,
    ):

        return bool(
            identifier
        ) and bool(
            re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]*",
                str(identifier),
            )
        )

    # =============================================================
    # SUCCESS
    # =============================================================

    @staticmethod
    def _success(
        sql,
        params=None,
    ):

        return {
            "success": True,
            "sql": sql,
            "params": params or {},
            "reason": None,
        }

    # =============================================================
    # FAILURE
    # =============================================================

    @staticmethod
    def _failure(
        reason,
    ):

        return {
            "success": False,
            "sql": None,
            "params": {},
            "reason": reason,
        }


query_builder = QueryBuilder()
