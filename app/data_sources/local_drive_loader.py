from pathlib import Path
from typing import List

from app.config import settings


class LocalDriveLoader:
    """
    Scans one or more local folders and returns all supported files.

    The folders to scan are configured in settings.local_scan_paths.
    """

    def __init__(self):
        self.supported_extensions = {
            ext.lower() for ext in settings.supported_extensions
        }

        # Read scan paths from config
        self.scan_paths = [
            Path(path).expanduser()
            for path in settings.local_scan_paths
        ]

    def scan(self) -> List[Path]:
        """
        Recursively scan all configured folders.

        Returns:
            List[Path]: List of supported files.
        """

        files = []
        visited = set()

        # Folders that should never be scanned
        excluded_dirs = {
            "Windows",
            "Program Files",
            "Program Files (x86)",
            "AppData",
            "$Recycle.Bin",
            "System Volume Information",
            "node_modules",
            ".git",
            ".venv",
            "venv",
            "__pycache__",
        }

        for root in self.scan_paths:

            if not root.exists():
                continue

            try:
                for file in root.rglob("*"):

                    # Skip excluded folders
                    if any(part in excluded_dirs for part in file.parts):
                        continue

                    if (
                        file.is_file()
                        and file.suffix.lower() in self.supported_extensions
                    ):

                        # Avoid duplicates
                        resolved = file.resolve()

                        if resolved not in visited:
                            visited.add(resolved)
                            files.append(file)

            except PermissionError:
                # Skip folders that Windows does not allow us to read
                continue

            except Exception:
                continue

        return sorted(files)

    def exists(self) -> bool:
        """
        Returns True if at least one configured folder exists.
        """

        return any(path.exists() for path in self.scan_paths)

    def get_scan_paths(self) -> List[Path]:
        """
        Return the configured scan folders.
        """

        return self.scan_paths