import re

from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class SearchService:

    def __init__(self):
        self.drive_loader = LocalDriveLoader()
        self.detector = FileDetector()

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

        files = self.drive_loader.scan()

        if not files:

            return {
                "documents": [],
                "count": 0
            }

        keywords = self.extract_keywords(question)

        best_documents = []
        best_score = 0

        print("\n" + "=" * 60)
        print("Searching Local Documents")
        print("=" * 60)
        print("Keywords:", keywords)

        for file in files:

            print(f"\nScanning: {file.name}")

            docs = self.detector.load(file)

            if not docs:
                continue

            score = 0

            filename = self.normalize(file.name)

            # -----------------------------
            # Filename Matching
            # -----------------------------
            for keyword in keywords:

                if keyword in filename:
                    score += 25

            # -----------------------------
            # Content Matching
            # -----------------------------
            for doc in docs:

                text = self.normalize(doc.page_content)

                for keyword in keywords:

                    occurrences = text.count(keyword)

                    if occurrences:

                        score += occurrences * 3

            print(f"Score: {score}")

            if score > best_score:

                best_score = score
                best_documents = docs

        print("\nBest Match Score:", best_score)

        if best_documents:

            print("Selected Document:", len(best_documents), "page(s)")

        else:

            print("No matching document found.")

        return {
            "documents": best_documents,
            "count": len(best_documents)
        }