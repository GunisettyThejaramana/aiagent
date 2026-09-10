import re

from app.custom_ai.document_knowledge_cache import document_knowledge_cache


class SearchService:

    def __init__(self):

        self.stop_words = {
            "the",
            "is",
            "are",
            "was",
            "were",
            "when",
            "where",
            "what",
            "which",
            "who",
            "why",
            "how",
            "a",
            "an",
            "of",
            "to",
            "for",
            "in",
            "on",
            "at",
            "and",
            "or",
            "do",
            "does",
            "did",
            "can",
            "could",
            "will",
            "would",
            "should",
            "with",
            "about",
            "from",
            "this",
            "that",
            "these",
            "those",
            "tell",
            "give",
            "show",
            "please",
            "me"
        }

        self.months = {
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
            "december"
        }

        self.document_keywords = {
            "sales",
            "sale",
            "revenue",
            "target",
            "achievement",
            "report",
            "reports",
            "summary",
            "kpi",
            "performance",
            "actual",
            "variance",
            "growth",
            "monthly",
            "month",
            "financial",
            "management"
        }

    # ---------------------------------------------------------
    # NORMALIZE TEXT
    # ---------------------------------------------------------

    def normalize(self, text: str) -> str:
        """
        Normalize text for reliable keyword matching.
        """

        if text is None:
            return ""

        text = str(text).lower()

        text = text.replace("-", " ")
        text = text.replace("_", " ")
        text = text.replace("/", " ")

        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ---------------------------------------------------------
    # EXTRACT KEYWORDS
    # ---------------------------------------------------------

    def extract_keywords(self, question: str):
        """
        Remove stop words and return meaningful keywords.
        """

        question = self.normalize(question)

        keywords = []

        for word in question.split():

            if len(word) < 3:
                continue

            if word in self.stop_words:
                continue

            keywords.append(word)

        return keywords

    # ---------------------------------------------------------
    # EXTRACT IMPORTANT TERMS
    # ---------------------------------------------------------

    def extract_months(self, question: str):
        """
        Extract month names from the question.
        """

        normalized = self.normalize(question)

        found_months = []

        for month in self.months:
            if month in normalized:
                found_months.append(month)

        return found_months

    def extract_years(self, question: str):
        """
        Extract four-digit years from the question.
        """

        return re.findall(r"\b20\d{2}\b", question)

    # ---------------------------------------------------------
    # CHECK SALES REPORTING QUESTION
    # ---------------------------------------------------------

    def is_sales_reporting_question(self, question: str) -> bool:
        """
        Identify questions that are clearly asking about
        sales/revenue reports, especially month/year reports.
        """

        normalized = self.normalize(question)
        words = set(normalized.split())

        has_sales_term = bool(
            words.intersection(
                {
                    "sales",
                    "sale",
                    "revenue"
                }
            )
        )

        has_month = bool(self.extract_months(question))
        has_year = bool(self.extract_years(question))

        has_reporting_term = bool(
            words.intersection(
                {
                    "report",
                    "reports",
                    "summary",
                    "total",
                    "actual",
                    "target",
                    "achievement",
                    "performance",
                    "revenue",
                    "sales"
                }
            )
        )

        return (
            has_sales_term
            and
            has_month
            and
            (has_year or has_reporting_term)
        )

    # ---------------------------------------------------------
    # SCORE DOCUMENT
    # ---------------------------------------------------------

    def score_document(
        self,
        source,
        docs,
        keywords,
        question
    ):
        """
        Calculate a relevance score for a group of documents
        belonging to the same source file.
        """

        score = 0

        normalized_source = self.normalize(str(source))
        normalized_question = self.normalize(question)

        # -----------------------------------------------------
        # Filename matching
        # -----------------------------------------------------

        for keyword in keywords:

            if keyword in normalized_source:
                score += 25

        # -----------------------------------------------------
        # Exact phrase matching
        # -----------------------------------------------------

        question_words = normalized_question.split()

        if question_words:
            question_phrase = " ".join(question_words)

            if question_phrase in normalized_source:
                score += 100

        # -----------------------------------------------------
        # Month matching
        # -----------------------------------------------------

        months = self.extract_months(question)

        for month in months:

            if month in normalized_source:
                score += 60

        # -----------------------------------------------------
        # Year matching
        # -----------------------------------------------------

        years = self.extract_years(question)

        for year in years:

            if year in normalized_source:
                score += 60

        # -----------------------------------------------------
        # Document keyword matching
        # -----------------------------------------------------

        for keyword in self.document_keywords:

            if keyword in normalized_question:

                if keyword in normalized_source:
                    score += 20

        # -----------------------------------------------------
        # Content matching
        # -----------------------------------------------------

        combined_content = []

        for doc in docs:

            page_content = getattr(
                doc,
                "page_content",
                ""
            )

            if page_content:
                combined_content.append(
                    self.normalize(page_content)
                )

        full_text = " ".join(combined_content)

        # -----------------------------------------------------
        # Keyword occurrences
        # -----------------------------------------------------

        for keyword in keywords:

            occurrences = full_text.count(keyword)

            if occurrences:

                # Give useful weight to the first few matches,
                # but prevent huge documents from dominating.
                score += min(
                    occurrences * 3,
                    30
                )

        # -----------------------------------------------------
        # Month in content
        # -----------------------------------------------------

        for month in months:

            if month in full_text:
                score += 40

        # -----------------------------------------------------
        # Year in content
        # -----------------------------------------------------

        for year in years:

            if year in full_text:
                score += 40

        # -----------------------------------------------------
        # Strong sales-report matching
        # -----------------------------------------------------

        if self.is_sales_reporting_question(question):

            sales_terms = [
                "sales",
                "sale",
                "revenue"
            ]

            for term in sales_terms:

                if term in normalized_source:
                    score += 40

                if term in full_text:
                    score += 20

        return score

    # ---------------------------------------------------------
    # SEARCH LOCAL DOCUMENTS
    # ---------------------------------------------------------

    def search_local_documents(self, question: str):

        documents = document_knowledge_cache.get_documents()

        if not documents:

            print("\n" + "=" * 60)
            print("Searching Cached Local Documents")
            print("=" * 60)
            print("No cached documents available.")

            return {
                "documents": [],
                "count": 0,
                "score": 0
            }

        keywords = self.extract_keywords(question)

        best_documents = []
        best_score = 0
        best_source = None

        print("\n" + "=" * 60)
        print("Searching Cached Local Documents")
        print("=" * 60)

        print("Question:", question)
        print("Keywords:", keywords)
        print("Cached Documents:", len(documents))

        # ---------------------------------------------------------
        # Group documents by source file
        # ---------------------------------------------------------

        grouped_documents = {}

        for doc in documents:

            source = None

            if hasattr(doc, "metadata") and doc.metadata:

                source = (
                    doc.metadata.get("source")
                    or doc.metadata.get("file_path")
                    or doc.metadata.get("filename")
                    or doc.metadata.get("name")
                )

            if source is None:

                source = "__unknown_source__"

            grouped_documents.setdefault(
                source,
                []
            ).append(doc)

        print(
            "Unique Source Files:",
            len(grouped_documents)
        )

        # ---------------------------------------------------------
        # Search every source file
        # ---------------------------------------------------------

        scored_documents = []

        for source, docs in grouped_documents.items():

            score = self.score_document(
                source=source,
                docs=docs,
                keywords=keywords,
                question=question
            )

            scored_documents.append(
                (
                    score,
                    source,
                    docs
                )
            )

        # ---------------------------------------------------------
        # Sort highest relevance first
        # ---------------------------------------------------------

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True
        )

        # ---------------------------------------------------------
        # Select best document
        # ---------------------------------------------------------

        if scored_documents:

            best_score, best_source, best_documents = (
                scored_documents[0]
            )

        # ---------------------------------------------------------
        # Debug output
        # ---------------------------------------------------------

        print(
            "\nBest Match Score:",
            best_score
        )

        if best_source:

            print(
                "Selected Source:",
                best_source
            )

            print(
                "Selected Document:",
                len(best_documents),
                "page(s)"
            )

        else:

            print(
                "No matching document found."
            )

        # ---------------------------------------------------------
        # Avoid returning completely irrelevant documents
        # ---------------------------------------------------------

        if best_score <= 0:

            print(
                "Document relevance score is too low."
            )

            return {
                "documents": [],
                "count": 0,
                "score": 0,
                "source": None
            }

        # ---------------------------------------------------------
        # Return search result
        # ---------------------------------------------------------

        return {
            "documents": best_documents,
            "count": len(best_documents),
            "score": best_score,
            "source": best_source
        }


# -------------------------------------------------------------
# SERVICE INSTANCE
# -------------------------------------------------------------

search_service = SearchService()