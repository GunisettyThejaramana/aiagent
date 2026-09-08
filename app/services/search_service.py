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

    def normalize(self, text: str) -> str:
        """
        Normalize text.
        """

        text = text.lower()

        text = text.replace("-", " ")
        text = text.replace("_", " ")
        text = text.replace("/", " ")

        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def extract_keywords(self, question: str):
        """
        Remove stop words and keep only meaningful keywords.
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

    def search_local_documents(self, question: str):

        documents = document_knowledge_cache.get_documents()

        if not documents:

            return {
                "documents": [],
                "count": 0
            }

        keywords = self.extract_keywords(question)

        best_documents = []
        best_score = 0

        print("\n" + "=" * 60)
        print("Searching Cached Local Documents")
        print("=" * 60)

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
                )

            if source is None:
                source = "__unknown_source__"

            grouped_documents.setdefault(source, []).append(doc)

        # ---------------------------------------------------------
        # Search cached documents
        # ---------------------------------------------------------

        for source, docs in grouped_documents.items():

            score = 0

            filename = self.normalize(str(source))

            # -----------------------------------------------------
            # Filename matching
            # -----------------------------------------------------

            for keyword in keywords:

                if keyword in filename:
                    score += 25

            # -----------------------------------------------------
            # Content matching
            # -----------------------------------------------------

            for doc in docs:

                page_content = getattr(
                    doc,
                    "page_content",
                    ""
                )

                text = self.normalize(page_content)

                for keyword in keywords:

                    occurrences = text.count(keyword)

                    if occurrences:
                        score += occurrences * 3

            # -----------------------------------------------------
            # Best document
            # -----------------------------------------------------

            if score > best_score:

                best_score = score
                best_documents = docs

        print("\nBest Match Score:", best_score)

        if best_documents:

            print(
                "Selected Document:",
                len(best_documents),
                "page(s)"
            )

        else:

            print("No matching document found.")

        return {
            "documents": best_documents,
            "count": len(best_documents)
        }