import re


class BusinessSchemaMapper:
    """
    Maps business concepts to the most appropriate database
    tables and columns using question context.

    This module does NOT generate SQL.
    It only determines the most likely business meaning
    of database schema elements.
    """

    CONCEPT_KEYWORDS = {

        "employee": [
            "employee",
            "employees",
            "staff",
            "worker",
            "workers",
            "personnel",
            "employee_name",
            "worker_name",
            "staff_name",
        ],

        "customer": [
            "customer",
            "customers",
            "client",
            "clients",
            "buyer",
            "buyers",
            "customer_name",
            "client_name",
            "buyer_name",
        ],

        "supplier": [
            "supplier",
            "suppliers",
            "vendor",
            "vendors",
            "supplier_name",
            "vendor_name",
        ],

        "product": [
            "product",
            "products",
            "item",
            "items",
            "goods",
            "merchandise",
            "product_name",
            "item_name",
        ],

        "order": [
            "order",
            "orders",
            "purchase",
            "purchases",
            "order_id",
            "order_number",
            "purchase_id",
        ],

        "payment": [
            "payment",
            "payments",
            "transaction",
            "transactions",
            "payment_id",
            "transaction_id",
        ],

        "invoice": [
            "invoice",
            "invoices",
            "bill",
            "billing",
            "invoice_id",
            "invoice_number",
        ],

        "revenue": [
            "revenue",
            "turnover",
            "income",
            "earnings",
            "sales_value",
            "revenue_amount",
        ],

        "sales": [
            "sale",
            "sales",
            "selling",
            "sold",
            "sales_amount",
            "sales_value",
        ],

        "balance": [
            "balance",
            "balances",
            "outstanding",
            "outstanding_balance",
            "remaining_balance",
            "amount_due",
            "due_amount",
            "balance_amount",
        ],

        "advance": [
            "advance",
            "advances",
            "advance_amount",
            "advanced_amount",
            "amount_given",
            "money_given",
        ],

        "credit": [
            "credit",
            "credits",
            "credited",
            "credit_amount",
            "amount_credit",
        ],

        "debit": [
            "debit",
            "debits",
            "debited",
            "debit_amount",
            "amount_debit",
        ],

        "amount": [
            "amount",
            "amounts",
            "value",
            "values",
            "money",
            "monetary_value",
            "total_amount",
        ],

        "price": [
            "price",
            "prices",
            "cost",
            "costs",
            "rate",
            "rates",
            "unit_price",
            "selling_price",
        ],

        "profit": [
            "profit",
            "profits",
            "profit_amount",
            "profit_value",
            "gain",
            "gains",
        ],

        "loss": [
            "loss",
            "losses",
            "loss_amount",
            "loss_value",
        ],

        "salary": [
            "salary",
            "salaries",
            "pay",
            "wage",
            "wages",
            "compensation",
            "salary_amount",
            "pay_amount",
        ],

        "quantity": [
            "quantity",
            "quantities",
            "qty",
            "units",
            "unit_count",
            "item_quantity",
        ],

        "production": [
            "production",
            "produced",
            "manufactured",
            "manufacturing",
            "output",
            "production_output",
        ],

        "stock": [
            "stock",
            "stocks",
            "inventory",
            "inventories",
            "stock_quantity",
            "inventory_quantity",
            "available_stock",
            "available_quantity",
            "stock_level",
        ],

        "return": [
            "return",
            "returns",
            "returned",
            "return_quantity",
            "returned_quantity",
        ],

        "department": [
            "department",
            "departments",
            "division",
            "divisions",
            "team",
            "department_name",
            "division_name",
        ],

        "date": [
            "date",
            "created_at",
            "updated_at",
            "order_date",
            "sale_date",
            "payment_date",
            "transaction_date",
        ],

        "month": [
            "month",
            "monthly",
        ],

        "year": [
            "year",
            "yearly",
            "annual",
        ],
    }

    # Concepts where numeric columns are normally meaningful.
    NUMERIC_CONCEPTS = {
        "balance",
        "advance",
        "credit",
        "debit",
        "amount",
        "price",
        "profit",
        "loss",
        "salary",
        "quantity",
        "stock",
        "revenue",
        "sales",
        "production",
    }

    # Columns that should almost never be treated as business
    # measures even though they may technically be numeric.
    IDENTIFIER_COLUMNS = {
        "id",
        "user_id",
        "employee_id",
        "customer_id",
        "supplier_id",
        "product_id",
        "order_id",
        "payment_id",
        "invoice_id",
        "loom_id",
        "weaver_id",
        "saree_id",
        "material_id",
        "production_warp_id",
        "warp_id",
        "weft_id",
    }

    # Columns representing state/category rather than quantity/value.
    STATUS_COLUMNS = {
        "status",
        "state",
        "condition",
        "type",
        "category",
        "stage",
        "mode",
        "stock_status",
        "payment_type",
        "account_type",
        "loom_type",
        "saree_type",
    }

    # Business concepts that have strong preferred table patterns.
    PREFERRED_TABLES = {

        "employee": [
            "employees",
        ],

        "customer": [
            "customers",
        ],

        "supplier": [
            "suppliers",
        ],

        "product": [
            "products",
        ],

        "order": [
            "orders",
            "sales_orders",
            "material_orders",
        ],

        "payment": [
            "payments",
        ],

        "invoice": [
            "invoices",
        ],

        "salary": [
            "employees",
        ],

        "balance": [
            "weavers",
            "looms",
        ],

        "advance": [
            "weavers",
        ],

        "credit": [
            "looms",
            "payments",
        ],

        "debit": [
            "looms",
            "payments",
        ],

        "stock": [
            "material_stock",
            "silver_material_stock",
            "color_silk_stock",
            "material_out_stock",
            "gold_company_stock",
            "silver_company_stock",
        ],

        "production": [
            "production_warps",
            "saree_entries",
            "wefts",
        ],
    }

    def map_concepts(
        self,
        business_language_result: dict,
        schema: dict,
    ) -> dict:

        question = business_language_result.get(
            "question",
            "",
        )

        normalized_question = self._normalize(
            question
        )

        concepts = [
            item["concept"]
            for item in business_language_result.get(
                "business_terms",
                [],
            )
        ]

        mappings = []

        for concept in concepts:

            mapping = self._map_concept(
                concept=concept,
                schema=schema,
                question=normalized_question,
            )

            mappings.append(mapping)

        return {
            "question": question,
            "concepts": concepts,
            "mappings": mappings,
        }

    def _map_concept(
        self,
        concept: str,
        schema: dict,
        question: str,
    ) -> dict:

        keywords = self.CONCEPT_KEYWORDS.get(
            concept,
            [concept],
        )

        numeric_question = self._is_numeric_question(
            question
        )

        table_candidates = []
        column_candidates = []

        for table in schema.get(
            "tables",
            [],
        ):

            table_name = table["table_name"]

            table_score = self._score_table(
                table_name=table_name,
                concept=concept,
                keywords=keywords,
            )

            if table_score > 0:

                table_candidates.append({
                    "table_name": table_name,
                    "score": table_score,
                })

            for column in table.get(
                "columns",
                [],
            ):

                column_name = str(
                    column["name"]
                )

                column_type = str(
                    column.get("type", "")
                )

                column_score = self._score_column(
                    column_name=column_name,
                    column_type=column_type,
                    concept=concept,
                    keywords=keywords,
                    numeric_question=numeric_question,
                )

                if column_score > 0:

                    column_candidates.append({
                        "table_name": table_name,
                        "column_name": column_name,
                        "type": column_type,
                        "score": column_score,
                    })

        table_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        column_candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        best_table = (
            table_candidates[0]
            if table_candidates
            else None
        )

        best_column = (
            column_candidates[0]
            if column_candidates
            else None
        )

        confidence = self._calculate_confidence(
            best_table=best_table,
            best_column=best_column,
        )

        return {
            "concept": concept,
            "best_table": best_table,
            "best_column": best_column,
            "table_candidates": table_candidates[:10],
            "column_candidates": column_candidates[:10],
            "confidence": confidence,
        }

    def _score_table(
        self,
        table_name: str,
        concept: str,
        keywords: list[str],
    ) -> int:

        score = 0

        normalized_table = (
            self._normalize_identifier(
                table_name
            )
        )

        # Strong preferred-table match.
        preferred_tables = self.PREFERRED_TABLES.get(
            concept,
            [],
        )

        for preferred_table in preferred_tables:

            preferred_normalized = (
                self._normalize_identifier(
                    preferred_table
                )
            )

            if normalized_table == preferred_normalized:
                score += 40

        # Generic concept/table matching.
        if normalized_table == concept:
            score += 30

        if normalized_table == concept + "s":
            score += 30

        for keyword in keywords:

            keyword_normalized = (
                self._normalize_identifier(
                    keyword
                )
            )

            if normalized_table == keyword_normalized:
                score += 25

            elif keyword_normalized in normalized_table:
                score += 10

        return score

    def _score_column(
        self,
        column_name: str,
        column_type: str,
        concept: str,
        keywords: list[str],
        numeric_question: bool,
    ) -> int:

        score = 0

        normalized_column = (
            self._normalize_identifier(
                column_name
            )
        )

        # ---------------------------------------------------------
        # 1. Reject identifiers.
        # ---------------------------------------------------------

        if self._is_identifier_column(
            normalized_column
        ):

            # ID columns should not answer business
            # value/quantity questions.
            if concept in self.NUMERIC_CONCEPTS:
                return 0

        # ---------------------------------------------------------
        # 2. Reject status/category columns for numeric concepts.
        # ---------------------------------------------------------

        if self._is_status_column(
            normalized_column
        ):

            if concept in self.NUMERIC_CONCEPTS:
                return 0

        # ---------------------------------------------------------
        # 3. Exact concept match.
        # ---------------------------------------------------------

        if normalized_column == concept:
            score += 40

        # ---------------------------------------------------------
        # 4. Keyword matching.
        # ---------------------------------------------------------

        for keyword in keywords:

            keyword_normalized = (
                self._normalize_identifier(
                    keyword
                )
            )

            if normalized_column == keyword_normalized:

                score += 35

            elif normalized_column.endswith(
                "_" + keyword_normalized
            ):

                score += 25

            elif keyword_normalized in normalized_column:

                score += 12

        # ---------------------------------------------------------
        # 5. Numeric validation.
        # ---------------------------------------------------------

        if concept in self.NUMERIC_CONCEPTS:

            if self._is_numeric_type(
                column_type
            ):

                score += 20

            else:

                # A text column should not normally be used
                # for a numeric business measure.
                score -= 20

        # ---------------------------------------------------------
        # 6. Quantity-specific intelligence.
        # ---------------------------------------------------------

        if concept == "stock":

            quantity_words = [
                "quantity",
                "qty",
                "weight",
                "amount",
                "available",
                "stock",
                "inventory",
                "count",
                "units",
            ]

            for word in quantity_words:

                if word in normalized_column:

                    score += 20

            # Strongly reject status fields.
            if (
                "status" in normalized_column
                or "state" in normalized_column
                or "type" in normalized_column
                or "category" in normalized_column
            ):

                score -= 40

        # ---------------------------------------------------------
        # 7. Salary-specific intelligence.
        # ---------------------------------------------------------

        if concept == "salary":

            if normalized_column == "salary":
                score += 40

            if (
                "salary" in normalized_column
                or "wage" in normalized_column
                or "pay" in normalized_column
            ):
                score += 20

        # ---------------------------------------------------------
        # 8. Balance-specific intelligence.
        # ---------------------------------------------------------

        if concept == "balance":

            if (
                "balance" in normalized_column
                or "outstanding" in normalized_column
                or "due" in normalized_column
            ):
                score += 25

        # ---------------------------------------------------------
        # 9. Advance-specific intelligence.
        # ---------------------------------------------------------

        if concept == "advance":

            if "advance" in normalized_column:
                score += 30

        # ---------------------------------------------------------
        # 10. Credit-specific intelligence.
        # ---------------------------------------------------------

        if concept == "credit":

            if (
                "credit" in normalized_column
                or "amount_credit" in normalized_column
            ):
                score += 30

        # ---------------------------------------------------------
        # 11. Debit-specific intelligence.
        # ---------------------------------------------------------

        if concept == "debit":

            if (
                "debit" in normalized_column
                or "amount_debit" in normalized_column
            ):
                score += 30

        return max(score, 0)

    def _is_numeric_question(
        self,
        question: str,
    ) -> bool:

        numeric_terms = [
            "total",
            "sum",
            "average",
            "avg",
            "highest",
            "lowest",
            "maximum",
            "minimum",
            "largest",
            "smallest",
            "most",
            "least",
            "how much",
            "amount",
            "value",
            "quantity",
            "number",
            "many",
            "balance",
            "advance",
            "credit",
            "debit",
            "salary",
            "revenue",
            "profit",
            "loss",
            "stock",
            "inventory",
        ]

        for term in numeric_terms:

            if term in question:
                return True

        return False

    @classmethod
    def _is_identifier_column(
        cls,
        column_name: str,
    ) -> bool:

        if column_name in cls.IDENTIFIER_COLUMNS:
            return True

        if column_name == "id":
            return True

        if column_name.endswith("_id"):
            return True

        return False

    @classmethod
    def _is_status_column(
        cls,
        column_name: str,
    ) -> bool:

        if column_name in cls.STATUS_COLUMNS:
            return True

        for status_word in [
            "status",
            "state",
            "condition",
            "category",
            "stage",
            "type",
        ]:

            if (
                column_name == status_word
                or column_name.endswith(
                    "_" + status_word
                )
            ):
                return True

        return False

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
            "MONEY",
        ]

        upper_type = column_type.upper()

        return any(
            numeric_type in upper_type
            for numeric_type in numeric_types
        )

    @staticmethod
    def _calculate_confidence(
        best_table,
        best_column,
    ) -> float:

        if not best_column and not best_table:
            return 0.0

        if best_column:

            score = best_column["score"]

            if score >= 80:
                return 0.99

            if score >= 60:
                return 0.98

            if score >= 45:
                return 0.95

            if score >= 35:
                return 0.90

            if score >= 25:
                return 0.85

            if score >= 15:
                return 0.75

            if score >= 10:
                return 0.65

        if best_table:

            score = best_table["score"]

            if score >= 50:
                return 0.95

            if score >= 40:
                return 0.90

            if score >= 30:
                return 0.85

            if score >= 20:
                return 0.80

            if score >= 10:
                return 0.70

        return 0.50

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        text = text.lower()

        text = re.sub(
            r"[^\w\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _normalize_identifier(
        text: str,
    ) -> str:

        text = text.lower()

        text = text.replace(
            "-",
            "_",
        )

        text = re.sub(
            r"[^a-z0-9_]",
            "_",
            text,
        )

        text = re.sub(
            r"_+",
            "_",
            text,
        )

        return text.strip("_")


business_schema_mapper = BusinessSchemaMapper()