
from decimal import Decimal
from datetime import date, datetime
import math


class ResponseEngine:

    def generate(
        self,
        question: str,
        intent_result: dict,
        entity_result: dict,
        metric_result: dict,
        query_result: dict,
        execution_result: dict,
    ) -> dict:

        if not execution_result.get("success"):
            return {
                "success": False,
                "answer": execution_result.get(
                    "reason",
                    "I could not retrieve the requested information.",
                ),
                "rows": [],
                "columns": [],
            }

        rows = execution_result.get("rows", [])
        columns = execution_result.get("columns", [])

        intent = intent_result.get(
            "intent",
            "UNKNOWN",
        )

        entities = [
            entity["type"]
            for entity in entity_result.get(
                "entities",
                [],
            )
        ]

        metric = metric_result.get("metric")

        if not rows:
            return {
                "success": True,
                "answer": self._no_results_answer(
                    entities,
                    intent,
                ),
                "rows": [],
                "columns": columns,
            }

        answer = self._build_answer(
            question=question,
            intent=intent,
            entities=entities,
            metric=metric,
            rows=rows,
            columns=columns,
            query_result=query_result,
        )

        return {
            "success": True,
            "answer": answer,
            "rows": rows,
            "columns": columns,
        }

    # =============================================================
    # MAIN ANSWER BUILDER
    # =============================================================

    def _build_answer(
        self,
        question: str,
        intent: str,
        entities: list[str],
        metric: str | None,
        rows: list[dict],
        columns: list[str],
        query_result: dict,
    ) -> str:

        if intent == "COUNT":
            return self._count_answer(
                entities,
                rows,
            )

        if intent == "TOTAL":
            return self._aggregate_answer(
                "total",
                entities,
                metric,
                rows,
            )

        if intent == "AVERAGE":
            return self._aggregate_answer(
                "average",
                entities,
                metric,
                rows,
            )

        if intent == "MAXIMUM":
            return self._maximum_minimum_answer(
                operation="highest",
                entities=entities,
                metric=metric,
                rows=rows,
                question=question,
            )

        if intent == "MINIMUM":
            return self._maximum_minimum_answer(
                operation="lowest",
                entities=entities,
                metric=metric,
                rows=rows,
                question=question,
            )

        if intent in (
            "TOP",
            "BOTTOM",
        ):
            return self._ranking_answer(
                intent=intent,
                entities=entities,
                metric=metric,
                rows=rows,
            )

        if intent in (
            "LIST",
            "GROUP_BY",
            "FILTER",
        ):
            return self._list_answer(
                entities=entities,
                metric=metric,
                rows=rows,
                columns=columns,
            )

        return self._generic_answer(
            rows=rows,
            columns=columns,
        )

    # =============================================================
    # COUNT
    # =============================================================

    def _count_answer(
        self,
        entities: list[str],
        rows: list[dict],
    ) -> str:

        if not rows:
            return "I found no matching records."

        row = rows[0]

        quantity_columns = [
            "total_num_sarees",
            "total_quantity",
        ]

        for column in quantity_columns:

            if column not in row:
                continue

            value = row[column]

            if value is None:

                if column == "total_num_sarees":
                    return (
                        "No saree production quantity "
                        "is available in the database."
                    )

                return (
                    "No quantity data is available "
                    "in the database."
                )

            if not ResponseValue.is_numeric(value):
                continue

            if column == "total_num_sarees":
                return (
                    f"A total of "
                    f"{self._format_number(value)} "
                    f"sarees were produced."
                )

            return (
                f"The total quantity is "
                f"{self._format_number(value)}."
            )

        value = self._first_numeric_value(row)

        if value is None:
            return (
                f"I found {len(rows)} "
                f"matching records."
            )

        entity_name = (
            self._human_entity(entities[0])
            if entities
            else "records"
        )

        if self._numeric_equal(value, 1):
            entity_name = self._singular(
                entity_name
            )

        return (
            f"There are "
            f"{self._format_number(value)} "
            f"{entity_name}."
        )

    # =============================================================
    # AGGREGATE
    # =============================================================

    def _aggregate_answer(
        self,
        operation: str,
        entities: list[str],
        metric: str | None,
        rows: list[dict],
    ) -> str:

        value = self._find_metric_value(
            rows[0],
            metric,
        )

        if value is None:
            value = self._first_numeric_value(
                rows[0]
            )

        if value is None:

            metric_name = self._human_metric(
                metric
            )

            return (
                f"There is no {metric_name} data "
                f"available for the matching records."
            )

        metric_name = self._human_metric(
            metric
        )

        entity_name = (
            self._human_entity(entities[0])
            if entities
            else ""
        )

        formatted_value = (
            self._format_number(value)
        )

        if operation == "total":

            if entity_name:
                return (
                    f"The total {metric_name} "
                    f"for {entity_name} is "
                    f"{formatted_value}."
                )

            return (
                f"The total {metric_name} is "
                f"{formatted_value}."
            )

        if operation == "average":

            if entity_name:
                return (
                    f"The average {metric_name} "
                    f"for {entity_name} is "
                    f"{formatted_value}."
                )

            return (
                f"The average {metric_name} is "
                f"{formatted_value}."
            )

        return (
            f"The result is "
            f"{formatted_value}."
        )

    # =============================================================
    # MAXIMUM / MINIMUM
    # =============================================================

    def _maximum_minimum_answer(
        self,
        operation: str,
        entities: list[str],
        metric: str | None,
        rows: list[dict],
        question: str,
    ) -> str:

        if not rows:
            return "I found no matching records."

        row = rows[0]

        metric_name = self._human_metric(
            metric
        )

        value = self._find_metric_value(
            row,
            metric,
        )

        if value is None:
            value = self._first_numeric_value(
                row
            )

        if value is None:
            return (
                f"I found the {operation} "
                f"{metric_name}, but its value "
                f"could not be determined."
            )

        identity = self._find_identity(
            row
        )

        if identity:

            return (
                f"{identity} has the "
                f"{operation} {metric_name} "
                f"of {self._format_number(value)}."
            )

        return (
            f"The {operation} {metric_name} is "
            f"{self._format_number(value)}."
        )

    # =============================================================
    # TOP / BOTTOM
    # =============================================================

    def _ranking_answer(
        self,
        intent: str,
        entities: list[str],
        metric: str | None,
        rows: list[dict],
    ) -> str:

        entity_name = (
            self._human_entity(entities[0])
            if entities
            else "records"
        )

        metric_name = self._human_metric(
            metric
        )

        direction = (
            "top"
            if intent == "TOP"
            else "bottom"
        )

        lines = [
            f"The {direction} {len(rows)} "
            f"{entity_name} by {metric_name} are:"
        ]

        for index, row in enumerate(
            rows,
            start=1,
        ):

            identity = self._find_identity(
                row
            )

            value = self._find_metric_value(
                row,
                metric,
            )

            if identity is None:
                identity = (
                    f"Record {index}"
                )

            if value is None:

                lines.append(
                    f"{index}. {identity}"
                )

            else:

                lines.append(
                    f"{index}. {identity} — "
                    f"{self._format_number(value)}"
                )

        return "\n".join(lines)

    # =============================================================
    # LIST
    # =============================================================

    def _list_answer(
        self,
        entities: list[str],
        metric: str | None,
        rows: list[dict],
        columns: list[str],
    ) -> str:

        entity_name = (
            self._human_entity(entities[0])
            if entities
            else "records"
        )

        if len(entities) > 1:

            entity_name = self._multi_entity_name(
                entities
            )

        lines = [
            f"I found {len(rows)} "
            f"{entity_name}:"
        ]

        for index, row in enumerate(
            rows[:20],
            start=1,
        ):

            identity = self._find_identity(
                row
            )

            if identity is None:
                identity = self._row_summary(
                    row
                )

            lines.append(
                f"{index}. {identity}"
            )

        if len(rows) > 20:

            lines.append(
                f"... and {len(rows) - 20} more."
            )

        return "\n".join(lines)

    # =============================================================
    # NO RESULTS
    # =============================================================

    def _no_results_answer(
        self,
        entities: list[str],
        intent: str,
    ) -> str:

        if len(entities) >= 2:

            names = [
                self._human_entity(entity)
                for entity in entities
            ]

            return (
                "I could not find matching data "
                f"for the requested "
                f"{' and '.join(names)}."
            )

        if entities:

            entity_name = self._human_entity(
                entities[0]
            )

            return (
                f"I could not find any matching "
                f"{entity_name}."
            )

        return (
            "I could not find any matching data."
        )

    # =============================================================
    # GENERIC
    # =============================================================

    def _generic_answer(
        self,
        rows: list[dict],
        columns: list[str],
    ) -> str:

        return (
            f"I found {len(rows)} matching records."
        )

    # =============================================================
    # IDENTITY
    # =============================================================

    @staticmethod
    def _find_identity(
        row: dict,
    ):

        preferred_columns = [
            "weavername",
            "weaver_name",
            "employee_name",
            "customer_name",
            "product_name",
            "saree_name",
            "saree_number",
            "loom_no",
            "loom_number",
            "name",
            "username",
            "task_name",
            "item_name",
        ]

        for column in preferred_columns:

            if column in row:

                value = row[column]

                if value is not None:
                    return str(value)

        first = row.get(
            "firstname"
        )

        last = row.get(
            "lastname"
        )

        if first or last:

            return " ".join(
                str(value)
                for value in (
                    first,
                    last,
                )
                if value
            )

        return None

    # =============================================================
    # METRIC VALUE
    # =============================================================

    @staticmethod
    def _find_metric_value(
        row: dict,
        metric: str | None,
    ):

        if not metric:
            return None

        metric_columns = {

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
                "credit_amount",
                "credited_amount",
            ],

            "total_debit": [
                "total_debit",
                "amount_debit",
                "debit",
                "debit_amount",
                "debited_amount",
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
            ],

            "salary": [
                "salary",
                "wage",
                "wages",
                "pay",
                "compensation",
            ],

            "amount": [
                "amount",
                "total_amount",
            ],

            "num_sarees": [
                "num_sarees",
                "no_of_sarees",
                "saree_count",
                "sarees_count",
                "production_quantity",
            ],

            "revenue": [
                "revenue",
                "total_revenue",
                "amount",
            ],
        }

        possible_columns = metric_columns.get(
            metric,
            [metric],
        )

        for column in possible_columns:

            if column not in row:
                continue

            value = row[column]

            if ResponseValue.is_numeric(
                value
            ):
                return value

        return None

    # =============================================================
    # FIRST NUMERIC VALUE
    # =============================================================

    def _first_numeric_value(
        self,
        row: dict,
    ):
        """
        Return the first meaningful numeric value.

        Identity columns such as id, *_id, and similar
        identifiers must not be treated as business metrics.
        """

        ignored_columns = {
            "id",
            "user_id",
            "weaver_id",
            "loom_id",
            "saree_id",
            "employee_id",
            "product_id",
            "customer_id",
            "production_warp_id",
            "material_id",
        }

        for column, value in row.items():

            column_name = str(
                column
            ).lower()

            if column_name in ignored_columns:
                continue

            if column_name.endswith("_id"):
                continue

            if not ResponseValue.is_numeric(
                value
            ):
                continue

            return value

        return None

    # =============================================================
    # ROW SUMMARY
    # =============================================================

    @staticmethod
    def _row_summary(
        row: dict,
    ) -> str:

        parts = []

        for key, value in row.items():

            if value is None:
                continue

            value = ResponseValue.format_value(
                value
            )

            parts.append(
                f"{key}: {value}"
            )

            if len(parts) >= 3:
                break

        return ", ".join(parts)

    # =============================================================
    # ENTITY NAME
    # =============================================================

    @staticmethod
    def _human_entity(
        entity: str,
    ) -> str:

        names = {
            "weaver": "weavers",
            "loom": "looms",
            "warp": "warps",
            "weft": "wefts",
            "saree": "sarees",
            "material": "materials",
            "stock": "stock records",
            "silk": "silk records",
            "gold": "gold records",
            "silver": "silver records",
            "zari": "zari records",
            "customer": "customers",
            "product": "products",
            "sales": "sales records",
            "order": "orders",
            "invoice": "invoices",
            "payment": "payments",
            "employee": "employees",
            "department": "departments",
            "user": "users",
            "operation": "operations",
            "activity": "activities",
        }

        return names.get(
            entity,
            f"{entity} records",
        )

    @classmethod
    def _multi_entity_name(
        cls,
        entities: list[str],
    ) -> str:

        names = [
            cls._human_entity(entity)
            for entity in entities
        ]

        return " and ".join(names)

    # =============================================================
    # METRIC NAME
    # =============================================================

    @staticmethod
    def _human_metric(
        metric: str | None,
    ) -> str:

        names = {

            "total_balance": "balance",

            "total_credit": "credit",

            "total_debit": "debit",

            "advance_amount": "advance amount",

            "quantity": "quantity",

            "price": "price",

            "salary": "salary",

            "revenue": "revenue",

            "amount": "amount",

            "num_sarees": "number of sarees",
        }

        return names.get(
            metric,
            metric.replace(
                "_",
                " ",
            )
            if metric
            else "value",
        )

    # =============================================================
    # NUMBER FORMATTING
    # =============================================================

    @staticmethod
    def _format_number(
        value,
    ) -> str:

        if value is None:
            return "0"

        if isinstance(
            value,
            Decimal,
        ):
            value = float(value)

        if isinstance(
            value,
            bool,
        ):
            return str(value)

        if isinstance(
            value,
            (int, float),
        ):

            if isinstance(
                value,
                float,
            ) and math.isnan(value):

                return "0"

            if float(value).is_integer():
                return f"{int(value):,}"

            return f"{value:,.2f}"

        return str(value)

    # =============================================================
    # NUMERIC COMPARISON
    # =============================================================

    @staticmethod
    def _numeric_equal(
        value,
        target,
    ) -> bool:

        try:

            return float(value) == float(
                target
            )

        except (
            TypeError,
            ValueError,
        ):
            return False

    # =============================================================
    # SINGULAR
    # =============================================================

    @staticmethod
    def _singular(
        value: str,
    ) -> str:

        if value.endswith("ies"):
            return value[:-3] + "y"

        if value.endswith("s"):
            return value[:-1]

        return value


class ResponseValue:

    @staticmethod
    def is_numeric(
        value,
    ) -> bool:

        if isinstance(
            value,
            bool,
        ):
            return False

        return isinstance(
            value,
            (
                int,
                float,
                Decimal,
            )
        )

    @staticmethod
    def format_value(
        value,
    ) -> str:

        if isinstance(
            value,
            (date, datetime),
        ):
            return value.isoformat()

        if isinstance(
            value,
            Decimal,
        ):
            return str(value)

        return str(value)


response_engine = ResponseEngine()

