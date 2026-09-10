
from __future__ import annotations

import re


class ReasoningEngine:
    """
    Select the best table from the REAL database schema.

    The user's vocabulary and the database vocabulary do not need
    to be identical.

    Example:

        User says:
            sales

        Database may contain:
            invoices
            invoice_records
            transactions
            order_history
            billing_details

    The engine scores the actual schema instead of requiring a
    table literally named 'sales'.
    """

    BUSINESS_ALIASES = {

        "sales": {
            "sale",
            "sales",
            "revenue",
            "turnover",
            "income",
            "receipt",
            "receipts",
            "collection",
            "collections",
            "invoice",
            "invoices",
            "bill",
            "bills",
            "order",
            "orders",
            "transaction",
            "transactions",
        },

        "balance": {
            "balance",
            "outstanding",
            "due",
            "remaining",
            "receivable",
            "payable",
            "pending",
        },

        "credit": {
            "credit",
            "credited",
            "credit_amount",
        },

        "debit": {
            "debit",
            "debited",
            "debit_amount",
        },

        "advance": {
            "advance",
            "advanced",
            "prepayment",
        },

        "salary": {
            "salary",
            "wage",
            "wages",
            "pay",
            "payroll",
            "compensation",
        },

        "quantity": {
            "quantity",
            "qty",
            "units",
            "count",
            "volume",
        },

        "price": {
            "price",
            "rate",
            "cost",
            "unit_price",
            "selling_price",
        },

        "profit": {
            "profit",
            "gain",
            "margin",
        },

        "loss": {
            "loss",
        },

        "production": {
            "production",
            "produced",
            "manufactured",
            "output",
        },

        "stock": {
            "stock",
            "inventory",
            "available",
            "on_hand",
        },

        "customer": {
            "customer",
            "client",
            "buyer",
            "purchaser",
        },

        "product": {
            "product",
            "item",
            "sku",
            "article",
        },

        "employee": {
            "employee",
            "staff",
            "personnel",
            "worker",
        },
    }

    METRIC_ALIASES = {

        "revenue": {
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
            "gross_sales",
            "net_sales",
            "sales_amount",
            "sales_value",
            "selling_amount",
            "selling_value",
            "invoice_amount",
            "invoice_total",
            "bill_amount",
            "grand_total",
            "net_amount",
            "gross_amount",
        },

        "total_balance": {
            "balance",
            "total_balance",
            "outstanding_balance",
            "remaining_balance",
            "amount_due",
            "due_amount",
            "pending_amount",
            "receivable",
            "payable",
        },

        "total_credit": {
            "credit",
            "total_credit",
            "credit_amount",
            "amount_credit",
            "credited_amount",
        },

        "total_debit": {
            "debit",
            "total_debit",
            "debit_amount",
            "amount_debit",
            "debited_amount",
        },

        "advance_amount": {
            "advance",
            "advance_amount",
            "advance_money",
            "prepayment",
        },

        "salary": {
            "salary",
            "wage",
            "wages",
            "pay",
            "compensation",
            "payroll",
        },

        "quantity": {
            "quantity",
            "qty",
            "units",
            "unit_count",
            "volume",
            "count",
        },

        "num_sarees": {
            "num_sarees",
            "saree_count",
            "sarees_count",
            "no_of_sarees",
            "production_quantity",
        },

        "price": {
            "price",
            "unit_price",
            "selling_price",
            "rate",
            "cost",
        },

        "amount": {
            "amount",
            "total_amount",
            "net_amount",
            "gross_amount",
            "value",
            "money",
        },

        "profit": {
            "profit",
            "profit_amount",
            "net_profit",
            "gross_profit",
            "margin",
        },

        "loss": {
            "loss",
            "loss_amount",
            "net_loss",
            "gross_loss",
        },
    }

    # =============================================================
    # MAIN
    # =============================================================

    def reason(
        self,
        question,
        intent_result,
        entity_result,
        schema,
        metric_result=None,
        business_context_result=None,
    ):

        intent = intent_result.get(
            "intent",
            "UNKNOWN",
        )

        entity_types = [
            entity.get("type")
            for entity in entity_result.get(
                "entities",
                [],
            )
        ]

        metric = (
            metric_result.get("metric")
            if metric_result
            else None
        )

        question_tokens = self._tokens(
            question
        )

        candidates = []

        for table in schema.get(
            "tables",
            [],
        ):

            table_name = table.get(
                "table_name",
                "",
            )

            columns = table.get(
                "columns",
                [],
            )

            score, reasons = self._score_table(
                table_name=table_name,
                columns=columns,
                question_tokens=question_tokens,
                entities=entity_types,
                metric=metric,
                intent=intent,
                has_date_range=bool(
                    entity_result.get(
                        "date_range"
                    )
                ),
            )

            if score > 0:

                candidates.append(
                    {
                        "table_name": table_name,
                        "score": score,
                        "reasons": reasons,
                        "columns": columns,
                    }
                )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        selected = (
            candidates[0]
            if candidates
            else None
        )

        return {
            "question": question,

            "intent": intent,

            "entities": entity_types,

            "limit": entity_result.get(
                "limit"
            ),

            "metric": metric,

            "business_concepts": (
                self._business_concepts(
                    question_tokens
                )
            ),

            "selected_table": selected,

            "candidate_tables": candidates[:25],
        }

    # =============================================================
    # TABLE SCORING
    # =============================================================

    def _score_table(
        self,
        table_name,
        columns,
        question_tokens,
        entities,
        metric,
        intent,
        has_date_range=False,
    ):

        table_tokens = self._tokens(
            table_name
        )

        column_names = [
            str(
                column.get(
                    "name",
                    "",
                )
            )
            for column in columns
        ]

        score = 0

        reasons = []

        table_lower = table_name.lower()

        # ---------------------------------------------------------
        # Entity -> table
        # ---------------------------------------------------------

        for entity in entities:

            aliases = self.BUSINESS_ALIASES.get(
                entity,
                {entity},
            )

            if (
                table_tokens & aliases
                or entity in table_tokens
            ):

                score += 30

                reasons.append(
                    f"table matches entity '{entity}'"
                )

        # ---------------------------------------------------------
        # Question -> table
        # ---------------------------------------------------------

        overlap = (
            question_tokens
            & table_tokens
        )

        if overlap:

            score += min(
                24,
                len(overlap) * 8,
            )

            reasons.append(
                "table name matches question vocabulary"
            )

        # ---------------------------------------------------------
        # Metric columns
        # ---------------------------------------------------------

        aliases = self.METRIC_ALIASES.get(
            metric,
            set(),
        )

        best_metric_score = 0

        for column_name in column_names:

            column_tokens = self._tokens(
                column_name
            )

            compact = (
                column_name
                .lower()
                .replace(
                    " ",
                    "_",
                )
            )

            if compact in aliases:

                best_metric_score = max(
                    best_metric_score,
                    45,
                )

            elif (
                column_tokens & aliases
            ):

                best_metric_score = max(
                    best_metric_score,
                    35,
                )

        if best_metric_score:

            score += best_metric_score

            reasons.append(
                "contains a column semantically matching requested metric"
            )

        # ---------------------------------------------------------
        # Column characteristics
        # ---------------------------------------------------------

        has_date = any(
            self._is_date_type(
                column.get(
                    "type",
                    "",
                )
            )
            or self._looks_date(
                column.get(
                    "name",
                    "",
                )
            )
            for column in columns
        )

        money_columns = [
            column
            for column in columns
            if (
                self._looks_money(
                    column.get(
                        "name",
                        "",
                    )
                )
                and
                self._is_numeric_type(
                    column.get(
                        "type",
                        "",
                    )
                )
            )
        ]

        quantity_columns = [
            column
            for column in columns
            if (
                self._looks_quantity(
                    column.get(
                        "name",
                        "",
                    )
                )
                and
                self._is_numeric_type(
                    column.get(
                        "type",
                        "",
                    )
                )
            )
        ]

        price_columns = [
            column
            for column in columns
            if (
                self._looks_price(
                    column.get(
                        "name",
                        "",
                    )
                )
                and
                self._is_numeric_type(
                    column.get(
                        "type",
                        "",
                    )
                )
            )
        ]

        # ---------------------------------------------------------
        # Revenue
        # ---------------------------------------------------------

        if metric == "revenue":

            if money_columns:

                score += 22

                reasons.append(
                    "contains numeric sales/amount column"
                )

            if (
                quantity_columns
                and price_columns
            ):

                score += 18

                reasons.append(
                    "contains quantity and price columns for derived sales"
                )

            if has_date:

                score += 15

                reasons.append(
                    "contains a usable date column"
                )

            transaction_words = (
                "sale",
                "sales",
                "invoice",
                "bill",
                "order",
                "receipt",
                "transaction",
                "revenue",
                "income",
                "payment",
            )

            if any(
                word in table_lower
                for word in transaction_words
            ):

                score += 20

                reasons.append(
                    "table name looks transactional"
                )

        # ---------------------------------------------------------
        # Balance
        # ---------------------------------------------------------

        if metric == "total_balance":

            if any(
                self._looks_balance(
                    column.get(
                        "name",
                        "",
                    )
                )
                for column in columns
            ):

                score += 25

                reasons.append(
                    "contains balance-like column"
                )

        # ---------------------------------------------------------
        # Date requirement
        # ---------------------------------------------------------

        if has_date_range:

            if has_date:

                score += 30

                reasons.append(
                    "date column supports requested period"
                )

            else:

                score -= 20

                reasons.append(
                    "no date column for period question"
                )

        # ---------------------------------------------------------
        # System tables
        # ---------------------------------------------------------

        if table_lower in {
            "users",
            "alembic_version",
            "sessions",
            "tokens",
        }:

            score -= 40

        # ---------------------------------------------------------
        # Revenue table must have value evidence
        # ---------------------------------------------------------

        if (
            metric == "revenue"
            and not money_columns
            and not (
                quantity_columns
                and price_columns
            )
        ):

            score -= 15

        return score, reasons

    # =============================================================
    # TOKENIZER
    # =============================================================

    @staticmethod
    def _tokens(
        value,
    ):

        text = re.sub(
            r"([a-z])([A-Z])",
            r"\1 \2",
            str(value),
        ).lower()

        return set(
            re.findall(
                r"[a-z0-9]+",
                text.replace(
                    "_",
                    " ",
                ),
            )
        )

    # =============================================================
    # BUSINESS CONCEPTS
    # =============================================================

    def _business_concepts(
        self,
        tokens,
    ):

        result = []

        for concept, aliases in (
            self.BUSINESS_ALIASES.items()
        ):

            if (
                tokens & aliases
                or concept in tokens
            ):

                result.append(
                    concept
                )

        return result

    # =============================================================
    # TYPES
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

    @staticmethod
    def _is_date_type(
        value,
    ):

        text = str(
            value
        ).upper()

        return any(
            name in text
            for name in (
                "DATE",
                "TIMESTAMP",
                "DATETIME",
                "TIME",
            )
        )

    # =============================================================
    # DATE NAME
    # =============================================================

    @staticmethod
    def _looks_date(
        name,
    ):

        tokens = set(
            re.findall(
                r"[a-z0-9]+",
                str(name)
                .lower()
                .replace(
                    "_",
                    " ",
                ),
            )
        )

        return bool(
            tokens
            & {
                "date",
                "datetime",
                "timestamp",
                "created",
                "updated",
                "issued",
                "posted",
                "recorded",
            }
        )

    # =============================================================
    # MONEY NAME
    # =============================================================

    @staticmethod
    def _looks_money(
        name,
    ):

        tokens = set(
            re.findall(
                r"[a-z0-9]+",
                str(name)
                .lower()
                .replace(
                    "_",
                    " ",
                ),
            )
        )

        return bool(
            tokens
            & {
                "amount",
                "total",
                "revenue",
                "sales",
                "sale",
                "value",
                "money",
                "income",
                "turnover",
                "price",
                "cost",
                "credit",
                "debit",
                "balance",
                "receipt",
                "receipts",
                "collection",
                "collections",
                "payment",
                "paid",
                "net",
                "gross",
            }
        )

    # =============================================================
    # QUANTITY
    # =============================================================

    @staticmethod
    def _looks_quantity(
        name,
    ):

        tokens = set(
            re.findall(
                r"[a-z0-9]+",
                str(name)
                .lower()
                .replace(
                    "_",
                    " ",
                ),
            )
        )

        return bool(
            tokens
            & {
                "quantity",
                "qty",
                "units",
                "count",
                "volume",
                "number",
            }
        )

    # =============================================================
    # PRICE
    # =============================================================

    @staticmethod
    def _looks_price(
        name,
    ):

        tokens = set(
            re.findall(
                r"[a-z0-9]+",
                str(name)
                .lower()
                .replace(
                    "_",
                    " ",
                ),
            )
        )

        return bool(
            tokens
            & {
                "price",
                "rate",
                "cost",
                "selling",
            }
        )

    # =============================================================
    # BALANCE
    # =============================================================

    @staticmethod
    def _looks_balance(
        name,
    ):

        tokens = set(
            re.findall(
                r"[a-z0-9]+",
                str(name)
                .lower()
                .replace(
                    "_",
                    " ",
                ),
            )
        )

        return bool(
            tokens
            & {
                "balance",
                "outstanding",
                "remaining",
                "due",
                "receivable",
                "payable",
                "pending",
            }
        )


reasoning_engine = ReasoningEngine()

