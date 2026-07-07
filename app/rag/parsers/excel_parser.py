from pathlib import Path
import pandas as pd


class ExcelParser:
    """
    Extracts text from Microsoft Excel (.xlsx) files.
    """

    def parse(self, file_path: Path) -> str:
        """
        Read all sheets from an Excel file and return as text.

        Args:
            file_path (Path): Path to the Excel file.

        Returns:
            str: Extracted text.
        """

        text = []

        try:
            excel_file = pd.ExcelFile(file_path)

            for sheet_name in excel_file.sheet_names:

                text.append(f"\n===== Sheet: {sheet_name} =====\n")

                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    dtype=str
                )

                df = df.fillna("")

                for _, row in df.iterrows():
                    row_text = " | ".join(
                        str(value).strip()
                        for value in row
                    )
                    text.append(row_text)

        except Exception as e:
            print(f"[EXCEL ERROR] {file_path}: {e}")

        return "\n".join(text)