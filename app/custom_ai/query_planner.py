class QueryPlanner:

    def plan(
        self,
        question: str,
        intent_result: dict,
        entity_result: dict,
        metric_result: dict,
        reasoning_result: dict,
        relationships: dict,
        schema: dict,
    ) -> dict:

        intent = intent_result.get("intent", "UNKNOWN")
        entities = [
            entity["type"]
            for entity in entity_result.get("entities", [])
        ]

        metric = metric_result.get("metric")
        selected_table = reasoning_result.get("selected_table")

        if not selected_table:
            return self._failure(
                "I could not determine which table should answer this question."
            )

        primary_table = selected_table["table_name"]

        # ---------------------------------------------------------
        # 1. Detect derived revenue calculation
        # ---------------------------------------------------------

        if metric == "revenue":

            sales_table = self._find_table(
                schema,
                ["sales"]
            )

            if sales_table:
                column_names = self._column_names(sales_table)

                if (
                    "quantity" in column_names
                    and "price" in column_names
                ):
                    return self._success(
                        plan_type="DERIVED_METRIC",
                        primary_table="sales",
                        tables=["sales"],
                        joins=[],
                        metric="revenue",
                        metric_expression="quantity * price",
                            aggregation=self._aggregation_for_intent(
        intent,
        metric,
    ),
                        limit=entity_result.get("limit"),
                        reason=(
                            "Revenue is derived from sales quantity multiplied "
                            "by sales price."
                        ),
                    )

        # ---------------------------------------------------------
        # 2. Detect multi-table relationship questions
        # ---------------------------------------------------------

        if len(entities) >= 2:

            relationship_plan = self._find_relationship_plan(
                entities=entities,
                primary_table=primary_table,
                relationships=relationships,
                schema=schema,
            )

            if relationship_plan:
                return self._success(
                    plan_type="RELATIONSHIP",
                    primary_table=primary_table,
                    tables=relationship_plan["tables"],
                    joins=relationship_plan["joins"],
                    metric=metric,
                    metric_expression=None,
                    aggregation=self._aggregation_for_intent(
    intent,
    metric,
),
                    limit=entity_result.get("limit"),
                    reason=(
                        "Multiple entities were detected and a relationship "
                        "path was found between their tables."
                    ),
                )

        # ---------------------------------------------------------
        # 3. Normal single-table query
        # ---------------------------------------------------------

        return self._success(
            plan_type="SINGLE_TABLE",
            primary_table=primary_table,
            tables=[primary_table],
            joins=[],
            metric=metric,
            metric_expression=None,
                aggregation=self._aggregation_for_intent(
        intent,
        metric,
    ),
            limit=entity_result.get("limit"),
            reason=(
                "The question can currently be answered using the selected "
                "primary table."
            ),
        )

    # =============================================================
    # Relationship planning
    # =============================================================

    def _find_relationship_plan(
        self,
        entities: list[str],
        primary_table: str,
        relationships: dict,
        schema: dict,
    ) -> dict | None:

        entity_table_candidates = {}

        for entity in entities:
            candidates = self._find_entity_tables(
                entity,
                schema,
            )

            if candidates:
                entity_table_candidates[entity] = candidates

        if len(entity_table_candidates) < 2:
            return None

        target_tables = []

        for entity, candidates in entity_table_candidates.items():

            best_table = candidates[0]

            if best_table != primary_table:
                target_tables.append(best_table)

        if not target_tables:
            return None

        target_table = target_tables[0]

        path = self._find_path(
            relationships,
            primary_table,
            target_table,
        )

        if len(path) < 2:
            return None

        joins = self._build_joins_from_path(
            path,
            relationships,
        )

        if not joins:
            return None

        return {
            "tables": path,
            "joins": joins,
        }

    # =============================================================
    # Find tables for entities
    # =============================================================

    def _find_entity_tables(
        self,
        entity: str,
        schema: dict,
    ) -> list[str]:

        rules = {
            "weaver": [
                "weavers",
            ],
            "loom": [
                "looms",
            ],
            "saree": [
                "saree_entries",
            ],
            "warp": [
                "production_warps",
                "warps",
            ],
            "weft": [
                "wefts",
            ],
            "payment": [
                "payments",
            ],
            "employee": [
                "employees",
            ],
            "sales": [
                "sales",
            ],
            "order": [
                "material_orders",
            ],
            "material": [
                "material_stock",
            ],
            "stock": [
                "material_stock",
                "material_out_stock",
            ],
            "user": [
                "users",
            ],
            "activity": [
                "activities",
            ],
            "operation": [
                "operations",
            ],
        }

        preferred_tables = rules.get(entity, [])

        available_tables = {
            table["table_name"]
            for table in schema.get("tables", [])
        }

        matches = []

        for table_name in preferred_tables:
            if table_name in available_tables:
                matches.append(table_name)

        return matches

    # =============================================================
    # Find relationship path
    # =============================================================

    def _find_path(
        self,
        relationships: dict,
        start_table: str,
        target_table: str,
    ) -> list[str]:

        if start_table == target_table:
            return [start_table]

        graph = {}

        for relationship in relationships.get(
            "relationships",
            []
        ):

            source = relationship["from_table"]
            target = relationship["to_table"]

            graph.setdefault(source, []).append(target)
            graph.setdefault(target, []).append(source)

        queue = [
            (
                start_table,
                [start_table],
            )
        ]

        visited = {
            start_table
        }

        while queue:

            current_table, path = queue.pop(0)

            for next_table in graph.get(
                current_table,
                [],
            ):

                if next_table in visited:
                    continue

                new_path = path + [
                    next_table
                ]

                if next_table == target_table:
                    return new_path

                visited.add(next_table)

                queue.append(
                    (
                        next_table,
                        new_path,
                    )
                )

        return []

    # =============================================================
    # Build JOIN definitions
    # =============================================================

    def _build_joins_from_path(
        self,
        path: list[str],
        relationships: dict,
    ) -> list[dict]:

        joins = []

        for index in range(
            len(path) - 1
        ):

            left_table = path[index]
            right_table = path[index + 1]

            relationship = self._find_relationship(
                relationships,
                left_table,
                right_table,
            )

            if not relationship:
                return []

            joins.append(
                {
                    "left_table": left_table,
                    "left_columns": relationship[
                        "from_columns"
                    ],
                    "right_table": right_table,
                    "right_columns": relationship[
                        "to_columns"
                    ],
                    "type": relationship[
                        "type"
                    ],
                }
            )

        return joins

    # =============================================================
    # Find direct relationship
    # =============================================================

    def _find_relationship(
        self,
        relationships: dict,
        table_a: str,
        table_b: str,
    ) -> dict | None:

        for relationship in relationships.get(
            "relationships",
            [],
        ):

            source = relationship[
                "from_table"
            ]

            target = relationship[
                "to_table"
            ]

            if (
                source == table_a
                and target == table_b
            ):
                return relationship

            if (
                source == table_b
                and target == table_a
            ):
                return {
                    "from_table": target,
                    "from_columns": relationship[
                        "to_columns"
                    ],
                    "to_table": source,
                    "to_columns": relationship[
                        "from_columns"
                    ],
                    "type": relationship[
                        "type"
                    ],
                }

        return None

    # =============================================================
    # Helpers
    # =============================================================

    @staticmethod
    def _find_table(
        schema: dict,
        table_names: list[str],
    ) -> dict | None:

        wanted = {
            name.lower()
            for name in table_names
        }

        for table in schema.get(
            "tables",
            [],
        ):

            if (
                table["table_name"].lower()
                in wanted
            ):
                return table

        return None

    @staticmethod
    def _column_names(
        table: dict,
    ) -> set[str]:

        return {
            column["name"].lower()
            for column in table.get(
                "columns",
                [],
            )
        }

    @staticmethod
    def _aggregation_for_intent(
        intent: str,
        metric: str | None = None,
    ) -> str | None:

        # COUNT normally means counting database records.
        #
        # But some business questions use "how many" to ask
        # for a quantity stored in a column.
        #
        # Example:
        #   "How many sarees were produced?"
        #
        # This should mean:
        #   SUM(num_sarees)
        #
        # rather than:
        #   COUNT(*)

        if intent == "COUNT":

            quantity_metrics = {
                "num_sarees",
                "quantity",
            }

            if metric in quantity_metrics:
                return "SUM"

            return "COUNT"

        aggregations = {
            "TOTAL": "SUM",
            "AVERAGE": "AVG",
            "MAXIMUM": "MAX",
            "MINIMUM": "MIN",
        }

        return aggregations.get(
            intent
        )

    @staticmethod
    def _success(
        plan_type: str,
        primary_table: str,
        tables: list[str],
        joins: list[dict],
        metric: str | None,
        metric_expression: str | None,
        aggregation: str | None,
        limit: int | None,
        reason: str,
    ) -> dict:

        return {
            "success": True,
            "plan_type": plan_type,
            "primary_table": primary_table,
            "tables": tables,
            "joins": joins,
            "metric": metric,
            "metric_expression": metric_expression,
            "aggregation": aggregation,
            "limit": limit,
            "reason": reason,
        }

    @staticmethod
    def _failure(
        reason: str,
    ) -> dict:

        return {
            "success": False,
            "plan_type": None,
            "primary_table": None,
            "tables": [],
            "joins": [],
            "metric": None,
            "metric_expression": None,
            "aggregation": None,
            "limit": None,
            "reason": reason,
        }


query_planner = QueryPlanner()