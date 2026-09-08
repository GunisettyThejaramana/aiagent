from sqlalchemy import inspect


class RelationshipEngine:

    def discover_relationships(self, engine) -> dict:
        """
        Discover relationships using:
        1. Explicit database foreign keys
        2. Column-name conventions
        """

        inspector = inspect(engine)

        tables = inspector.get_table_names()

        relationships = []

        # --------------------------------------------------
        # 1. EXPLICIT FOREIGN KEY RELATIONSHIPS
        # --------------------------------------------------

        for table_name in tables:

            foreign_keys = inspector.get_foreign_keys(
                table_name
            )

            for foreign_key in foreign_keys:

                referred_table = foreign_key.get(
                    "referred_table"
                )

                constrained_columns = foreign_key.get(
                    "constrained_columns",
                    []
                )

                referred_columns = foreign_key.get(
                    "referred_columns",
                    []
                )

                if not referred_table:
                    continue

                relationships.append(
                    {
                        "from_table": table_name,
                        "from_columns": constrained_columns,
                        "to_table": referred_table,
                        "to_columns": referred_columns,
                        "type": "foreign_key",
                        "confidence": 1.0,
                    }
                )

        # --------------------------------------------------
        # 2. INFER RELATIONSHIPS FROM COLUMN NAMES
        # --------------------------------------------------

        schema_columns = {}

        for table_name in tables:

            columns = inspector.get_columns(
                table_name
            )

            schema_columns[table_name] = [
                str(column["name"])
                for column in columns
            ]

        existing_relationships = {
            (
                item["from_table"],
                tuple(item["from_columns"]),
                item["to_table"],
                tuple(item["to_columns"]),
            )
            for item in relationships
        }

        for source_table in tables:

            source_columns = schema_columns[
                source_table
            ]

            for source_column in source_columns:

                column_lower = source_column.lower()

                # We only infer columns ending in "_id"
                if not column_lower.endswith("_id"):
                    continue

                entity_name = column_lower[:-3]

                possible_target_tables = [
                    entity_name,
                    entity_name + "s",
                ]

                for target_table in tables:

                    if target_table.lower() not in [
                        name.lower()
                        for name in possible_target_tables
                    ]:
                        continue

                    target_columns = schema_columns[
                        target_table
                    ]

                    target_id_column = None

                    for target_column in target_columns:

                        if target_column.lower() == "id":
                            target_id_column = target_column
                            break

                    if not target_id_column:
                        continue

                    relationship_key = (
                        source_table,
                        (source_column,),
                        target_table,
                        (target_id_column,),
                    )

                    if relationship_key in existing_relationships:
                        continue

                    relationships.append(
                        {
                            "from_table": source_table,
                            "from_columns": [
                                source_column
                            ],
                            "to_table": target_table,
                            "to_columns": [
                                target_id_column
                            ],
                            "type": "inferred",
                            "confidence": 0.85,
                        }
                    )

                    existing_relationships.add(
                        relationship_key
                    )

        return {
            "relationship_count": len(
                relationships
            ),
            "relationships": relationships,
        }

    # ------------------------------------------------------
    # FIND PATH BETWEEN TWO TABLES
    # ------------------------------------------------------

    def find_relationship_path(
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

            source = relationship[
                "from_table"
            ]

            target = relationship[
                "to_table"
            ]

            graph.setdefault(
                source,
                []
            ).append(target)

            graph.setdefault(
                target,
                []
            ).append(source)

        if start_table not in graph:
            return []

        queue = [
            (
                start_table,
                [start_table]
            )
        ]

        visited = {
            start_table
        }

        while queue:

            current_table, path = queue.pop(0)

            for next_table in graph.get(
                current_table,
                []
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
                        new_path
                    )
                )

        return []

    # ------------------------------------------------------
    # GET DIRECTLY RELATED TABLES
    # ------------------------------------------------------

    def get_related_tables(
        self,
        relationships: dict,
        table_name: str,
    ) -> list[str]:

        related_tables = []

        for relationship in relationships.get(
            "relationships",
            []
        ):

            if relationship[
                "from_table"
            ] == table_name:

                related_tables.append(
                    relationship[
                        "to_table"
                    ]
                )

            elif relationship[
                "to_table"
            ] == table_name:

                related_tables.append(
                    relationship[
                        "from_table"
                    ]
                )

        return list(
            dict.fromkeys(
                related_tables
            )
        )


relationship_engine = RelationshipEngine()