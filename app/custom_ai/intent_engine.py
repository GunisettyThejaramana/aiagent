
import re


class IntentEngine:
    """
    Determines what operation the user wants.

    Examples:

        total sales
            -> TOTAL

        average salary
            -> AVERAGE

        top 5 customers
            -> TOP

        sales in August 2026
            -> TOTAL

    The final SQL is still generated from the real database schema.
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

    def understand(
        self,
        question: str,
    ) -> dict:

        original = (
            question or ""
        ).strip()

        if not original:

            return {
                "intent": "UNKNOWN",
                "confidence": 0.0,
                "matched_terms": [],
                "question": original,
            }

        q = re.sub(
            r"\s+",
            " ",
            re.sub(
                r"[^\w\s/-]",
                " ",
                original.lower(),
            ),
        ).strip()

        rules = [

            (
                "TOTAL",
                [
                    "total",
                    "overall",
                    "sum",
                    "combined",
                    "how much",
                    "total amount",
                    "total sales",
                    "overall sales",
                    "what were the sales",
                    "what was the sales",
                    "sales in",
                ],
                0.96,
            ),

            (
                "COUNT",
                [
                    "how many",
                    "count",
                    "number of",
                    "how many records",
                    "number",
                ],
                0.95,
            ),

            (
                "AVERAGE",
                [
                    "average",
                    "avg",
                    "mean",
                ],
                0.95,
            ),

            (
                "MAXIMUM",
                [
                    "highest",
                    "maximum",
                    "max",
                    "largest",
                    "greatest",
                    "most",
                ],
                0.90,
            ),

            (
                "MINIMUM",
                [
                    "lowest",
                    "minimum",
                    "min",
                    "smallest",
                    "least",
                ],
                0.90,
            ),

            (
                "TOP",
                [
                    "top",
                    "best",
                    "leading",
                    "highest selling",
                    "most selling",
                    "most sold",
                ],
                0.90,
            ),

            (
                "BOTTOM",
                [
                    "bottom",
                    "worst",
                    "lowest selling",
                    "least selling",
                    "least sold",
                ],
                0.90,
            ),

            (
                "GROUP_BY",
                [
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
                ],
                0.90,
            ),

            (
                "FILTER",
                [
                    "where",
                    "for customer",
                    "for product",
                    "with customer",
                    "with product",
                    "only",
                    "between",
                    "during",
                    "from ",
                    "to ",
                ],
                0.85,
            ),

            (
                "LIST",
                [
                    "show",
                    "list",
                    "display",
                    "give me",
                    "get",
                    "fetch",
                    "view",
                ],
                0.75,
            ),
        ]

        for (
            intent,
            terms,
            confidence,
        ) in rules:

            matched = [
                term
                for term in terms
                if term in q
            ]

            if matched:

                return {
                    "intent": intent,
                    "confidence": confidence,
                    "matched_terms": matched,
                    "question": original,
                }

        # ---------------------------------------------------------
        # Sales/revenue period question
        # ---------------------------------------------------------

        if (
            re.search(
                r"\b("
                r"sales|sale|revenue|turnover|income"
                r")\b",
                q,
            )
            and
            re.search(
                r"\b("
                r"in|during|for|from|between|last|this"
                r")\b",
                q,
            )
        ):

            return {
                "intent": "TOTAL",
                "confidence": 0.80,
                "matched_terms": [
                    "sales by period"
                ],
                "question": original,
            }

        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "matched_terms": [],
            "question": original,
        }


intent_engine = IntentEngine()

