from sqlalchemy import inspect


class SchemaEngine:
    """
    Reads the selected database schema and creates a searchable
    representation for our custom AI.
    """

    def inspect_database(self, engine) -> dict:
        inspector = inspect(engine)

        tables = inspector.get_table_names()

        schema = {
            "tables": [],
            "table_count": len(tables),
        }

        for table_name in tables:
            columns = inspector.get_columns(table_name)

            table_info = {
                "table_name": table_name,
                "columns": [],
            }

            for column in columns:
                table_info["columns"].append(
                    {
                        "name": str(column["name"]),
                        "type": str(column["type"]),
                        "nullable": column.get("nullable"),
                    }
                )

            schema["tables"].append(table_info)

        return schema

    def find_matching_tables(
        self,
        schema: dict,
        entity_types: list[str],
    ) -> list[dict]:
        """
        Find database tables that appear related to the
        entities identified by our Entity Engine.
        """

        matches = []

        for table in schema.get("tables", []):
            table_name = table["table_name"].lower()

            score = 0
            matched_entities = []

            for entity in entity_types:
                entity_lower = entity.lower()

                # Direct table-name match.
                if entity_lower in table_name:
                    score += 10
                    matched_entities.append(entity)
                    continue

                # Singular/plural matching.
                if entity_lower.endswith("s"):
                    singular = entity_lower[:-1]

                    if singular in table_name:
                        score += 8
                        matched_entities.append(entity)

                else:
                    plural = entity_lower + "s"

                    if plural in table_name:
                        score += 8
                        matched_entities.append(entity)

            if score > 0:
                matches.append(
                    {
                        "table_name": table["table_name"],
                        "score": score,
                        "matched_entities": matched_entities,
                        "columns": table["columns"],
                    }
                )

        matches.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return matches

    def find_matching_columns(
        self,
        table: dict,
        entity_types: list[str],
    ) -> list[dict]:
        """
        Find columns that are likely related to identified entities.
        """

        matches = []

        column_keywords = {
            "customer": [
                "customer",
                "client",
                "buyer",
                "customer_name",
                "customer_id",
                "client_name",
            ],
            "product": [
                "product",
                "item",
                "product_name",
                "product_id",
                "item_name",
            ],
            "sales": [
                "sale",
                "sales",
                "revenue",
                "amount",
                "total",
            ],
            "order": [
                "order",
                "order_id",
            ],
            "employee": [
                "employee",
                "employee_id",
                "employee_name",
                "staff",
            ],
            "department": [
                "department",
                "department_id",
                "department_name",
            ],
            "invoice": [
                "invoice",
                "invoice_id",
                "invoice_number",
            ],
            "payment": [
                "payment",
                "payment_id",
                "transaction",
            ],
        }

        for column in table.get("columns", []):
            column_name = column["name"].lower()

            score = 0
            matched_entities = []

            for entity in entity_types:
                keywords = column_keywords.get(entity, [])

                for keyword in keywords:
                    if keyword in column_name:
                        score += 5
                        matched_entities.append(entity)
                        break

            if score > 0:
                matches.append(
                    {
                        "column_name": column["name"],
                        "type": column["type"],
                        "score": score,
                        "matched_entities": list(
                            dict.fromkeys(matched_entities)
                        ),
                    }
                )

        matches.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return matches


schema_engine = SchemaEngine()