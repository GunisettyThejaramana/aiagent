import faiss
import numpy as np

from app.rag.document_loader import DocumentLoader
from app.rag.embeddings import embedding_generator


INDEX_FILE = "company_docs.index"
EMBEDDING_DIMENSION = 384


def build_index():
    """
    Build the FAISS index from all enterprise documents.
    """

    print("=" * 60)
    print("Building Enterprise AI Index...")
    print("=" * 60)

    # ---------------------------------------
    # Load Documents
    # ---------------------------------------

    loader = DocumentLoader()

    documents = loader.load_documents()

    print(f"Loaded {len(documents)} documents.")

    if not documents:
        print("No documents found.")
        return

    # ---------------------------------------
    # Generate Embeddings
    # ---------------------------------------

    vectors = []

    for document in documents:

        embedding = embedding_generator.get_embedding(
            document.page_content
        )

        vectors.append(
            embedding.astype(np.float32)
        )

    # ---------------------------------------
    # Create FAISS Index
    # ---------------------------------------

    index = faiss.IndexFlatL2(
        EMBEDDING_DIMENSION
    )

    index.add(
        np.array(vectors)
    )

    print(f"{index.ntotal} vectors indexed.")

    # ---------------------------------------
    # Save Index
    # ---------------------------------------

    faiss.write_index(
        index,
        INDEX_FILE
    )

    print(f"Index saved as '{INDEX_FILE}'")

    print("=" * 60)
    print("Index Build Completed Successfully")
    print("=" * 60)


if __name__ == "__main__":
    build_index()