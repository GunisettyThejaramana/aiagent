from pathlib import Path
from typing import Callable, Dict, List

from app.data_sources.pdf_loader import load_pdf
from app.data_sources.word_loader import load_word
from app.data_sources.excel_loader import load_excel
from app.data_sources.csv_loader import load_csv
from app.data_sources.txt_loader import load_text
from app.data_sources.json_loader import load_json
from app.data_sources.xml_loader import load_xml
from app.data_sources.html_loader import load_html
from app.data_sources.markdown_loader import load_markdown
from app.data_sources.ppt_loader import load_ppt


class FileDetector:
    """
    Detects the file type and calls the appropriate loader.
    """

    def __init__(self):
        self.supported_loaders: Dict[str, Callable] = {
            ".pdf": load_pdf,
            ".doc": load_word,
            ".docx": load_word,
            ".xlsx": load_excel,
            ".csv": load_csv,
            ".txt": load_text,
            ".json": load_json,
            ".xml": load_xml,
            ".html": load_html,
            ".htm": load_html,
            ".md": load_markdown,
            ".pptx": load_ppt,
        }

    def load(self, file_path: Path) -> List:
        """
        Load a document using the appropriate loader.
        """

        loader = self.supported_loaders.get(file_path.suffix.lower())

        if loader is None:
            return []

        try:
            return loader(str(file_path))
        except Exception:
            return []

    def is_supported(self, file_path: Path) -> bool:
        """
        Check whether the file type is supported.
        """
        return file_path.suffix.lower() in self.supported_loaders

    def get_supported_extensions(self) -> List[str]:
        """
        Return all supported file extensions.
        """
        return sorted(self.supported_loaders.keys())