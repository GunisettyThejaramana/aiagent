import fitz  # PyMuPDF
from pathlib import Path


class PDFParser:
    """
    Extracts text from PDF documents.
    """

    def parse(self, file_path: Path) -> str:
        """
        Read a PDF and return all text.

        Args:
            file_path (Path): Path to the PDF file.

        Returns:
            str: Extracted text.
        """

        text = ""

        try:
            document = fitz.open(file_path)

            for page in document:
                text += page.get_text()

            document.close()

        except Exception as e:
            print(f"[PDF ERROR] {file_path}: {e}")

        return text.strip()