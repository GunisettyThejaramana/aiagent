from pathlib import Path


class TextParser:
    """
    Extracts text from plain text (.txt) files.
    """

    def parse(self, file_path: Path) -> str:
        """
        Read a text file and return its contents.

        Args:
            file_path (Path): Path to the text file.

        Returns:
            str: Extracted text.
        """

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                return file.read().strip()

        except Exception as e:
            print(f"[TEXT ERROR] {file_path}: {e}")
            return ""