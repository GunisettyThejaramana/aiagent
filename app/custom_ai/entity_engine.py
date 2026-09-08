import re


class EntityEngine:
    """
    Custom entity extraction engine.

    This engine identifies business concepts from the user's
    natural-language question.

    No external AI or LLM is used.
    """

    ENTITY_TERMS = {

        # -----------------------------------------------------
        # WEAVING / MANUFACTURING
        # -----------------------------------------------------

        "weaver": [
            "weaver",
            "weavers",
            "worker",
            "workers",
            "handloom worker",
            "handloom workers",
        ],

        "loom": [
            "loom",
            "looms",
            "loom number",
            "loom no",
        ],

        "warp": [
            "warp",
            "warps",
            "production warp",
            "production warps",
        ],

        "weft": [
            "weft",
            "wefts",
        ],

        "saree": [
            "saree",
            "sarees",
            "sari",
            "saris",
        ],

        # -----------------------------------------------------
        # MATERIALS
        # -----------------------------------------------------

        "material": [
            "material",
            "materials",
        ],

        "stock": [
            "stock",
            "stocks",
            "inventory",
            "inventories",
        ],

        "silk": [
            "silk",
            "silks",
        ],

        "gold": [
            "gold",
        ],

        "silver": [
            "silver",
        ],

        "zari": [
            "zari",
        ],

        # -----------------------------------------------------
        # SALES / BUSINESS
        # -----------------------------------------------------

        "customer": [
            "customer",
            "customers",
            "client",
            "clients",
            "buyer",
            "buyers",
        ],

        "product": [
            "product",
            "products",
            "item",
            "items",
        ],

        "sales": [
            "sale",
            "sales",
            "revenue",
            "turnover",
        ],

        "order": [
            "order",
            "orders",
            "purchase",
            "purchases",
        ],

        "invoice": [
            "invoice",
            "invoices",
            "bill",
            "bills",
        ],

        "payment": [
            "payment",
            "payments",
            "transaction",
            "transactions",
        ],

        # -----------------------------------------------------
        # PEOPLE / ORGANIZATION
        # -----------------------------------------------------

        "employee": [
            "employee",
            "employees",
            "staff",
        ],

        "department": [
            "department",
            "departments",
            "division",
            "divisions",
        ],

        "user": [
            "user",
            "users",
            "account",
            "accounts",
        ],

        # -----------------------------------------------------
        # OPERATIONS
        # -----------------------------------------------------

        "operation": [
            "operation",
            "operations",
            "task",
            "tasks",
            "work",
        ],

        "activity": [
            "activity",
            "activities",
            "action",
            "actions",
        ],
    }

    def extract(self, question: str) -> dict:

        if not question or not question.strip():

            return {
                "entities": [],
                "numbers": [],
                "limit": None,
                "dates": [],
                "question": question,
            }

        original_question = question.strip()

        normalized = original_question.lower()

        # Replace punctuation with spaces.
        normalized = re.sub(
            r"[^\w\s]",
            " ",
            normalized,
        )

        # Remove duplicate spaces.
        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        entities = self._extract_entities(normalized)

        numbers = self._extract_numbers(normalized)

        limit = self._extract_limit(normalized)

        dates = self._extract_dates(normalized)

        return {
            "entities": entities,
            "numbers": numbers,
            "limit": limit,
            "dates": dates,
            "question": original_question,
        }

    def _extract_entities(
        self,
        question: str,
    ) -> list[dict]:

        found = []

        for entity_name, terms in self.ENTITY_TERMS.items():

            matched_terms = []

            for term in terms:

                pattern = rf"\b{re.escape(term)}\b"

                if re.search(pattern, question):

                    matched_terms.append(term)

            if matched_terms:

                found.append(
                    {
                        "type": entity_name,
                        "matched_terms": matched_terms,
                    }
                )

        return found

    @staticmethod
    def _extract_numbers(
        question: str,
    ) -> list[int]:

        matches = re.findall(
            r"\b\d+\b",
            question,
        )

        return [
            int(value)
            for value in matches
        ]

    @staticmethod
    def _extract_limit(
        question: str,
    ) -> int | None:

        patterns = [

            r"\btop\s+(\d+)\b",

            r"\bbottom\s+(\d+)\b",

            r"\bfirst\s+(\d+)\b",

            r"\blast\s+(\d+)\b",

            r"\bshow\s+(\d+)\b",

            r"\blist\s+(\d+)\b",

        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                question,
            )

            if match:

                return int(
                    match.group(1)
                )

        return None

    @staticmethod
    def _extract_dates(
        question: str,
    ) -> list[str]:

        date_patterns = [

            r"\b\d{4}-\d{1,2}-\d{1,2}\b",

            r"\b\d{1,2}/\d{1,2}/\d{4}\b",

            r"\b\d{1,2}-\d{1,2}-\d{4}\b",

        ]

        dates = []

        for pattern in date_patterns:

            dates.extend(
                re.findall(
                    pattern,
                    question,
                )
            )

        return dates


entity_engine = EntityEngine()