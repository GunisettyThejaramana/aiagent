import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings
from app.scripts.build_index import build_index


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".csv",
    ".pptx",
    ".txt",
}


class CompanyFileWatcher(FileSystemEventHandler):
    """
    Watches company folders and rebuilds the vector index
    whenever supported files change.
    """

    def _should_process(self, file_path: str) -> bool:
        """
        Check whether the changed file is supported.
        """
        extension = Path(file_path).suffix.lower()

        return extension in SUPPORTED_EXTENSIONS

    def on_created(self, event):

        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        print(f"\n[NEW FILE] {event.src_path}")

        build_index()

    def on_modified(self, event):

        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        print(f"\n[MODIFIED] {event.src_path}")

        build_index()

    def on_deleted(self, event):

        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        print(f"\n[DELETED] {event.src_path}")

        build_index()


def start_file_watcher():
    """
    Start monitoring all configured company folders.
    """

    observer = Observer()

    handler = CompanyFileWatcher()

    for folder in settings.document_paths:

        folder_path = Path(folder)

        if not folder_path.exists():
            print(f"[WARNING] Folder not found: {folder}")
            continue

        observer.schedule(
            handler,
            str(folder_path),
            recursive=True
        )

        print(f"Watching: {folder_path}")

    observer.start()

    print("\nCompany File Watcher Started...\n")

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        observer.stop()

    observer.join()


if __name__ == "__main__":
    start_file_watcher()