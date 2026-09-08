class KnowledgeRouter:
    """
    Deterministic router for deciding where a question should be answered from.

    Possible sources:
        - database
        - documents
        - both
    """

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
    }

    DATABASE_KEYWORDS = {
        "database",
        "table",
        "tables",
        "record",
        "records",
        "row",
        "rows",
        "sales",
        "sale",
        "customer",
        "customers",
        "product",
        "products",
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
        "revenue",
        "quantity",
        "price",
        "amount",
        "count",
        "total",
        "average",
        "highest",
        "lowest",
        "top",
        "bottom",
    }

    BOTH_KEYWORDS = {
        "compare",
        "comparison",
        "difference",
        "against",
        "between",
        "database and document",
        "database and documents",
    }

    def normalize(self, text: str) -> str:
        return " ".join(text.lower().strip().split())

    def _contains_keyword(self, question: str, keywords: set[str]) -> bool:
        words = set(question.split())

        for keyword in keywords:
            if " " in keyword:
                if keyword in question:
                    return True
            elif keyword in words:
                return True

        return False

    def route(self, question: str) -> str:
        question = self.normalize(question)

        if not question:
            return "database"

        # Explicit request to compare database information with documents.
        if self._contains_keyword(question, self.BOTH_KEYWORDS):
            return "both"

        document_match = self._contains_keyword(
            question,
            self.DOCUMENT_KEYWORDS,
        )

        database_match = self._contains_keyword(
            question,
            self.DATABASE_KEYWORDS,
        )

        if document_match and database_match:
         document_phrases = {
        "what does",
        "what is mentioned",
        "what is written",
        "according to",
        "what does the",
        "what do the",
    }

         if any(phrase in question for phrase in document_phrases):
            return "documents"

         return "both"
        if document_match:
            return "documents"

        return "database"


knowledge_router = KnowledgeRouter()