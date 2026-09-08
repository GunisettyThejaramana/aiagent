import re


class IntentEngine:
    """
    Custom rule-based intent understanding engine.

    This is the first version of our own AI reasoning system.
    It does not use OpenAI, Ollama, LangChain, or another LLM.
    """

    INTENTS = {
        "TOTAL",
        "COUNT",
        "AVERAGE",
        "MAXIMUM",
        "MINIMUM",
        "TOP",
        "BOTTOM",
        "GROUP_BY",
        "FILTER",
        "LIST",
        "UNKNOWN",
    }

    def understand(self, question: str) -> dict:
        if not question or not question.strip():
            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "matched_terms": [],
            }

        original_question = question.strip()
        q = original_question.lower()

        # Normalize common punctuation.
        normalized = re.sub(r"[^\w\s]", " ", q)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # ---------------------------------------------------------
        # TOTAL
        # ---------------------------------------------------------
        total_terms = [
            "total",
            "overall",
            "sum",
            "combined",
            "how much",
            "total amount",
            "total sales",
            "overall sales",
        ]

        matched = self._find_terms(normalized, total_terms)

        if matched:
            return self._result(
                "TOTAL",
                0.95,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # COUNT
        # ---------------------------------------------------------
        count_terms = [
            "how many",
            "count",
            "number of",
            "how much records",
            "how many records",
            "number",
        ]

        matched = self._find_terms(normalized, count_terms)

        if matched:
            return self._result(
                "COUNT",
                0.95,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # AVERAGE
        # ---------------------------------------------------------
        average_terms = [
            "average",
            "avg",
            "mean",
        ]

        matched = self._find_terms(normalized, average_terms)

        if matched:
            return self._result(
                "AVERAGE",
                0.95,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # MAXIMUM
        # ---------------------------------------------------------
        maximum_terms = [
            "highest",
            "maximum",
            "max",
            "largest",
            "greatest",
            "most",
        ]

        matched = self._find_terms(normalized, maximum_terms)

        if matched:
            return self._result(
                "MAXIMUM",
                0.90,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # MINIMUM
        # ---------------------------------------------------------
        minimum_terms = [
            "lowest",
            "minimum",
            "min",
            "smallest",
            "least",
        ]

        matched = self._find_terms(normalized, minimum_terms)

        if matched:
            return self._result(
                "MINIMUM",
                0.90,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # TOP
        # ---------------------------------------------------------
        top_terms = [
            "top",
            "best",
            "leading",
            "highest selling",
            "most selling",
            "most sold",
        ]

        matched = self._find_terms(normalized, top_terms)

        if matched:
            return self._result(
                "TOP",
                0.90,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # BOTTOM
        # ---------------------------------------------------------
        bottom_terms = [
            "bottom",
            "worst",
            "lowest selling",
            "least selling",
            "least sold",
        ]

        matched = self._find_terms(normalized, bottom_terms)

        if matched:
            return self._result(
                "BOTTOM",
                0.90,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # GROUP BY
        # ---------------------------------------------------------
        group_terms = [
            "by product",
            "by customer",
            "by month",
            "by year",
            "by date",
            "by category",
            "group by",
            "grouped by",
            "breakdown",
            "break down",
        ]

        matched = self._find_terms(normalized, group_terms)

        if matched:
            return self._result(
                "GROUP_BY",
                0.90,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # FILTER
        # ---------------------------------------------------------
        filter_terms = [
            "where",
            "for customer",
            "for product",
            "from customer",
            "with customer",
            "with product",
            "only",
            "between",
            "during",
        ]

        matched = self._find_terms(normalized, filter_terms)

        if matched:
            return self._result(
                "FILTER",
                0.85,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # LIST
        # ---------------------------------------------------------
        list_terms = [
            "show",
            "list",
            "display",
            "give me",
            "get",
            "fetch",
            "view",
        ]

        matched = self._find_terms(normalized, list_terms)

        if matched:
            return self._result(
                "LIST",
                0.75,
                matched,
                original_question,
            )

        # ---------------------------------------------------------
        # UNKNOWN
        # ---------------------------------------------------------
        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "matched_terms": [],
            "question": original_question,
        }

    @staticmethod
    def _find_terms(question: str, terms: list[str]) -> list[str]:
        matched = []

        for term in terms:
            if term in question:
                matched.append(term)

        return matched

    @staticmethod
    def _result(
        intent: str,
        confidence: float,
        matched_terms: list[str],
        question: str,
    ) -> dict:
        return {
            "intent": intent,
            "confidence": confidence,
            "matched_terms": matched_terms,
            "question": question,
        }


intent_engine = IntentEngine()