from langchain_core.documents import Document


def load_text(file_path: str):
    """
    Load a text file and return a LangChain Document.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8",
        errors="ignore"
    ) as file:

        content = file.read()

    return [
        Document(
            page_content=content,
            metadata={
                "source": file_path
            }
        )
    ]