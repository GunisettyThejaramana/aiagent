from app.services.scanner_service import scan_documents


def get_documents():

    return scan_documents()


def document_count():

    return len(
        scan_documents()
    )