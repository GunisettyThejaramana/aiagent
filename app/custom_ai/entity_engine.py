
from __future__ import annotations

import re
from datetime import date, datetime, timedelta


class EntityEngine:
    """
    Extract business entities, limits and calendar ranges.

    Important:
    This engine does NOT assume that the database uses the same
    names as the user.

    Example:

        User:
            What were the total sales in August 2026?

        Extracted:
            entity = sales
            date_range = 2026-08-01 -> 2026-09-01

    The actual database table/column names are resolved later
    from the database schema.
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
            "sku",
        ],

        "sales": [
            "sale",
            "sales",
            "revenue",
            "turnover",
            "income",
            "receipts",
            "collections",
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
            "collection",
            "collections",
        ],

        # -----------------------------------------------------
        # PEOPLE / ORGANIZATION
        # -----------------------------------------------------

        "employee": [
            "employee",
            "employees",
            "staff",
            "personnel",
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
            "log",
            "logs",
        ],
    }

    MONTHS = {
        "january": 1,
        "jan": 1,
        "february": 2,
        "feb": 2,
        "march": 3,
        "mar": 3,
        "april": 4,
        "apr": 4,
        "may": 5,
        "june": 6,
        "jun": 6,
        "july": 7,
        "jul": 7,
        "august": 8,
        "aug": 8,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "october": 10,
        "oct": 10,
        "november": 11,
        "nov": 11,
        "december": 12,
        "dec": 12,
    }

    # =============================================================
    # MAIN
    # =============================================================

    def extract(
        self,
        question: str,
    ) -> dict:

        if not question or not question.strip():

            return {
                "entities": [],
                "numbers": [],
                "limit": None,
                "dates": [],
                "date_range": None,
                "question": question,
            }

        original = question.strip()

        normalized = re.sub(
            r"[^\w\s/-]",
            " ",
            original.lower(),
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        ).strip()

        return {
            "entities": self._extract_entities(
                normalized
            ),

            "numbers": self._extract_numbers(
                normalized
            ),

            "limit": self._extract_limit(
                normalized
            ),

            "dates": self._extract_dates(
                normalized
            ),

            "date_range": self._extract_date_range(
                normalized
            ),

            "question": original,
        }

    # =============================================================
    # ENTITIES
    # =============================================================

    def _extract_entities(
        self,
        question: str,
    ) -> list[dict]:

        found = []

        for entity_name, terms in self.ENTITY_TERMS.items():

            matched = []

            for term in terms:

                pattern = rf"\b{re.escape(term)}\b"

                if re.search(
                    pattern,
                    question,
                ):

                    matched.append(term)

            if matched:

                found.append(
                    {
                        "type": entity_name,
                        "matched_terms": matched,
                    }
                )

        return found

    # =============================================================
    # NUMBERS
    # =============================================================

    @staticmethod
    def _extract_numbers(
        question: str,
    ) -> list[int]:

        return [
            int(value)
            for value in re.findall(
                r"\b\d+\b",
                question,
            )
        ]

    # =============================================================
    # LIMIT
    # =============================================================

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

    # =============================================================
    # EXPLICIT DATES
    # =============================================================

    @staticmethod
    def _extract_dates(
        question: str,
    ) -> list[str]:

        patterns = [

            r"\b\d{4}-\d{1,2}-\d{1,2}\b",

            r"\b\d{1,2}/\d{1,2}/\d{4}\b",

            r"\b\d{1,2}-\d{1,2}-\d{4}\b",
        ]

        values = []

        for pattern in patterns:

            values.extend(
                re.findall(
                    pattern,
                    question,
                )
            )

        return values

    # =============================================================
    # DATE RANGE
    # =============================================================

    def _extract_date_range(
        self,
        question: str,
    ) -> dict | None:

        today = date.today()

        explicit_dates = self._extract_dates(
            question
        )

        # ---------------------------------------------------------
        # Two explicit dates
        # ---------------------------------------------------------

        if len(explicit_dates) >= 2:

            parsed = [
                self._parse_date(value)
                for value in explicit_dates[:2]
            ]

            if all(parsed):

                start = parsed[0]
                end = parsed[1]

                if end < start:
                    start, end = end, start

                return self._range(
                    start,
                    end + timedelta(days=1),
                    "explicit date range",
                )

        # ---------------------------------------------------------
        # One explicit date
        # ---------------------------------------------------------

        if len(explicit_dates) == 1:

            parsed = self._parse_date(
                explicit_dates[0]
            )

            if parsed:

                return self._range(
                    parsed,
                    parsed + timedelta(days=1),
                    "explicit date",
                )

        # ---------------------------------------------------------
        # Month + year
        #
        # August 2026
        # September 2025
        # ---------------------------------------------------------

        month_pattern = (
            r"\b("
            + "|".join(self.MONTHS)
            + r")\s+(\d{4})\b"
        )

        match = re.search(
            month_pattern,
            question,
        )

        if match:

            month = self.MONTHS[
                match.group(1)
            ]

            year = int(
                match.group(2)
            )

            start = date(
                year,
                month,
                1,
            )

            if month == 12:

                end = date(
                    year + 1,
                    1,
                    1,
                )

            else:

                end = date(
                    year,
                    month + 1,
                    1,
                )

            return self._range(
                start,
                end,
                f"{match.group(1)} {year}",
            )

        # ---------------------------------------------------------
        # Numeric month/year
        #
        # 08/2026
        # ---------------------------------------------------------

        match = re.search(
            r"\b(\d{1,2})/(\d{4})\b",
            question,
        )

        if match:

            month = int(
                match.group(1)
            )

            year = int(
                match.group(2)
            )

            if 1 <= month <= 12:

                start = date(
                    year,
                    month,
                    1,
                )

                if month == 12:

                    end = date(
                        year + 1,
                        1,
                        1,
                    )

                else:

                    end = date(
                        year,
                        month + 1,
                        1,
                    )

                return self._range(
                    start,
                    end,
                    f"{month:02d}/{year}",
                )

        # ---------------------------------------------------------
        # TODAY
        # ---------------------------------------------------------

        if re.search(
            r"\b(today|todays|today's)\b",
            question,
        ):

            return self._range(
                today,
                today + timedelta(days=1),
                "today",
            )

        # ---------------------------------------------------------
        # YESTERDAY
        # ---------------------------------------------------------

        if re.search(
            r"\byesterday\b",
            question,
        ):

            start = today - timedelta(
                days=1
            )

            return self._range(
                start,
                today,
                "yesterday",
            )

        # ---------------------------------------------------------
        # THIS MONTH
        # ---------------------------------------------------------

        if re.search(
            r"\bthis month\b",
            question,
        ):

            start = today.replace(
                day=1
            )

            if today.month == 12:

                end = date(
                    today.year + 1,
                    1,
                    1,
                )

            else:

                end = date(
                    today.year,
                    today.month + 1,
                    1,
                )

            return self._range(
                start,
                end,
                "this month",
            )

        # ---------------------------------------------------------
        # LAST MONTH
        # ---------------------------------------------------------

        if re.search(
            r"\blast month\b",
            question,
        ):

            end = today.replace(
                day=1
            )

            if end.month == 1:

                start = date(
                    end.year - 1,
                    12,
                    1,
                )

            else:

                start = date(
                    end.year,
                    end.month - 1,
                    1,
                )

            return self._range(
                start,
                end,
                "last month",
            )

        # ---------------------------------------------------------
        # THIS YEAR
        # ---------------------------------------------------------

        if re.search(
            r"\bthis year\b",
            question,
        ):

            return self._range(
                date(
                    today.year,
                    1,
                    1,
                ),
                date(
                    today.year + 1,
                    1,
                    1,
                ),
                "this year",
            )

        # ---------------------------------------------------------
        # LAST YEAR
        # ---------------------------------------------------------

        if re.search(
            r"\blast year\b",
            question,
        ):

            return self._range(
                date(
                    today.year - 1,
                    1,
                    1,
                ),
                date(
                    today.year,
                    1,
                    1,
                ),
                "last year",
            )

        # ---------------------------------------------------------
        # Month range
        #
        # January 2026 to March 2026
        # ---------------------------------------------------------

        month_matches = list(
            re.finditer(
                r"\b("
                + "|".join(self.MONTHS)
                + r")\s+(\d{4})\b",
                question,
            )
        )

        if len(month_matches) >= 2:

            first = month_matches[0]
            second = month_matches[1]

            m1 = self.MONTHS[
                first.group(1)
            ]

            y1 = int(
                first.group(2)
            )

            m2 = self.MONTHS[
                second.group(1)
            ]

            y2 = int(
                second.group(2)
            )

            start = date(
                y1,
                m1,
                1,
            )

            if m2 == 12:

                end = date(
                    y2 + 1,
                    1,
                    1,
                )

            else:

                end = date(
                    y2,
                    m2 + 1,
                    1,
                )

            if end > start:

                return self._range(
                    start,
                    end,
                    "month range",
                )

        return None

    # =============================================================
    # DATE PARSER
    # =============================================================

    @staticmethod
    def _parse_date(
        value: str,
    ) -> date | None:

        for fmt in (
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):

            try:

                return datetime.strptime(
                    value,
                    fmt,
                ).date()

            except ValueError:
                pass

        return None

    # =============================================================
    # RANGE
    # =============================================================

    @staticmethod
    def _range(
        start: date,
        end: date,
        label: str,
    ) -> dict:

        return {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "label": label,
        }


entity_engine = EntityEngine()

