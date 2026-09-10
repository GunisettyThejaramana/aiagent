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
    # OLLAMA ROUTING
    # ============================================================

    def route(
        self,
        question: str,
        database_available: bool = True,
        documents_available: bool = True,
    ) -> str:

        question = self.normalize(
            question
        )

        if not question:
            return "chat"

        if not ollama_client.is_available():

            print(
                "Ollama unavailable. "
                "Using deterministic router."
            )

            return self.fallback_route(
                question
            )

        system_prompt = """
You are the routing brain of an enterprise AI assistant.

Classify the user's question into exactly ONE route:

chat
database
documents
both

ROUTE DEFINITIONS:

chat:
- Greetings
- Casual conversation
- General knowledge
- Programming questions
- Technical explanations
- Writing help
- Mathematics
- Learning questions
- Questions that do not require company data

database:
- Questions requiring structured business data
- Sales records
- Customers
- Employees
- Products
- Payments
- Inventory
- Transactions
- Counts
- Totals
- Averages
- Rankings
- Dates in business records
- Any question asking for values that should come
  from database tables

documents:
- Questions explicitly asking about uploaded files
- PDFs
- Reports
- Manuals
- Policies
- Contracts
- Presentations
- Document content
- "According to the report..."
- "What does the document say?"
- "What is mentioned in the PDF?"

both:
- The user explicitly requires information from both
  database and documents.
- Comparisons between database information and documents.

IMPORTANT:

A simple greeting such as:
"hello"
"hi"
"good morning"
must ALWAYS be classified as chat.

A general question such as:
"What is Python?"
must be chat.

Return ONLY JSON:

{
  "route": "chat"
}

or

{
  "route": "database"
}

or

{
  "route": "documents"
}

or

{
  "route": "both"
}
"""

        user_prompt = f"""
DATABASE AVAILABLE:
{database_available}

DOCUMENTS AVAILABLE:
{documents_available}

USER QUESTION:
{question}

Choose exactly one route.
"""

        try:

            result = ollama_client.generate_json(
                system_prompt,
                user_prompt,
            )

            route = str(
                result.get(
                    "route",
                    "",
                )
            ).strip().lower()

            if route in {
                "chat",
                "database",
                "documents",
                "both",
            }:

                return route

        except Exception as exc:

            print(
                "Ollama routing error:",
                exc,
            )

        return self.fallback_route(
            question
        )


# ============================================================
# GLOBAL ROUTER
# ============================================================

knowledge_router = KnowledgeRouter()