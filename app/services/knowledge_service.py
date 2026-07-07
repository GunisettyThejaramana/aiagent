from app.services.document_service import (
    get_documents
)


def knowledge_status():

    docs = get_documents()

    return {
        "total_documents": len(docs),
        "status": "Ready"
    }