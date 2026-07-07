from pathlib import Path

from app.admin.settings import load_settings


def scan_documents():

    settings = load_settings()

    knowledge_path = settings["knowledge_path"]

    supported_extensions = [
        ext.lower()
        for ext in settings["supported_extensions"]
    ]

    if not knowledge_path:

        raise Exception(
            "Knowledge folder is not configured."
        )

    root = Path(knowledge_path)

    if not root.exists():

        raise FileNotFoundError(
            f"{knowledge_path} does not exist."
        )

    documents = []

    for file in root.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower()
            in supported_extensions
        ):

            documents.append(
                {
                    "name": file.name,
                    "path": str(file),
                    "extension": file.suffix,
                    "size": file.stat().st_size
                }
            )

    return documents