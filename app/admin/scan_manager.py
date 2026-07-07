from app.services.scanner_service import scan_documents
from app.rag.rag_agent import build_knowledge_base


class ScanManager:

    def __init__(self):

        self.status = "Idle"

        self.total_files = 0

        self.total_chunks = 0

    def start_scan(self):

        self.status = "Scanning"

        documents = scan_documents()

        self.total_files = len(documents)

        self.total_chunks = build_knowledge_base()

        self.status = "Completed"

        return {
            "status": self.status,
            "files": self.total_files,
            "chunks": self.total_chunks
        }

    def get_status(self):

        return {
            "status": self.status,
            "files": self.total_files,
            "chunks": self.total_chunks
        }


scan_manager = ScanManager()