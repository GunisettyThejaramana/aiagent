import faiss
import numpy as np
import pickle


class VectorStore:

    def __init__(self):

        self.index = None

        self.documents = []

    def build(
        self,
        embeddings,
        documents
    ):

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(
            dimension
        )

        self.index.add(
            embeddings.astype("float32")
        )

        self.documents = documents

    def save(self):

        faiss.write_index(
            self.index,
            "vector_db/faiss.index"
        )

        with open(
            "vector_db/documents.pkl",
            "wb"
        ) as file:

            pickle.dump(
                self.documents,
                file
            )

    def load(self):

        self.index = faiss.read_index(
            "vector_db/faiss.index"
        )

        with open(
            "vector_db/documents.pkl",
            "rb"
        ) as file:

            self.documents = pickle.load(
                file
            )