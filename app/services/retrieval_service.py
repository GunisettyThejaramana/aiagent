from app.rag.retriever import search


def retrieve_documents(question):

    results = search(question)

    return results


def retrieve_context(question):

    documents = retrieve_documents(question)

    context = "\n\n".join(documents)

    return context