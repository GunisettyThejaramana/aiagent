from typing import List

from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class DocumentLoader:
    """
    Loads all supported documents from the configured
    local scan paths for use in the RAG pipeline.
    """

    def __init__(self):
        self.local_loader = LocalDriveLoader()
        self.file_detector = FileDetector()

    def load_documents(self) -> List:
        """
        Scan all configured folders and load supported documents.

        Returns
        -------
        List
            List of LangChain Document objects.
        """

        documents = []

        files = self.local_loader.scan()

        print(f"Found {len(files)} supported file(s).")

        for file in files:

            try:
                docs = self.file_detector.load(file)

                if docs:
                    documents.extend(docs)
                    print(f"Loaded: {file}")

            except Exception as e:
                print(f"Error loading '{file}': {e}")

        print(f"\nTotal loaded documents: {len(documents)}")

        return documents

    def document_count(self) -> int:
        """
        Return the number of supported files found.
        """
        return len(self.local_loader.scan())

    def supported_files(self):
        """
        Return the list of supported files found during scanning.
        """
        return self.local_loader.scan()