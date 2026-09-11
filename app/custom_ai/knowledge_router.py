"""
Intelligent knowledge router.

Possible routes:

    chat
    database
    documents
    both

Ollama performs the primary classification.

A small deterministic fallback is retained so the
application can still make a reasonable decision if
Ollama is temporarily unavailable.
"""

from __future__ import annotations

from app.ollama_client import ollama_client


class KnowledgeRouter:

    # ============================================================
    # NORMALIZE
    # ============================================================

    def normalize(
        self,
        text: str,
    ) -> str:

        return " ".join(
            str(text or "")
            .lower()
            .strip()
            .split()
        )

    # ============================================================
    # DETERMINISTIC FALLBACK
    # ============================================================

    def fallback_route(
        self,
        question: str,
    ) -> str:

        q = self.normalize(question)

        if not q:
            return "chat"

        # --------------------------------------------------------
        # Explicit document language
        # --------------------------------------------------------

        document_terms = [
            "document",
            "documents",
            "file",
            "files",
            "pdf",
            "report",
            "reports",
            "manual",
            "policy",
            "policies",
            "contract",
            "agreement",
            "presentation",
            "according to the report",
            "according to the document",
            "according to the file",
            "what does the report say",
            "what does the document say",
            "what is mentioned in the report",
            "what is mentioned in the document",
            "what is written in the report",
            "what is written in the document",
        ]

        if any(
            term in q
            for term in document_terms
        ):
            return "documents"

        # --------------------------------------------------------
        # Database terms
        # --------------------------------------------------------

        database_terms = [
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
            "transaction",
            "transactions",
            "quantity",
            "price",
            "sales data",
            "sales records",
        ]

        if any(
            term in q
            for term in database_terms
        ):
            return "database"

        # --------------------------------------------------------
        # Comparison
        # --------------------------------------------------------

        both_terms = [
            "database and document",
            "database and documents",
            "database vs document",
            "database vs documents",
            "compare database",
            "compare the database",
        ]

        if any(
            term in q
            for term in both_terms
        ):
            return "both"

        # --------------------------------------------------------
        # Default = CHAT
        # --------------------------------------------------------

        return "chat"

    # ============================================================
    # FAST LOCAL ROUTING
    # ============================================================

    def route(
        self,
        question: str,
        database_available: bool = True,
        documents_available: bool = True,
    ) -> str:
        """Route locally first. No LLM call is used for routing."""
        q = self.normalize(question)
        if not q:
            return "chat"

        # Explicit combined requests must be checked first.
        both_terms = (
            "database and document", "database and documents",
            "database and pdf", "database and report",
            "both database", "compare database",
            "compare the database with", "compare database with",
        )
        if any(x in q for x in both_terms):
            return "both"

        document_terms = (
            "document", "documents", "pdf", "file", "files",
            "report", "reports", "manual", "policy", "policies",
            "contract", "agreement", "presentation",
            "according to the report", "according to the document",
            "according to the pdf", "what does the report say",
            "what does the document say", "what does the pdf say",
            "what is mentioned in the report",
            "what is mentioned in the document",
            "uploaded file", "uploaded document",
        )
        database_terms = (
            "database", "table", "tables", "record", "records",
            "row", "rows", "weaver", "weavers", "loom", "looms",
            "saree", "sarees", "warp", "warps", "weft", "wefts",
            "stock", "stocks", "payment", "payments", "balance",
            "transaction", "transactions", "quantity", "price",
            "sales", "sale", "revenue", "profit", "customer",
            "customers", "employee", "employees", "salary",
            "invoice", "invoices", "order", "orders", "inventory",
            "production", "production data", "business data",
            "last month", "this month", "today", "yesterday",
            "last year", "this year", "how many", "total",
            "count", "average", "sum",
        )

        has_doc = any(x in q for x in document_terms)
        has_db = any(x in q for x in database_terms)

        if has_doc and has_db:
            return "both"
        if has_doc:
            return "documents"
        if has_db:
            return "database"

        return "chat"


# ============================================================
# GLOBAL ROUTER
# ============================================================

knowledge_router = KnowledgeRouter()