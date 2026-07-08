from langchain_community.document_loaders import Docx2txtLoader


def load_word(file_path: str):
    """
    Load a Word document and return LangChain Documents.
    """

    loader = Docx2txtLoader(file_path)

    return loader.load()