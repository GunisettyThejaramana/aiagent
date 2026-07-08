import pandas as pd

from langchain_core.documents import Document


def load_csv(file_path: str):
    """
    Load a CSV file and convert each row into a LangChain Document.
    """

    dataframe = pd.read_csv(file_path)

    documents = []

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
                    "row": index + 1
                }
            )
        )

    return documents