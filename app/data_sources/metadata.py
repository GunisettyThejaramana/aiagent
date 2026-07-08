from pathlib import Path


class DocumentMetadata:

    @staticmethod
    def build(file_path: Path):

        stat = file_path.stat()

        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_type": file_path.suffix.lower(),
            "file_size_kb": round(stat.st_size / 1024, 2),
            "parent_folder": file_path.parent.name
        }