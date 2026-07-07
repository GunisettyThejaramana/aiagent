from sentence_transformers import SentenceTransformer
from typing import List

# Load the embedding model only once
model = SentenceTransformer("all-MiniLM-L6-v2")


class EmbeddingGenerator:
    """
    Generates embeddings for text or documents.
    """

    def get_embedding(self, text: str):
        """
        Generate embedding for a single text.
        """
        return model.encode(text)

    def get_embeddings(self, texts: List[str]):
        """
        Generate embeddings for multiple texts.
        """
        return model.encode(texts)

    def embed_documents(self, documents):
        """
        Generate embeddings for LangChain Document objects.

        Returns:
            List[dict]
        """

        embedded_documents = []

        for document in documents:

            embedding = self.get_embedding(
                document.page_content
            )

            embedded_documents.append(
                {
                    "embedding": embedding,
                    "document": document,
                }
            )

        return embedded_documents


# Singleton instance
embedding_generator = EmbeddingGenerator()