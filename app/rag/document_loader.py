from pathlib import Path
from typing import List

from langchain_core.documents import Document

from app.rag.loaders.local_drive_loader import LocalDriveLoader

from app.rag.parsers.pdf_parser import PDFParser
from app.rag.parsers.word_parser import WordParser
from app.rag.parsers.excel_parser import ExcelParser
from app.rag.parsers.csv_parser import CSVParser
from app.rag.parsers.ppt_parser import PPTParser
from app.rag.parsers.text_parser import TextParser

from app.rag.metadata import MetadataGenerator


class DocumentLoader:
    """
    Loads all supported documents from configured local folders.
    """

    def __init__(self):

        self.loader = LocalDriveLoader()

        self.parsers = {
            ".pdf": PDFParser(),
            ".docx": WordParser(),
            ".xlsx": ExcelParser(),
            ".csv": CSVParser(),
            ".pptx": PPTParser(),
            ".txt": TextParser(),
        }

    def load_documents(self) -> List[Document]:

        documents = []

        files = self.loader.scan()

        for file_path in files:

            parser = self.parsers.get(file_path.suffix.lower())

            if parser is None:
                continue

            text = parser.parse(file_path)

            if not text.strip():
                continue

            metadata = MetadataGenerator.generate(file_path)

            documents.append(
                Document(
                    page_content=text,
                    metadata=metadata,
                )
            )

        return documents