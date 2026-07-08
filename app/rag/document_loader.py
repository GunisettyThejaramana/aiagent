from langchain.document_loaders import PyPDFLoader

def load_pdf(path):

    loader = PyPDFLoader(path)

    docs = loader.load()

    return docs