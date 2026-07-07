from pathlib import Path
from datetime import datetime


class MetadataGenerator:
    """
    Generates metadata for local documents.
    """

    @staticmethod
    def generate(file_path: Path) -> dict:
        """
        Generate metadata for a document.

        Args:
            file_path (Path)

        Returns:
            dict
        """

        stat = file_path.stat()

        return {
            "source": "local_drive",
            "file_name": file_path.name,
            "extension": file_path.suffix.lower(),
            "directory": str(file_path.parent),
            "absolute_path": str(file_path.resolve()),
            "size_mb": round(
                stat.st_size / (1024 * 1024),
                2
            ),
            "created_at": datetime.fromtimestamp(
                stat.st_ctime
            ).strftime("%Y-%m-%d %H:%M:%S"),
            "last_modified": datetime.fromtimestamp(
                stat.st_mtime
            ).strftime("%Y-%m-%d %H:%M:%S"),
        }