
from __future__ import annotations

import re


class MetricEngine:
    """
    Determines what business value the user wants.

    This is intentionally database-independent.

    IMPORTANT:

    'revenue' does NOT mean that the database must contain
    a column named revenue.

    Later stages map the metric to the real database column.

    Example:

        revenue
            ->
        grand_total
        net_amount
        sales_value
        invoice_total
        total_amount
        quantity * price
    """

    METRIC_KEYWORDS = {

        "total_balance": [
            "balance",
            "balances",
            "total balance",
            "remaining balance",
            "outstanding balance",
            "outstanding amount",
            "amount due",
            "due balance",
            "pending amount",
        ],

        "total_credit": [
            "credit",
            "credits",
            "total credit",
            "credited",
            "credit amount",
            "credited amount",
        ],

        "total_debit": [
            "debit",
            "debits",
            "total debit",
            "debited",
            "debit amount",
            "debited amount",
        ],

        "advance_amount": [
            "advance",
            "advance amount",
            "advances",
            "money given in advance",
            "advance payment",
            "prepayment",
        ],

        "quantity": [
            "quantity",
            "quantities",
            "units",
            "unit count",
            "number of items",
            "volume",
        ],

        "price": [
            "price",
            "prices",
            "cost",
            "costs",
            "rate",
            "unit price",
            "selling price",
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

        "profit": [
            "profit",
            "profits",
            "profit amount",
            "gain",
            "gains",
            "margin",
        ],

        "loss": [
            "loss",
            "losses",
            "loss amount",
        ],

        "revenue": [
            "revenue",
            "revenues",
            "sales",
            "sale",
            "turnover",
            "income",
            "sales revenue",
            "sales amount",
            "sales value",
            "selling amount",
            "selling value",
            "receipts",
            "collections",
        ],

        "amount": [
            "amount",
            "amounts",
            "value",
            "values",
            "money",
            "monetary value",
            "total amount",
        ],

        "num_sarees": [
            "sarees produced",
            "saree produced",
            "produced sarees",
            "number of sarees",
            "how many sarees",
            "saree quantity",
            "saree count",
            "production quantity",
        ],
    }

    RANKING_DEFAULTS = {

        "weaver": "total_balance",

        "loom": "total_balance",

        "employee": "salary",

        "customer": "revenue",

        "sales": "revenue",

        "product": "revenue",

        "saree": "amount",

        "order": "quantity",

        "material": "quantity",

        "payment": "amount",
    }

    # =============================================================
    # MAIN
    # =============================================================

    def understand(
        self,
        question: str,
    ) -> dict:

        original = question or ""

        normalized = re.sub(
            r"\s+",
            " ",
            original.lower(),
        ).strip()

        candidates = []

        for metric, terms in self.METRIC_KEYWORDS.items():

            matched_terms = []

            score = 0

            for term in terms:

                if re.search(
                    rf"\b{re.escape(term)}\b",
                    normalized,
                ):

                    matched_terms.append(
                        term
                    )

                    if " " in term:
                        score += 6
                    else:
                        score += 3

            if matched_terms:

                candidates.append(
                    {
                        "metric": metric,
                        "score": score,
                        "matched_terms": matched_terms,
                    }
                )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # ---------------------------------------------------------
        # Strong sales/revenue phrase
        # ---------------------------------------------------------

        if re.search(
            r"\b(total|overall|combined)\s+"
            r"(sales|revenue|turnover|income)\b",
            normalized,
        ):

            candidates.insert(
                0,
                {
                    "metric": "revenue",
                    "score": 100,
                    "matched_terms": [
                        "total sales/revenue"
                    ],
                },
            )

        if candidates:

            best = candidates[0]

            return {
                "metric": best["metric"],
                "confidence": min(
                    0.99,
                    0.70
                    + best["score"] / 100,
                ),
                "matched_terms": best[
                    "matched_terms"
                ],
                "candidate_metrics": candidates,
                "question": original,
            }

        # ---------------------------------------------------------
        # Ranking default
        # ---------------------------------------------------------

        for entity, metric in self.RANKING_DEFAULTS.items():

            if not re.search(
                rf"\b{re.escape(entity)}s?\b",
                normalized,
            ):
                continue

            if not re.search(
                r"\b(top|bottom|highest|lowest|best|worst)\b",
                normalized,
            ):
                continue

            return {
                "metric": metric,
                "confidence": 0.75,
                "matched_terms": [],
                "candidate_metrics": [
                    {
                        "metric": metric,
                        "default": True,
                    }
                ],
                "question": original,
            }

        return {
            "metric": None,
            "confidence": 0.0,
            "matched_terms": [],
            "candidate_metrics": [],
            "question": original,
        }


metric_engine = MetricEngine()

