class ReasoningEngine:

    def reason(
        self,
        question,
        intent_result,
        entity_result,
        schema,
        metric_result=None,
        business_context_result=None,
    ):
        """
        Determine which database table should answer the question.

        The reasoning process considers:

        1. Explicit entities
        2. Business context
        3. Requested metric
        4. Matching columns
        5. Master/business tables
        6. Transaction/history penalties
        7. Intent
        """

        intent = intent_result.get(
            "intent",
            "UNKNOWN",
        )

        entity_types = [
            entity["type"]
            for entity in entity_result.get(
                "entities",
                [],
            )
        ]

        limit = entity_result.get(
            "limit"
        )

        metric = None

        if metric_result:
            metric = metric_result.get(
                "metric"
            )

        # ---------------------------------------------------------
        # BUSINESS CONTEXT
        # ---------------------------------------------------------

        contexts = []

        if business_context_result:

            contexts = business_context_result.get(
                "contexts",
                []
            )

        # ---------------------------------------------------------
        # EXTRACT BUSINESS CONCEPTS
        # ---------------------------------------------------------

        business_concepts = []

        for context in contexts:

            concept = context.get(
                "concept"
            )

            meaning = context.get(
                "meaning"
            )

            if concept:
                business_concepts.append(
                    concept.lower()
                )

            if meaning:
                business_concepts.append(
                    meaning.lower()
                )

        # ---------------------------------------------------------
        # TABLE RULES
        # ---------------------------------------------------------

        master_table_rules = {

            "weaver": {
                "preferred_tables": [
                    "weavers",
                ],
                "identifier_columns": [
                    "weavername",
                    "weaver_name",
                ],
            },

            "loom": {
                "preferred_tables": [
                    "looms",
                ],
                "identifier_columns": [
                    "loom_no",
                    "loom_number",
                ],
            },

            "saree": {
                "preferred_tables": [
                    "saree_entries",
                ],
                "identifier_columns": [
                    "saree_number",
                    "saree_name",
                ],
            },

            "customer": {
                "preferred_tables": [
                    "customers",
                ],
                "identifier_columns": [
                    "customer_name",
                    "customer_id",
                ],
            },

            "employee": {
                "preferred_tables": [
                    "employees",
                ],
                "identifier_columns": [
                    "employee_name",
                    "employee_id",
                ],
            },

            "department": {
                "preferred_tables": [
                    "departments",
                ],
                "identifier_columns": [
                    "department_name",
                    "department_id",
                ],
            },

            "product": {
                "preferred_tables": [
                    "products",
                ],
                "identifier_columns": [
                    "product_name",
                    "product_id",
                ],
            },

            "payment": {
                "preferred_tables": [
                    "payments",
                ],
                "identifier_columns": [
                    "payment_id",
                    "amount",
                ],
            },

            "sales": {
                "preferred_tables": [
                    "sales",
                ],
                "identifier_columns": [
                    "customer_name",
                    "product_name",
                ],
            },

            "order": {
                "preferred_tables": [
                    "material_orders",
                ],
                "identifier_columns": [
                    "weaver_name",
                    "item_name",
                ],
            },

            "stock": {
                "preferred_tables": [
                    "material_stock",
                    "silver_material_stock",
                    "color_silk_stock",
                ],
                "identifier_columns": [
                    "name",
                    "category",
                ],
            },
        }

        # ---------------------------------------------------------
        # METRIC → TABLE/COLUMN KNOWLEDGE
        # ---------------------------------------------------------

        metric_rules = {

            "total_balance": {
                "preferred_tables": [
                    "weavers",
                    "looms",
                ],
                "preferred_columns": [
                    "total_balance",
                    "balance",
                    "outstanding_balance",
                    "amount_due",
                    "due_amount",
                ],
            },

            "advance_amount": {
                "preferred_tables": [
                    "weavers",
                ],
                "preferred_columns": [
                    "advance_amount",
                    "advance",
                ],
            },

            "salary": {
                "preferred_tables": [
                    "employees",
                ],
                "preferred_columns": [
                    "salary",
                    "wage",
                    "pay",
                ],
            },

            "total_credit": {
                "preferred_tables": [
                    "weavers",
                    "looms",
                    "saree_entries",
                    "payments",
                ],
                "preferred_columns": [
                    "total_credit",
                    "amount_credit",
                    "credit",
                    "credited_amount",
                ],
            },

            "amount": {
                "preferred_tables": [
                    "payments",
                    "looms",
                    "saree_entries",
                    "sales",
                    "revenue",
                ],
                "preferred_columns": [
                    "amount",
                    "amount_credit",
                    "amount_debit",
                ],
            },

            "quantity": {
                "preferred_tables": [
                    "material_orders",
                    "material_out_stock",
                    "color_silk_item",
                    "silver_company_stock",
                ],
                "preferred_columns": [
                    "quantity",
                    "weight",
                    "no_of_sarees",
                ],
            },

            "num_sarees": {
                "preferred_tables": [
                    "production_warps",
                    "wefts",
                    "weft_colors",
                ],
                "preferred_columns": [
                    "num_sarees",
                    "no_of_sarees",
                ],
            },

            "revenue": {
                "preferred_tables": [
                    "sales",
                    "revenue",
                ],
                "preferred_columns": [
                    "amount",
                    "price",
                    "quantity",
                ],
            },
        }

        metric_rule = metric_rules.get(
            metric,
            {}
        )

        preferred_metric_tables = [
            table.lower()
            for table in metric_rule.get(
                "preferred_tables",
                []
            )
        ]

        preferred_metric_columns = [
            column.lower()
            for column in metric_rule.get(
                "preferred_columns",
                []
            )
        ]

        # ---------------------------------------------------------
        # ENTITY TABLES
        # ---------------------------------------------------------

        entity_preferred_tables = []

        for entity in entity_types:

            rule = master_table_rules.get(
                entity
            )

            if rule:

                for table_name in rule.get(
                    "preferred_tables",
                    []
                ):

                    entity_preferred_tables.append(
                        table_name.lower()
                    )

        # ---------------------------------------------------------
        # SPECIAL BUSINESS CONTEXT RULES
        # ---------------------------------------------------------

        context_table_preferences = []

        context_column_preferences = []

        # Outstanding balance
        if (
            "balance" in business_concepts
            or "outstanding_financial_balance"
            in business_concepts
            or "outstanding" in question.lower()
        ):

            context_table_preferences.extend([
                "weavers",
                "looms",
            ])

            context_column_preferences.extend([
                "total_balance",
                "balance",
                "outstanding_balance",
                "amount_due",
                "due_amount",
            ])

        # Advance
        if (
            "advance" in business_concepts
            or "advance_money_given"
            in business_concepts
        ):

            context_table_preferences.append(
                "weavers"
            )

            context_column_preferences.extend([
                "advance_amount",
                "advance",
            ])

        # Salary
        if (
            "salary" in business_concepts
            or "employee_compensation"
            in business_concepts
        ):

            context_table_preferences.append(
                "employees"
            )

            context_column_preferences.extend([
                "salary",
                "wage",
                "pay",
            ])

        # Credit
        if (
            "credit" in business_concepts
            or "credited_amount"
            in business_concepts
        ):

            context_table_preferences.extend([
                "weavers",
                "looms",
                "saree_entries",
                "payments",
            ])

            context_column_preferences.extend([
                "total_credit",
                "amount_credit",
                "credit",
                "credited_amount",
            ])

        # Debit
        if (
            "debit" in business_concepts
            or "debited_amount"
            in business_concepts
        ):

            context_table_preferences.extend([
                "looms",
                "saree_entries",
                "payments",
            ])

            context_column_preferences.extend([
                "amount_debit",
                "debit",
                "debited_amount",
            ])

        # Production
        if (
            "production" in business_concepts
            or "production_output"
            in business_concepts
        ):

            context_table_preferences.extend([
                "production_warps",
                "saree_entries",
                "wefts",
            ])

            context_column_preferences.extend([
                "num_sarees",
                "no_of_sarees",
            ])

        # Stock / inventory
        if (
            "stock" in business_concepts
            or "current_inventory"
            in business_concepts
        ):

            context_table_preferences.extend([
                "material_stock",
                "silver_material_stock",
                "color_silk_stock",
            ])

            context_column_preferences.extend([
                "quantity",
                "weight",
            ])

        # ---------------------------------------------------------
        # COMBINE PREFERENCES
        # ---------------------------------------------------------

        preferred_tables = set(
            entity_preferred_tables
            + preferred_metric_tables
            + context_table_preferences
        )

        preferred_columns = set(
            preferred_metric_columns
            + context_column_preferences
        )

        # ---------------------------------------------------------
        # CANDIDATE TABLES
        # ---------------------------------------------------------

        tables = schema.get(
            "tables",
            []
        )

        candidates = []

        for table in tables:

            table_name = table[
                "table_name"
            ]

            table_lower = table_name.lower()

            columns = table.get(
                "columns",
                []
            )

            column_names = [
                column["name"].lower()
                for column in columns
            ]

            score = 0

            reasons = []

            # =====================================================
            # 1. ENTITY MATCH
            # =====================================================

            for entity in entity_types:

                entity_lower = entity.lower()

                if table_lower == entity_lower:

                    score += 25

                    reasons.append(
                        f"exact table match for entity '{entity}'"
                    )

                elif table_lower == (
                    entity_lower + "s"
                ):

                    score += 22

                    reasons.append(
                        f"plural table match for entity '{entity}'"
                    )

                elif (
                    entity_lower.endswith("s")
                    and table_lower
                    == entity_lower[:-1]
                ):

                    score += 22

                    reasons.append(
                        f"singular table match for entity '{entity}'"
                    )

                elif entity_lower in table_lower:

                    score += 10

                    reasons.append(
                        f"table name contains entity '{entity}'"
                    )

            # =====================================================
            # 2. PREFERRED ENTITY TABLE
            # =====================================================

            if table_lower in entity_preferred_tables:

                score += 35

                reasons.append(
                    "preferred business table for detected entity"
                )

            # =====================================================
            # 3. METRIC TABLE MATCH
            # =====================================================

            if table_lower in preferred_metric_tables:

                score += 40

                reasons.append(
                    f"preferred table for metric '{metric}'"
                )

            # =====================================================
            # 4. BUSINESS CONTEXT TABLE MATCH
            # =====================================================

            if table_lower in [
                name.lower()
                for name in context_table_preferences
            ]:

                score += 45

                reasons.append(
                    "preferred table for detected business context"
                )

            # =====================================================
            # 5. METRIC COLUMN MATCH
            # =====================================================

            matching_metric_columns = []

            for column in preferred_metric_columns:

                if column in column_names:

                    matching_metric_columns.append(
                        column
                    )

                    score += 35

                    reasons.append(
                        f"contains metric column '{column}'"
                    )

            # =====================================================
            # 6. BUSINESS CONTEXT COLUMN MATCH
            # =====================================================

            for column in context_column_preferences:

                if column.lower() in column_names:

                    score += 40

                    reasons.append(
                        f"contains business-context column '{column}'"
                    )

            # =====================================================
            # 7. MASTER TABLE RULES
            # =====================================================

            for entity in entity_types:

                rule = master_table_rules.get(
                    entity
                )

                if not rule:
                    continue

                if table_lower in [
                    name.lower()
                    for name in rule[
                        "preferred_tables"
                    ]
                ]:

                    score += 30

                    reasons.append(
                        f"preferred master table for entity '{entity}'"
                    )

                for identifier in rule[
                    "identifier_columns"
                ]:

                    if identifier.lower() in column_names:

                        score += 6

                        reasons.append(
                            f"contains entity identifier column '{identifier}'"
                        )

            # =====================================================
            # 8. TRANSACTION/HISTORY PENALTY
            # =====================================================

            transaction_words = [
                "return",
                "returns",
                "order",
                "orders",
                "payment",
                "payments",
                "transaction",
                "transactions",
                "history",
                "log",
                "logs",
                "activity",
                "activities",
                "stock_out",
                "out_stock",
            ]

            for word in transaction_words:

                if word in table_lower:

                    # Do not penalize a specifically preferred
                    # business table.
                    if table_lower not in preferred_tables:

                        score -= 8

                        reasons.append(
                            f"transaction/history table penalty for '{word}'"
                        )

            # =====================================================
            # 9. SYSTEM TABLE PENALTY
            # =====================================================

            system_tables = {
                "users",
                "activities",
                "alembic_version",
            }

            if table_lower in system_tables:

                score -= 35

                reasons.append(
                    "system table penalty"
                )

            # =====================================================
            # 10. SENSITIVE/IDENTIFIER-ONLY TABLE PENALTY
            # =====================================================

            if table_lower == "users":

                score -= 25

                reasons.append(
                    "users table is not a business metric source"
                )

            # =====================================================
            # 11. INTENT REASONING
            # =====================================================

            numeric_columns = [
                column
                for column in columns
                if self._is_numeric_type(
                    column["type"]
                )
            ]

            if intent == "TOTAL":

                if numeric_columns:

                    score += 3

                    reasons.append(
                        "table contains numeric columns suitable for totals"
                    )

            elif intent == "COUNT":

                if "id" in column_names:

                    score += 3

                    reasons.append(
                        "table contains id column suitable for counting"
                    )

            elif intent in (
                "TOP",
                "BOTTOM",
                "MAXIMUM",
                "MINIMUM",
            ):

                if numeric_columns:

                    score += 2

                    reasons.append(
                        "table contains numeric columns suitable for ranking"
                    )

            elif intent == "GROUP_BY":

                if len(column_names) >= 2:

                    score += 1

                    reasons.append(
                        "table contains multiple columns suitable for grouping"
                    )

            # =====================================================
            # 12. LIMIT
            # =====================================================

            if (
                intent in (
                    "TOP",
                    "BOTTOM",
                )
                and limit
                and numeric_columns
            ):

                score += 1

                reasons.append(
                    f"supports ranked result with limit {limit}"
                )

            # =====================================================
            # 13. CANDIDATE
            # =====================================================

            if score > 0:

                candidates.append(
                    {
                        "table_name": table_name,
                        "score": score,
                        "reasons": reasons,
                        "columns": columns,
                    }
                )

        # ---------------------------------------------------------
        # SORT
        # ---------------------------------------------------------

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        selected_table = (
            candidates[0]
            if candidates
            else None
        )

        return {
            "question": question,
            "intent": intent,
            "entities": entity_types,
            "limit": limit,
            "metric": metric,
            "business_concepts": business_concepts,
            "selected_table": selected_table,
            "candidate_tables": candidates,
        }

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

        column_type_upper = str(
            column_type
        ).upper()

        return any(
            numeric_type in column_type_upper
            for numeric_type in numeric_types
        )


reasoning_engine = ReasoningEngine()