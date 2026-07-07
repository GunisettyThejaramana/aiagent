import faiss
import numpy as np

from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import embedding_generator

# ==========================================================
# Create FAISS Index
# ==========================================================

EMBEDDING_DIMENSION = 384

index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)

# Store original LangChain Documents
documents = []


class VectorStore:
    """
    Builds and manages the FAISS vector database.
    """

    def __init__(self):

        self.loader = DocumentLoader()

    def build_index(self):

        global documents

        print("Loading enterprise documents...")

        documents = self.loader.load_documents()

        print(f"{len(documents)} documents loaded.")

        vectors = []

        for doc in documents:

            embedding = embedding_generator.get_embedding(
                doc.page_content
            )

            vectors.append(embedding.astype(np.float32))

        if vectors:

            index.add(
                np.array(vectors)
            )

            print(f"{index.ntotal} vectors added.")

        else:

            print("No documents found.")

    def get_index(self):

        return index

    def get_documents(self):

        return documents


vector_store = VectorStore()