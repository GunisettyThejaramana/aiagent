def search_documents(query):

    query_vector = get_embedding(query)

    D, I = index.search(
        np.array([query_vector]),
        k=3
    )

    return I