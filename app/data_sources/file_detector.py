from pathlib import Path

from app.data_sources.pdf_loader import load_pdf
from app.data_sources.word_loader import load_word
from app.data_sources.excel_loader import load_excel
from app.data_sources.csv_loader import load_csv
from app.data_sources.txt_loader import load_text


class FileDetector:
    """
    Detects the file type and calls the appropriate loader.
    """

    def __init__(self):
        self.supported_loaders = {
            ".pdf": load_pdf,
            ".docx": load_word,
            ".xlsx": load_excel,
            ".csv": load_csv,
            ".txt": load_text,
        }

    def load(self, file_path: Path):
        """
        Load a document based on its extension.

        Parameters
        ----------
        file_path : Path

        Returns
        -------
        list
            LangChain Document objects
        """

        extension = file_path.suffix.lower()

        loader = self.supported_loaders.get(extension)

        if loader is None:
            return []

        try:
            return loader(str(file_path))

        except Exception as e:
            print(f"Failed to load {file_path}: {e}")
            return []

    def is_supported(self, file_path: Path) -> bool:
        """
        Check whether the file type is supported.
        """

        return file_path.suffix.lower() in self.supported_loaders