class KnowledgeRouter:
    """
    Deterministic router for deciding where a question should be answered from.

    Sources:
        - database
        - documents
        - both

    The router is intentionally conservative.

    Rules:
        1. Explicit document language wins.
        2. Report/document-style questions win over generic business words.
        3. Database-specific words such as balance, weaver, loom, stock,
           payment, employee, etc. go to the database.
        4. Questions asking for sales/revenue for a specific reporting
           month/year can be answered from business reports, so they are
           routed to documents in Auto mode.
        5. If nothing is clear, default to database.
    """

    # ================================================================
    # DOCUMENT KEYWORDS
    # ================================================================

    DOCUMENT_KEYWORDS = {
        "document",
        "documents",
        "file",
        "files",
        "pdf",
        "pdfs",
        "manual",
        "manuals",
        "policy",
        "policies",
        "report",
        "reports",
        "mentioned",
        "mention",
        "written",
        "says",
        "said",
        "content",
        "according",
        "guideline",
        "guidelines",
        "procedure",
        "procedures",
        "agreement",
        "contract",
        "contracts",
        "notice",
        "notices",
        "letter",
        "letters",
        "presentation",
        "presentations",
        "reporting",
        "target",
        "achievement",
        "kpi",
        "summary",
        "summarize",
        "summarise",
    }

    # ================================================================
    # DATABASE KEYWORDS
    # ================================================================

    DATABASE_KEYWORDS = {
        "database",
        "table",
        "tables",
        "record",
        "records",
        "row",
        "rows",
        "weaver",
        "weavers",
        "loom",
        "looms",
        "saree",
        "sarees",
        "warp",
        "warps",
        "weft",
        "wefts",
        "stock",
        "stocks",
        "payment",
        "payments",
        "balance",
        "credit",
        "debit",
        "salary",
        "salaries",
        "employee",
        "employees",
        "quantity",
        "price",
        "transaction",
        "transactions",
    }

    # ================================================================
    # BOTH KEYWORDS
    # ================================================================

    BOTH_KEYWORDS = {
        "compare",
        "comparison",
        "difference",
        "against",
        "between",
        "database and document",
        "database and documents",
        "database versus document",
        "database versus documents",
        "database vs document",
        "database vs documents",
    }

    # ================================================================
    # EXPLICIT DOCUMENT PHRASES
    # ================================================================

    DOCUMENT_PHRASES = {
        "according to the report",
        "according to the document",
        "according to the file",
        "according to the pdf",

        "in the report",
        "in the document",
        "in the file",
        "in the pdf",

        "from the report",
        "from the document",
        "from the file",
        "from the pdf",

        "as per the report",
        "as per the document",
        "as per the file",
        "as per the pdf",

        "what does the report say",
        "what does the document say",
        "what does the file say",
        "what does the pdf say",

        "what is mentioned in the report",
        "what is mentioned in the document",
        "what is mentioned in the file",
        "what is mentioned in the pdf",

        "what is written in the report",
        "what is written in the document",
        "what is written in the file",
        "what is written in the pdf",

        "show me the report",
        "show me the document",
        "show me the file",

        "sales report",
        "sales reports",
        "sales target report",
        "sales target achievement report",
        "management report",
        "management kpi report",
        "kpi report",
    }

    # ================================================================
    # REPORTING MONTHS
    # ================================================================

    MONTHS = {
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    }

    # ================================================================
    # NORMALIZE
    # ================================================================

    def normalize(self, text: str) -> str:
        return " ".join(
            str(text or "")
            .lower()
            .strip()
            .split()
        )

    # ================================================================
    # KEYWORD MATCHING
    # ================================================================

    def _contains_keyword(
        self,
        question: str,
        keywords: set[str]
    ) -> bool:

        words = set(question.split())

        for keyword in keywords:

            if " " in keyword:

                if keyword in question:
                    return True

            elif keyword in words:

                return True

        return False

    # ================================================================
    # MONTH + REPORTING QUESTION DETECTION
    # ================================================================

    def _contains_month(self, question: str) -> bool:
        words = set(question.split())

        return any(
            month in words
            for month in self.MONTHS
        )

    def _is_sales_reporting_question(
        self,
        question: str
    ) -> bool:
        """
        Detect questions such as:

            What were the total sales in August 2026?
            What was the revenue in August 2026?
            Show sales for September 2026.
            What were total sales in July?

        These are treated as document/report questions in Auto mode
        because business reporting data is available in indexed reports.
        """

        sales_words = {
            "sales",
            "sale",
            "revenue",
            "turnover",
            "achievement",
        }

        reporting_words = {
            "total",
            "monthly",
            "month",
            "report",
            "actual",
            "target",
            "achievement",
            "summary",
            "were",
            "was",
            "show",
            "give",
        }

        has_sales_word = self._contains_keyword(
            question,
            sales_words
        )

        has_month = self._contains_month(
            question
        )

        has_reporting_word = self._contains_keyword(
            question,
            reporting_words
        )

        # Example:
        # "What were the total sales in August 2026?"
        if (
            has_sales_word
            and has_month
            and has_reporting_word
        ):
            return True

        return False

    # ================================================================
    # ROUTE
    # ================================================================

    def route(self, question: str) -> str:

        question = self.normalize(
            question
        )

        if not question:
            return "database"

        # ------------------------------------------------------------
        # 1. Explicit document phrases always win.
        # ------------------------------------------------------------

        if any(
            phrase in question
            for phrase in self.DOCUMENT_PHRASES
        ):
            return "documents"

        # ------------------------------------------------------------
        # 2. Explicit BOTH questions.
        # ------------------------------------------------------------

        if self._contains_keyword(
            question,
            self.BOTH_KEYWORDS
        ):
            return "both"

        # ------------------------------------------------------------
        # 3. Reporting questions involving a month.
        #
        # Example:
        # "What were the total sales in August 2026?"
        #
        # This must go to documents instead of SQL.
        # ------------------------------------------------------------

        if self._is_sales_reporting_question(
            question
        ):
            return "documents"

        # ------------------------------------------------------------
        # 4. Normal keyword detection.
        # ------------------------------------------------------------

        document_match = self._contains_keyword(
            question,
            self.DOCUMENT_KEYWORDS
        )

        database_match = self._contains_keyword(
            question,
            self.DATABASE_KEYWORDS
        )

        # ------------------------------------------------------------
        # 5. Document language wins when both types occur.
        # ------------------------------------------------------------

        if document_match:
            return "documents"

        # ------------------------------------------------------------
        # 6. Database language.
        # ------------------------------------------------------------

        if database_match:
            return "database"

        # ------------------------------------------------------------
        # 7. Default behavior.
        # ------------------------------------------------------------

        return "database"


# ================================================================
# GLOBAL ROUTER INSTANCE
# ================================================================

knowledge_router = KnowledgeRouter()