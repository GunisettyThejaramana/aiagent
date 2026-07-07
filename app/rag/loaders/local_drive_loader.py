from pathlib import Path
from typing import List

from app.config import settings


class LocalDriveLoader:
    """
    Scans configured local folders and returns all supported files.

    Supported extensions are defined in config.py.
    """

    def __init__(self):
        self.document_paths = settings.document_paths
        self.supported_extensions = {
            ext.lower() for ext in settings.SUPPORTED_FILE_TYPES
        }

    def scan(self) -> List[Path]:
        """
        Scan all configured folders recursively.

        Returns:
            List[Path]: List of supported files.
        """
        files = []

        for folder in self.document_paths:
            folder_path = Path(folder)

            if not folder_path.exists():
                print(f"[WARNING] Folder not found: {folder}")
                continue

            if not folder_path.is_dir():
                print(f"[WARNING] Not a directory: {folder}")
                continue

            for file in folder_path.rglob("*"):

                if not file.is_file():
                    continue

                if file.suffix.lower() not in self.supported_extensions:
                    continue

                try:
                    file_size_mb = (
                        file.stat().st_size / (1024 * 1024)
                    )

                    if file_size_mb > settings.MAX_FILE_SIZE_MB:
                        print(
                            f"[SKIPPED] Large file: {file}"
                        )
                        continue

                except Exception:
                    continue

                files.append(file)

        return files

    def get_file_count(self) -> int:
        """
        Returns the number of supported files found.
        """
        return len(self.scan())