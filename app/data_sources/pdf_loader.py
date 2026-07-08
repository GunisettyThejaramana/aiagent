from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path: str):
    """
    Load a searchable PDF.

    Parameters
    ----------
    file_path : str
        Path to the PDF file.

    Returns
    -------
    list
        List of LangChain Document objects.
    """

    try:
        loader = PyPDFLoader(file_path)
        return loader.load()

    except Exception:
        return []