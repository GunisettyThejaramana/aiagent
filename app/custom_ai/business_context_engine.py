import re


class BusinessContextEngine:
    """
    Determines the business meaning of concepts based on the
    question context.

    This engine does not generate SQL.

    Its job is to answer questions such as:

        "stock"    -> current inventory
        "balance"  -> outstanding financial value
        "salary"   -> employee compensation
        "advance"  -> money given in advance
        "revenue"  -> business income

    It also identifies concepts that should NOT be used for
    certain business meanings.
    """

    CONTEXT_RULES = {

        "stock": {
            "meaning": "current_inventory",

            "preferred_keywords": [
                "available",
                "inventory",
                "in stock",
                "current stock",
                "stock level",
                "remaining stock",
                "how much stock",
                "how much inventory",
                "available stock",
            ],

            "preferred_column_keywords": [
                "quantity",
                "qty",
                "stock_quantity",
                "inventory_quantity",
                "available_quantity",
                "weight",
                "stock_level",
            ],

            "preferred_table_keywords": [
                "stock",
                "inventory",
                "company_stock",
                "material_stock",
            ],

            "avoid_table_keywords": [
                "order",
                "orders",
                "purchase",
                "return",
                "payment",
                "activity",
                "log",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "balance": {
            "meaning": "outstanding_financial_balance",

            "preferred_keywords": [
                "balance",
                "outstanding",
                "remaining",
                "due",
                "amount due",
                "outstanding balance",
                "remaining balance",
            ],

            "preferred_column_keywords": [
                "balance",
                "total_balance",
                "outstanding",
                "amount_due",
                "due_amount",
            ],

            "preferred_table_keywords": [
                "weaver",
                "employee",
                "customer",
                "account",
                "ledger",
                "payment",
            ],

            "avoid_table_keywords": [
                "activity",
                "log",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "advance": {
            "meaning": "advance_money_given",

            "preferred_keywords": [
                "advance",
                "advanced",
                "money given",
                "amount given",
                "advance payment",
            ],

            "preferred_column_keywords": [
                "advance",
                "advance_amount",
                "advanced_amount",
                "amount_given",
                "money_given",
            ],

            "preferred_table_keywords": [
                "weaver",
                "employee",
                "customer",
                "payment",
            ],

            "avoid_table_keywords": [
                "activity",
                "log",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "salary": {
            "meaning": "employee_compensation",

            "preferred_keywords": [
                "salary",
                "salaries",
                "pay",
                "wage",
                "wages",
                "compensation",
                "payroll",
            ],

            "preferred_column_keywords": [
                "salary",
                "salary_amount",
                "pay",
                "pay_amount",
                "wage",
            ],

            "preferred_table_keywords": [
                "employee",
                "employees",
                "staff",
                "payroll",
            ],

            "avoid_table_keywords": [
                "payment",
                "payments",
                "activity",
                "log",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "credit": {
            "meaning": "credited_amount",

            "preferred_keywords": [
                "credit",
                "credited",
                "credit amount",
                "amount credited",
            ],

            "preferred_column_keywords": [
                "credit",
                "credit_amount",
                "amount_credit",
                "credited",
            ],

            "preferred_table_keywords": [
                "payment",
                "payments",
                "account",
                "ledger",
                "loom",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "debit": {
            "meaning": "debited_amount",

            "preferred_keywords": [
                "debit",
                "debited",
                "debit amount",
                "amount debited",
            ],

            "preferred_column_keywords": [
                "debit",
                "debit_amount",
                "amount_debit",
                "debited",
            ],

            "preferred_table_keywords": [
                "payment",
                "payments",
                "account",
                "ledger",
                "loom",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "revenue": {
            "meaning": "business_income",

            "preferred_keywords": [
                "revenue",
                "turnover",
                "income",
                "earnings",
                "sales value",
                "business income",
            ],

            "preferred_column_keywords": [
                "revenue",
                "revenue_amount",
                "sales",
                "sales_value",
                "amount",
            ],

            "preferred_table_keywords": [
                "revenue",
                "sales",
                "income",
            ],

            "avoid_table_keywords": [
                "payment",
                "activity",
                "log",
            ],

            "avoid_column_keywords": [
                "status",
                "type",
                "category",
                "id",
            ],
        },

        "quantity": {
            "meaning": "business_quantity",

            "preferred_keywords": [
                "quantity",
                "quantities",
                "qty",
                "units",
                "number of items",
                "unit count",
            ],

            "preferred_column_keywords": [
                "quantity",
                "qty",
                "units",
                "unit_count",
                "item_quantity",
                "num_sarees",
                "no_of_sarees",
            ],

            "preferred_table_keywords": [
                "stock",
                "inventory",
                "order",
                "production",
                "sales",
                "material",
            ],

            "avoid_column_keywords": [
                "id",
                "status",
                "type",
                "category",
            ],
        },

        "production": {
            "meaning": "production_output",

            "preferred_keywords": [
                "production",
                "produced",
                "manufactured",
                "manufacturing",
                "output",
                "production output",
            ],

            "preferred_column_keywords": [
                "quantity",
                "num_sarees",
                "no_of_sarees",
                "production",
                "output",
            ],

            "preferred_table_keywords": [
                "production",
                "saree",
                "warp",
                "weft",
            ],

            "avoid_table_keywords": [
                "payment",
                "activity",
                "log",
            ],

            "avoid_column_keywords": [
                "id",
                "status",
                "type",
                "category",
            ],
        },

        "profit": {
            "meaning": "business_profit",

            "preferred_keywords": [
                "profit",
                "profits",
                "gain",
                "profit amount",
                "profit value",
            ],

            "preferred_column_keywords": [
                "profit",
                "profit_amount",
                "profit_value",
                "gain",
            ],

            "preferred_table_keywords": [
                "profit",
                "sales",
                "revenue",
            ],

            "avoid_column_keywords": [
                "id",
                "status",
                "type",
                "category",
            ],
        },

        "loss": {
            "meaning": "business_loss",

            "preferred_keywords": [
                "loss",
                "losses",
                "loss amount",
                "loss value",
            ],

            "preferred_column_keywords": [
                "loss",
                "loss_amount",
                "loss_value",
            ],

            "preferred_table_keywords": [
                "loss",
                "sales",
                "revenue",
            ],

            "avoid_column_keywords": [
                "id",
                "status",
                "type",
                "category",
            ],
        },
    }

    def understand(
        self,
        question: str,
        business_language_result: dict,
    ) -> dict:

        original_question = (
            question.strip()
            if question
            else ""
        )

        normalized_question = self._normalize(
            original_question
        )

        concepts = [
            item["concept"]
            for item in business_language_result.get(
                "business_terms",
                [],
            )
        ]

        contexts = []

        for concept in concepts:

            context = self._resolve_concept(
                concept=concept,
                question=normalized_question,
            )

            contexts.append(context)

        return {
            "question": original_question,
            "normalized_question": normalized_question,
            "contexts": contexts,
        }

    def _resolve_concept(
        self,
        concept: str,
        question: str,
    ) -> dict:

        rule = self.CONTEXT_RULES.get(
            concept
        )

        if not rule:

            return {
                "concept": concept,
                "meaning": concept,
                "confidence": 0.50,
                "preferred_keywords": [],
                "matched_context": [],
                "preferred_column_keywords": [],
                "preferred_table_keywords": [],
                "avoid_table_keywords": [],
                "avoid_column_keywords": [],
            }

        matched_context = []

        for keyword in rule.get(
            "preferred_keywords",
            [],
        ):

            if self._contains_phrase(
                question,
                keyword,
            ):

                matched_context.append(
                    keyword
                )

        if matched_context:

            confidence = min(
                0.98,
                0.80
                + (
                    len(matched_context)
                    * 0.05
                ),
            )

        else:

            confidence = 0.75

        return {
            "concept": concept,
            "meaning": rule["meaning"],
            "confidence": confidence,
            "preferred_keywords": rule.get(
                "preferred_keywords",
                [],
            ),
            "matched_context": matched_context,
            "preferred_column_keywords": rule.get(
                "preferred_column_keywords",
                [],
            ),
            "preferred_table_keywords": rule.get(
                "preferred_table_keywords",
                [],
            ),
            "avoid_table_keywords": rule.get(
                "avoid_table_keywords",
                [],
            ),
            "avoid_column_keywords": rule.get(
                "avoid_column_keywords",
                [],
            ),
        }

    @staticmethod
    def _contains_phrase(
        question: str,
        phrase: str,
    ) -> bool:

        normalized_phrase = re.sub(
            r"[^\w\s]",
            " ",
            phrase.lower(),
        )

        normalized_phrase = re.sub(
            r"\s+",
            " ",
            normalized_phrase,
        ).strip()

        pattern = (
            r"\b"
            + re.escape(normalized_phrase)
            + r"\b"
        )

        return bool(
            re.search(
                pattern,
                question,
            )
        )

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


business_context_engine = BusinessContextEngine()