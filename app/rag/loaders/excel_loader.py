import pandas as pd


def load_excel(file_path):

    excel = pd.ExcelFile(file_path)

    text = ""

    for sheet in excel.sheet_names:

        df = pd.read_excel(
            file_path,
            sheet_name=sheet
        )

        text += f"\nSheet : {sheet}\n"

        text += df.to_string(index=False)

    return text