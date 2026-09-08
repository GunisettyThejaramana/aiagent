from __future__ import annotations


class MetricEngine:
    """
    Understands what business value the user wants to calculate.

    This engine is database-independent.
    It does not generate SQL.
    """

    METRIC_KEYWORDS = {
        "total_balance": [
            "balance",
            "balances",
            "total balance",
            "remaining balance",
            "outstanding balance",
            "outstanding",
            "due balance",
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
            "amount debit",
            "amount_debit",
        ],

        "advance_amount": [
            "advance",
            "advance amount",
            "advances",
            "money given in advance",
        ],

        "quantity": [
            "quantity",
            "quantities",
            "amount of",
            "number of items",
            "items",
        ],

        "price": [
            "price",
            "prices",
            "cost",
            "costs",
            "unit price",
        ],

        "salary": [
            "salary",
            "salaries",
            "pay",
            "wages",
        ],

        "revenue": [
            "revenue",
            "turnover",
            "income",
            "sales revenue",
        ],

        "amount": [
            "amount",
            "value",
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
            "production count",
            "production quantity",
        ],
    }

    # Default metric for ranking questions when the user
    # does not explicitly specify what to rank by.
    #
    # Example:
    #   "show top 5 weavers"
    #       -> total_balance
    #
    #   "show top 5 employees"
    #       -> salary
    #
    # Explicit metrics always take priority over these defaults.
    RANKING_DEFAULTS = {
        "weaver": "total_balance",
        "weavers": "total_balance",

        "loom": "total_balance",
        "looms": "total_balance",

        "employee": "salary",
        "employees": "salary",

        "customer": "revenue",
        "customers": "revenue",

        "sales": "revenue",
        "sale": "revenue",

        "product": "revenue",
        "products": "revenue",

        "saree": "amount",
        "sarees": "amount",

        "order": "quantity",
        "orders": "quantity",

        "material": "quantity",
        "materials": "quantity",

        "payment": "amount",
        "payments": "amount",
    }

    # Stronger phrases should win over generic words.
    PHRASE_PRIORITY = {
        "total debit": 5,
        "total credit": 5,
        "total balance": 5,
        "outstanding balance": 5,
        "advance amount": 5,
        "sarees produced": 5,
        "saree produced": 5,
        "produced sarees": 5,
        "number of sarees": 5,
        "how many sarees": 5,
        "saree count": 5,
        "sales revenue": 5,
        "production quantity": 5,
    }

    RANKING_KEYWORDS = [
        "top",
        "highest",
        "maximum",
        "max",
        "best",
        "largest",
        "bottom",
        "lowest",
        "minimum",
        "min",
        "worst",
        "smallest",
    ]

    def _normalize(self, text: str) -> str:
        return " ".join(
            (text or "").lower().strip().split()
        )

    def _score_metric(
        self,
        question: str,
        metric: str,
        keywords: list[str],
    ) -> tuple[int, list[str]]:
        score = 0
        matched_terms = []

        for keyword in keywords:
            keyword_normalized = self._normalize(keyword)

            if keyword_normalized in question:
                matched_terms.append(keyword)

                # Longer phrases are more meaningful.
                word_count = len(keyword_normalized.split())

                if word_count >= 3:
                    score += 4
                elif word_count == 2:
                    score += 3
                else:
                    score += 2

                # Important phrases receive additional weight.
                score += self.PHRASE_PRIORITY.get(
                    keyword_normalized,
                    0,
                )

        return score, matched_terms

    def _is_ranking_question(
        self,
        question: str,
    ) -> bool:
        for keyword in self.RANKING_KEYWORDS:
            if keyword in question:
                return True

        return False

    def _detect_ranking_entity(
        self,
        question: str,
    ) -> str | None:
        """
        Detect the main business entity in a ranking question.

        This is intentionally simple and deterministic.
        It does not depend on database table names.
        """

        # Check longer/more specific forms first.
        entities = sorted(
            self.RANKING_DEFAULTS.keys(),
            key=len,
            reverse=True,
        )

        for entity in entities:
            if entity in question:
                return entity

        return None

    def _get_ranking_default_metric(
        self,
        question: str,
    ) -> str | None:
        """
        Determine a default ranking metric when the user
        asks for TOP/BOTTOM but does not specify a metric.
        """

        if not self._is_ranking_question(question):
            return None

        entity = self._detect_ranking_entity(question)

        if not entity:
            return None

        return self.RANKING_DEFAULTS.get(entity)

    def understand(
        self,
        question: str,
        schema: dict | None = None,
    ) -> dict:
        original_question = question
        normalized_question = self._normalize(question)

        candidates = []

        for metric, keywords in self.METRIC_KEYWORDS.items():
            score, matched_terms = self._score_metric(
                normalized_question,
                metric,
                keywords,
            )

            if score > 0:
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
        # Explicit metric found
        # ---------------------------------------------------------
        if candidates:
            best = candidates[0]

            if best["score"] >= 10:
                confidence = 0.99
            elif best["score"] >= 7:
                confidence = 0.95
            elif best["score"] >= 5:
                confidence = 0.90
            elif best["score"] >= 3:
                confidence = 0.80
            else:
                confidence = 0.70

            return {
                "metric": best["metric"],
                "confidence": confidence,
                "matched_terms": best["matched_terms"],
                "candidate_metrics": candidates,
                "question": original_question,
            }

        # ---------------------------------------------------------
        # No explicit metric.
        #
        # If this is a ranking question, use a deterministic
        # business default based on the entity.
        # ---------------------------------------------------------
        ranking_metric = self._get_ranking_default_metric(
            normalized_question
        )

        if ranking_metric:
            return {
                "metric": ranking_metric,
                "confidence": 0.75,
                "matched_terms": [],
                "candidate_metrics": [
                    {
                        "metric": ranking_metric,
                        "score": 0,
                        "matched_terms": [],
                        "default": True,
                    }
                ],
                "question": original_question,
                "default_metric": True,
                "default_reason": (
                    "No explicit ranking metric was specified, "
                    "so a business-default metric was selected."
                ),
            }

        # ---------------------------------------------------------
        # No metric could be determined.
        # ---------------------------------------------------------
        return {
            "metric": None,
            "confidence": 0.0,
            "matched_terms": [],
            "candidate_metrics": [],
            "question": original_question,
        }


metric_engine = MetricEngine()