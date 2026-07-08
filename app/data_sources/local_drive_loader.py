from pathlib import Path
from typing import List

from app.config import settings


class LocalDriveLoader:
    """
    Scans the current user's Documents folder
    and returns all supported files.
    """

    def __init__(self):
        self.documents_path = Path.home() / "Documents"
        self.supported_extensions = settings.supported_extensions

    def scan(self) -> List[Path]:
        """
        Recursively scan the Documents folder.

        Returns:
            List[Path]
        """

        files = []

        if not self.documents_path.exists():
            return files

        for file in self.documents_path.rglob("*"):

            if (
                file.is_file()
                and file.suffix.lower() in self.supported_extensions
            ):
                files.append(file)

        return files

    def exists(self) -> bool:
        """
        Check whether the Documents folder exists.
        """

        return self.documents_path.exists()

    def get_documents_path(self) -> Path:
        """
        Return the current user's Documents folder.
        """

        return self.documents_path