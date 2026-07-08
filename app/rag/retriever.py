def retrieve_documents(question):
    docs = vectorstore.similarity_search(
        question,
        k=5
    )
    return docs