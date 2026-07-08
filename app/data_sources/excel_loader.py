import pandas as pd

from langchain_core.documents import Document


def load_excel(file_path: str):
    """
    Load an Excel file and convert each row into a LangChain Document.
    """

    documents = []

    excel = pd.ExcelFile(file_path)

    for sheet in excel.sheet_names:

        dataframe = pd.read_excel(
            file_path,
            sheet_name=sheet
        )

        for index, row in dataframe.iterrows():

            content = "\n".join(
                f"{column}: {row[column]}"
                for column in dataframe.columns
            )

            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": file_path,
                        "sheet": sheet,
                        "row": index + 1
                    }
                )
            )

    return documents