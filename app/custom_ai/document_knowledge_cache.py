from pathlib import Path
from threading import Lock
from typing import Dict, List, Any

from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class DocumentKnowledgeCache:
    """
    Caches documents loaded from the configured local scan paths.

    The cache prevents the application from scanning and loading
    every document again for every user question.
    """

    def __init__(self):
        self.drive_loader = LocalDriveLoader()
        self.detector = FileDetector()

        self._documents: List[Any] = []
        self._file_metadata: Dict[str, Dict[str, Any]] = {}

        self._initialized = False
        self._lock = Lock()

    # ============================================================
    # BUILD CACHE
    # ============================================================

    def build(self) -> List[Any]:
        """
        Scan configured folders and load all supported documents.

        Returns:
            List of loaded document objects.
        """

        with self._lock:

            files = self.drive_loader.scan()

            documents = []
            file_metadata = {}

            print("\n" + "=" * 60)
            print("BUILDING DOCUMENT KNOWLEDGE CACHE")
            print("=" * 60)

            print(f"Supported files found: {len(files)}")

            for file_path in files:

                try:

                    resolved_path = file_path.resolve()

                    docs = self.detector.load(
                        resolved_path
                    )

                    if not docs:
                        continue

                    documents.extend(docs)

                    stat = resolved_path.stat()

                    file_metadata[str(resolved_path)] = {
                        "path": str(resolved_path),
                        "name": resolved_path.name,
                        "suffix": resolved_path.suffix.lower(),
                        "size": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "document_count": len(docs),
                    }

                except Exception as exc:

                    print(
                        f"Document cache error "
                        f"for '{file_path}': {exc}"
                    )

            self._documents = documents
            self._file_metadata = file_metadata
            self._initialized = True

            print(
                f"Documents loaded into cache: "
                f"{len(self._documents)}"
            )

            print(
                f"Files cached: "
                f"{len(self._file_metadata)}"
            )

            print("=" * 60)

            return self._documents

    # ============================================================
    # GET DOCUMENTS
    # ============================================================

    def get_documents(self) -> List[Any]:
        """
        Return cached documents.

        Builds the cache automatically if it has not been built.
        """

        if not self._initialized:
            return self.build()

        return self._documents

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh(self) -> List[Any]:
        """
        Force a complete rebuild of the document cache.
        """

        print("\nRefreshing document knowledge cache...")

        return self.build()

    # ============================================================
    # CLEAR
    # ============================================================

    def clear(self):
        """
        Clear all cached documents and metadata.
        """

        with self._lock:

            self._documents.clear()
            self._file_metadata.clear()

            self._initialized = False

    # ============================================================
    # STATUS
    # ============================================================

    def is_ready(self) -> bool:
        """
        Return True if the cache has been built.
        """

        return self._initialized

    # ============================================================
    # DOCUMENT COUNT
    # ============================================================

    def document_count(self) -> int:
        """
        Return the number of loaded document chunks.
        """

        return len(self.get_documents())

    # ============================================================
    # FILE COUNT
    # ============================================================

    def file_count(self) -> int:
        """
        Return the number of source files in the cache.
        """

        if not self._initialized:
            self.build()

        return len(self._file_metadata)

    # ============================================================
    # FILE METADATA
    # ============================================================

    def get_file_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Return metadata for cached source files.
        """

        if not self._initialized:
            self.build()

        return self._file_metadata

    # ============================================================
    # CACHE INFO
    # ============================================================

    def get_info(self) -> Dict[str, Any]:
        """
        Return basic cache information.
        """

        if not self._initialized:
            self.build()

        return {
            "ready": self._initialized,
            "document_count": len(self._documents),
            "file_count": len(self._file_metadata),
            "scan_paths": [
                str(path)
                for path in self.drive_loader.get_scan_paths()
            ],
        }


# ================================================================
# GLOBAL CACHE INSTANCE
# ================================================================

document_knowledge_cache = DocumentKnowledgeCache()