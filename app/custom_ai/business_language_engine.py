import re


class BusinessLanguageEngine:
    """
    Converts natural business language into normalized business concepts.

    This engine does not generate SQL and does not depend on a
    particular database schema.
    """

    SYNONYMS = {

        # People / business entities
        "employee": [
            "employee",
            "employees",
            "staff",
            "staff member",
            "staff members",
            "worker",
            "workers",
            "personnel",
            "team member",
            "team members",
        ],

        "customer": [
            "customer",
            "customers",
            "client",
            "clients",
            "buyer",
            "buyers",
            "consumer",
            "consumers",
        ],

        "supplier": [
            "supplier",
            "suppliers",
            "vendor",
            "vendors",
        ],

        "product": [
            "product",
            "products",
            "item",
            "items",
            "goods",
            "merchandise",
        ],

        # Transactions
        "order": [
            "order",
            "orders",
            "purchase",
            "purchases",
            "sales order",
            "sales orders",
        ],

        "payment": [
            "payment",
            "payments",
            "transaction",
            "transactions",
            "paid",
            "payment made",
            "payments made",
        ],

        "invoice": [
            "invoice",
            "invoices",
            "bill",
            "bills",
            "billing",
        ],

        # Financial concepts
        "revenue": [
            "revenue",
            "turnover",
            "income",
            "earnings",
            "sales value",
            "business income",
        ],

        "sales": [
            "sale",
            "sales",
            "selling",
            "sold",
        ],

        "balance": [
            "balance",
            "balances",
            "outstanding",
            "outstanding balance",
            "remaining",
            "remaining balance",
            "due",
            "amount due",
            "outstanding amount",
        ],

        "advance": [
            "advance",
            "advances",
            "advance amount",
            "money advanced",
            "money given",
            "amount given",
            "advance payment",
        ],

        "credit": [
            "credit",
            "credits",
            "credited",
            "credit amount",
            "amount credited",
        ],

        "debit": [
            "debit",
            "debits",
            "debited",
            "debit amount",
            "amount debited",
        ],

        "amount": [
            "amount",
            "amounts",
            "value",
            "values",
            "money",
            "monetary value",
        ],

        "price": [
            "price",
            "prices",
            "cost",
            "costs",
            "rate",
            "rates",
            "unit price",
        ],

        "profit": [
            "profit",
            "profits",
            "profit amount",
            "profit value",
            "gain",
            "gains",
        ],

        "loss": [
            "loss",
            "losses",
            "loss amount",
            "loss value",
        ],

        "salary": [
            "salary",
            "salaries",
            "pay",
            "wage",
            "wages",
            "compensation",
            "payroll",
        ],

        # Operational concepts
        "quantity": [
            "quantity",
            "quantities",
            "amount of",
            "number of items",
            "units",
            "unit count",
            "volume",
        ],

        "production": [
            "production",
            "produced",
            "manufactured",
            "manufacturing",
            "output",
            "production output",
        ],

        "stock": [
            "stock",
            "stocks",
            "inventory",
            "inventories",
            "available stock",
            "available inventory",
            "stock level",
            "stock levels",
        ],

        "return": [
            "return",
            "returns",
            "returned",
            "goods returned",
            "items returned",
        ],

        "pending": [
            "pending",
            "pending work",
            "pending orders",
            "waiting",
            "not completed",
            "unfinished",
        ],

        "completed": [
            "completed",
            "complete",
            "finished",
            "done",
            "closed",
        ],

        # Organization
        "department": [
            "department",
            "departments",
            "division",
            "divisions",
            "team",
            "teams",
            "business unit",
            "business units",
        ],

        # Time / dates
        "date": [
            "date",
            "dates",
            "day",
            "days",
        ],

        "month": [
            "month",
            "months",
            "monthly",
        ],

        "year": [
            "year",
            "years",
            "yearly",
            "annual",
            "annually",
        ],
    }

    COMPARISON_TERMS = {

        "highest": [
            "highest",
            "maximum",
            "max",
            "largest",
            "greatest",
            "most",
            "biggest",
            "highest value",
        ],

        "lowest": [
            "lowest",
            "minimum",
            "min",
            "smallest",
            "least",
            "lowest value",
        ],

        "increase": [
            "increase",
            "increased",
            "growth",
            "grew",
            "higher",
            "rise",
            "risen",
            "up",
            "increasing",
        ],

        "decrease": [
            "decrease",
            "decreased",
            "decline",
            "declined",
            "drop",
            "dropped",
            "lower",
            "fall",
            "fallen",
            "down",
            "decreasing",
        ],
    }

    TIME_TERMS = {

        "today": [
            "today",
        ],

        "yesterday": [
            "yesterday",
        ],

        "tomorrow": [
            "tomorrow",
        ],

        "this_week": [
            "this week",
            "current week",
        ],

        "last_week": [
            "last week",
            "previous week",
        ],

        "this_month": [
            "this month",
            "current month",
        ],

        "last_month": [
            "last month",
            "previous month",
        ],

        "next_month": [
            "next month",
        ],

        "this_year": [
            "this year",
            "current year",
        ],

        "last_year": [
            "last year",
            "previous year",
        ],

        "next_year": [
            "next year",
        ],
    }

    def understand(self, question: str) -> dict:

        if not question or not question.strip():
            return {
                "question": question,
                "normalized_question": "",
                "business_terms": [],
                "comparisons": [],
                "time_terms": [],
                "numbers": [],
            }

        original_question = question.strip()

        normalized_question = self._normalize(
            original_question
        )

        business_terms = self._find_business_terms(
            normalized_question
        )

        comparisons = self._find_comparisons(
            normalized_question
        )

        time_terms = self._find_time_terms(
            normalized_question
        )

        numbers = self._extract_numbers(
            normalized_question
        )

        return {
            "question": original_question,
            "normalized_question": normalized_question,
            "business_terms": business_terms,
            "comparisons": comparisons,
            "time_terms": time_terms,
            "numbers": numbers,
        }

    @staticmethod
    def _normalize(question: str) -> str:

        question = question.lower()

        question = re.sub(
            r"[^\w\s]",
            " ",
            question,
        )

        question = re.sub(
            r"\s+",
            " ",
            question,
        )

        return question.strip()

    def _find_business_terms(
        self,
        question: str,
    ) -> list[dict]:

        results = []

        for concept, synonyms in self.SYNONYMS.items():

            matched_terms = []

            for synonym in synonyms:

                pattern = rf"\b{re.escape(synonym)}\b"

                if re.search(pattern, question):
                    matched_terms.append(synonym)

            if matched_terms:

                results.append({
                    "concept": concept,
                    "matched_terms": matched_terms,
                })

        return results

    def _find_comparisons(
        self,
        question: str,
    ) -> list[dict]:

        results = []

        for comparison, terms in self.COMPARISON_TERMS.items():

            matched_terms = []

            for term in terms:

                pattern = rf"\b{re.escape(term)}\b"

                if re.search(pattern, question):
                    matched_terms.append(term)

            if matched_terms:

                results.append({
                    "comparison": comparison,
                    "matched_terms": matched_terms,
                })

        return results

    def _find_time_terms(
        self,
        question: str,
    ) -> list[dict]:

        results = []

        for time_concept, terms in self.TIME_TERMS.items():

            matched_terms = []

            for term in terms:

                pattern = rf"\b{re.escape(term)}\b"

                if re.search(pattern, question):
                    matched_terms.append(term)

            if matched_terms:

                results.append({
                    "time": time_concept,
                    "matched_terms": matched_terms,
                })

        return results

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


business_language_engine = BusinessLanguageEngine()