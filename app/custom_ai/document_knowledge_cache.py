from pathlib import Path
from threading import Lock
from typing import Dict, List, Any, Optional


from app.data_sources.local_drive_loader import LocalDriveLoader
from app.data_sources.file_detector import FileDetector


class DocumentKnowledgeCache:
    """
    Caches documents loaded from the configured local scan paths.

    Responsibilities:
        1. Scan configured local folders.
        2. Detect and load supported documents.
        3. Keep loaded document chunks in memory.
        4. Keep metadata about the source files.
        5. Provide fast access to cached documents.

    This class intentionally does NOT generate LLM answers.

    Document retrieval and LLM answer generation are handled
    separately by the application services.
    """

    def __init__(self):

        self.drive_loader = LocalDriveLoader()
        self.detector = FileDetector()

        # Cached document chunks
        self._documents: List[Any] = []

        # Metadata indexed by absolute file path
        self._file_metadata: Dict[str, Dict[str, Any]] = {}

        # Cache state
        self._initialized = False

        # Protect cache operations from concurrent requests
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

            print("\n" + "=" * 60)
            print("BUILDING DOCUMENT KNOWLEDGE CACHE")
            print("=" * 60)

            # ----------------------------------------------------
            # Scan configured paths
            # ----------------------------------------------------

            try:

                files = self.drive_loader.scan()

            except Exception as exc:

                print(
                    "Document scan failed:",
                    exc
                )

                self._documents = []
                self._file_metadata = {}
                self._initialized = True

                print("=" * 60)

                return []

            print(
                f"Supported files found: {len(files)}"
            )

            documents: List[Any] = []

            file_metadata: Dict[
                str,
                Dict[str, Any]
            ] = {}

            # ----------------------------------------------------
            # Load every supported file
            # ----------------------------------------------------

            for file_path in files:

                try:

                    # Convert to Path in case the loader
                    # returns a string.
                    resolved_path = Path(
                        file_path
                    ).resolve()

                    # ------------------------------------------------
                    # Load document
                    # ------------------------------------------------

                    docs = self.detector.load(
                        resolved_path
                    )

                    if not docs:

                        print(
                            f"Skipped empty document: "
                            f"{resolved_path}"
                        )

                        continue

                    # ------------------------------------------------
                    # Add document chunks
                    # ------------------------------------------------

                    documents.extend(docs)

                    # ------------------------------------------------
                    # File statistics
                    # ------------------------------------------------

                    try:

                        stat = resolved_path.stat()

                        size = stat.st_size
                        modified_time = stat.st_mtime

                    except OSError:

                        size = 0
                        modified_time = 0

                    # ------------------------------------------------
                    # Store metadata
                    # ------------------------------------------------

                    file_metadata[
                        str(resolved_path)
                    ] = {

                        "path": str(
                            resolved_path
                        ),

                        "name": resolved_path.name,

                        "suffix": (
                            resolved_path
                            .suffix
                            .lower()
                        ),

                        "size": size,

                        "modified_time": (
                            modified_time
                        ),

                        "document_count": len(
                            docs
                        ),
                    }

                except Exception as exc:

                    print(
                        "Document cache error "
                        f"for '{file_path}': {exc}"
                    )

            # ----------------------------------------------------
            # Replace cache atomically
            # ----------------------------------------------------

            self._documents = documents

            self._file_metadata = file_metadata

            self._initialized = True

            # ----------------------------------------------------
            # Cache statistics
            # ----------------------------------------------------

            print(
                f"Documents loaded into cache: "
                f"{len(self._documents)}"
            )

            print(
                f"Files cached: "
                f"{len(self._file_metadata)}"
            )

            print("=" * 60)

            return list(self._documents)

    # ============================================================
    # GET DOCUMENTS
    # ============================================================

    def get_documents(self) -> List[Any]:
        """
        Return cached documents.

        Builds the cache automatically if it has not
        already been initialized.
        """

        if not self._initialized:

            self.build()

        with self._lock:

            return list(
                self._documents
            )

    # ============================================================
    # REFRESH
    # ============================================================

    def refresh(self) -> List[Any]:
        """
        Force a complete rebuild of the document cache.
        """

        print(
            "\nRefreshing document knowledge cache..."
        )

        return self.build()

    # ============================================================
    # CLEAR
    # ============================================================

    def clear(self):
        """
        Clear all cached documents and metadata.
        """

        with self._lock:

            self._documents = []

            self._file_metadata = {}

            self._initialized = False

        print(
            "Document knowledge cache cleared."
        )

    # ============================================================
    # STATUS
    # ============================================================

    def is_ready(self) -> bool:
        """
        Return True if the cache has been built.
        """

        with self._lock:

            return self._initialized

    # ============================================================
    # DOCUMENT COUNT
    # ============================================================

    def document_count(self) -> int:
        """
        Return the number of loaded document chunks.
        """

        if not self._initialized:

            self.build()

        with self._lock:

            return len(
                self._documents
            )

    # ============================================================
    # FILE COUNT
    # ============================================================

    def file_count(self) -> int:
        """
        Return the number of source files in the cache.
        """

        if not self._initialized:

            self.build()

        with self._lock:

            return len(
                self._file_metadata
            )

    # ============================================================
    # FILE METADATA
    # ============================================================

    def get_file_metadata(
        self
    ) -> Dict[str, Dict[str, Any]]:
        """
        Return metadata for cached source files.
        """

        if not self._initialized:

            self.build()

        with self._lock:

            return dict(
                self._file_metadata
            )

    # ============================================================
    # GET SOURCE METADATA
    # ============================================================

    def get_source_metadata(
        self,
        source: str
    ) -> Optional[Dict[str, Any]]:
        """
        Return metadata for a specific source file.

        Args:
            source:
                Absolute or relative source path.

        Returns:
            Metadata dictionary if found, otherwise None.
        """

        if not self._initialized:

            self.build()

        if not source:

            return None

        try:

            normalized_source = str(
                Path(source).resolve()
            )

        except Exception:

            normalized_source = str(
                source
            )

        with self._lock:

            metadata = self._file_metadata.get(
                normalized_source
            )

            if metadata:

                return dict(
                    metadata
                )

            # ----------------------------------------------------
            # Fallback: compare normalized strings
            # ----------------------------------------------------

            normalized_source_lower = (
                normalized_source.lower()
            )

            for path, data in (
                self._file_metadata.items()
            ):

                if (
                    str(path).lower()
                    == normalized_source_lower
                ):

                    return dict(
                        data
                    )

        return None

    # ============================================================
    # SCAN PATHS
    # ============================================================

    def get_scan_paths(self) -> List[str]:
        """
        Return configured document scan paths.
        """

        try:

            paths = (
                self.drive_loader
                .get_scan_paths()
            )

            return [
                str(path)
                for path in paths
            ]

        except Exception as exc:

            print(
                "Unable to read document scan paths:",
                exc
            )

            return []

    # ============================================================
    # CACHE INFO
    # ============================================================

    def get_info(self) -> Dict[str, Any]:
        """
        Return basic cache information.
        """

        if not self._initialized:

            self.build()

        with self._lock:

            return {
                "ready": self._initialized,

                "document_count": len(
                    self._documents
                ),

                "file_count": len(
                    self._file_metadata
                ),

                "scan_paths": self.get_scan_paths(),
            }


# ================================================================
# GLOBAL CACHE INSTANCE
# ================================================================

document_knowledge_cache = DocumentKnowledgeCache()