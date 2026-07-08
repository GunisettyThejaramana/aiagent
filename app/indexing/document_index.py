from typing import List

from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class DocumentIndex:
    """
    Builds a document index from all supported files
    found in the configured local scan paths.
    """

    def __init__(self):
        self.loader = LocalDriveLoader()
        self.detector = FileDetector()
        self.documents: List = []

    def build(self) -> List:
        """
        Scan configured folders, detect supported files,
        load them, and build the document collection.

        Returns
        -------
        List
            List of LangChain Document objects.
        """

        self.documents.clear()

        files = self.loader.scan()

        for file in files:
            try:
                docs = self.detector.load(file)

                if docs:
                    self.documents.extend(docs)

            except Exception:
                continue

        return self.documents

    def get_documents(self) -> List:
        """
        Return all indexed documents.
        """
        return self.documents

    def clear(self):
        """
        Clear the current document index.
        """
        self.documents.clear()

    def document_count(self) -> int:
        """
        Return the number of indexed documents.
        """
        return len(self.documents)