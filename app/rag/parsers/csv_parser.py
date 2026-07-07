from pathlib import Path
import pandas as pd


class CSVParser:
    """
    Extracts text from CSV files.
    """

    def parse(self, file_path: Path) -> str:
        """
        Read a CSV file and convert it into plain text.

        Args:
            file_path (Path): Path to the CSV file.

        Returns:
            str: Extracted text.
        """

        text = []

        try:
            df = pd.read_csv(
                file_path,
                dtype=str
            )

            df = df.fillna("")

            # Add column names
            text.append(" | ".join(df.columns))

            # Add rows
            for _, row in df.iterrows():
                row_text = " | ".join(
                    str(value).strip()
                    for value in row
                )

                text.append(row_text)

        except Exception as e:
            print(f"[CSV ERROR] {file_path}: {e}")

        return "\n".join(text)