from pathlib import Path

from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class DocumentIndex:

    def __init__(self):

        self.loader = LocalDriveLoader()
        self.detector = FileDetector()

        self.documents = []

    def build(self):

        self.documents.clear()

        files = self.loader.scan()

        for file in files:

            docs = self.detector.load(file)

            self.documents.extend(docs)

        return self.documents

    def get_documents(self):

        return self.documents