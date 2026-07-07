import numpy as np

from app.rag.embeddings import model

from app.rag.vector_store import VectorStore


store = VectorStore()


def search(
    question,
    top_k=5
):

    store.load()

    embedding = model.encode(
        [question],
        convert_to_numpy=True
    )

    distances, indices = store.index.search(
        embedding.astype("float32"),
        top_k
    )

    results = []

    for index in indices[0]:

        if index < len(store.documents):

            results.append(
                store.documents[index]
            )

    return results