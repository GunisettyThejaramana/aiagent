"""
Source hint helper for the Enterprise AI Assistant.

IMPORTANT:
    AUTO mode is NOT keyword based.

The normal AUTO decision is made by checking real evidence from:
    1. the connected database deterministic pipeline
    2. the local document search index
    3. general Ollama chat when neither source can answer

This module only recognizes explicit user instructions such as:
    "according to the report"
    "from the database"
    "use the document"
    "compare the database with the report"

It does not classify ordinary words such as "sales", "total", "report",
"balance", etc. as a source.
"""

from __future__ import annotations


class KnowledgeRouter:
    """Detect only explicit source requests.

    The actual AUTO routing is evidence-based and is implemented in
    app.routes. This class intentionally does not guess a source from
    business keywords.
    """

    DOCUMENT_PHRASES = (
        "according to the document",
        "according to the documents",
        "according to the pdf",
        "according to the report",
        "according to the reports",
        "according to the file",
        "according to the files",
        "from the document",
        "from the documents",
        "from the pdf",
        "from the report",
        "from the reports",
        "from the file",
        "from the files",
        "use the document",
        "use the documents",
        "use the pdf",
        "use the report",
        "use the file",
        "what does the document say",
        "what do the documents say",
        "what does the pdf say",
        "what does the report say",
        "what do the reports say",
        "what is mentioned in the document",
        "what is mentioned in the report",
        "what is written in the document",
        "what is written in the report",
        "in the document",
        "in the pdf",
        "in the report",
        "in the uploaded file",
        "in the uploaded document",
    )

    DATABASE_PHRASES = (
        "according to the database",
        "according to the database records",
        "according to database records",
        "from the database",
        "from database",
        "from the database records",
        "from database records",
        "use the database",
        "use database",
        "in the database",
        "in database",
        "from the records",
        "from database records",
    )

    BOTH_PHRASES = (
        "database and document",
        "database and documents",
        "database and pdf",
        "database and report",
        "database and reports",
        "database with document",
        "database with documents",
        "database with pdf",
        "database with report",
        "database with reports",
        "compare database with",
        "compare the database with",
        "compare database and",
        "compare the database and",
        "compare database to",
        "compare the database to",
    )

    @staticmethod
    def normalize(text: str) -> str:
        return " ".join(
            str(text or "").lower().strip().split()
        )

    def explicit_route(self, question: str) -> str | None:
        """Return an explicitly requested source, otherwise None."""
        q = self.normalize(question)

        if not q:
            return None

        if any(phrase in q for phrase in self.BOTH_PHRASES):
            return "both"

        if any(phrase in q for phrase in self.DOCUMENT_PHRASES):
            return "documents"

        if any(phrase in q for phrase in self.DATABASE_PHRASES):
            return "database"

        return None

    def route(
        self,
        question: str,
        database_available: bool = True,
        documents_available: bool = True,
    ) -> str:
        """Compatibility method.

        It returns an explicit source when the user explicitly requested
        one. Otherwise it returns ``auto`` so the caller can perform
        evidence-based routing.
        """
        explicit = self.explicit_route(question)

        if explicit == "database" and not database_available:
            return "auto"

        if explicit == "documents" and not documents_available:
            return "auto"

        if explicit:
            return explicit

        return "auto"


knowledge_router = KnowledgeRouter()
