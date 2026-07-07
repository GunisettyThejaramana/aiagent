from pathlib import Path

from app.admin.settings import (
    load_settings,
    save_settings
)


def set_knowledge_folder(folder_path: str):

    folder = Path(folder_path)

    if not folder.exists():

        raise FileNotFoundError(
            "Knowledge folder does not exist."
        )

    settings = load_settings()

    settings["knowledge_path"] = str(folder)

    save_settings(settings)

    return settings


def get_knowledge_folder():

    settings = load_settings()

    return settings.get(
        "knowledge_path",
        ""
    )