from langchain_community.document_loaders import PyPDFLoader


def load_pdf(file_path: str):
    """
    Load a searchable PDF.
    """

    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        print(f"Loaded PDF: {file_path}")

        return docs

    except Exception as e:

        print(f"Failed to load {file_path}: {e}")

        return []