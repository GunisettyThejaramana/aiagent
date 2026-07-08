from pathlib import Path

from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class SearchService:

    def __init__(self):

        self.drive_loader = LocalDriveLoader()
        self.detector = FileDetector()

    def search_local_documents(
        self,
        question: str
    ):

        files = self.drive_loader.scan()

        matched_documents = []

        keywords = [
            word.lower()
            for word in question.split()
            if len(word) > 2
        ]

        for file in files:

            filename = file.name.lower()

            # Match filename first
            if any(keyword in filename for keyword in keywords):

                docs = self.detector.load(file)

                matched_documents.extend(docs)

                continue

            # Otherwise inspect the document
            docs = self.detector.load(file)

            for doc in docs:

                text = doc.page_content.lower()

                if any(keyword in text for keyword in keywords):

                    matched_documents.append(doc)

        return {
    "documents": matched_documents,
    "count": len(matched_documents)
}