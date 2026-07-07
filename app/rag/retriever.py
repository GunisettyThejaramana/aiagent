from typing import List

from langchain_core.documents import Document

from app.rag.vector_store import vectorstore


class Retriever:
    """
    Retrieves relevant documents from the vector store.
    """

    def __init__(self):
        self.vectorstore = vectorstore

    def retrieve_documents(
        self,
        question: str,
        k: int = 5
    ) -> List[Document]:
        """
        Retrieve the top-k relevant documents.

        Args:
            question (str): User query.
            k (int): Number of documents to retrieve.

        Returns:
            List[Document]
        """

        documents = self.vectorstore.similarity_search(
            query=question,
            k=k
        )

        return documents


retriever = Retriever()