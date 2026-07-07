import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

CONFIG_FILE = BASE_DIR / "config" / "settings.json"


def load_settings():

    with open(CONFIG_FILE, "r") as file:

        return json.load(file)


def save_settings(data):

    with open(CONFIG_FILE, "w") as file:

        json.dump(
            data,
            file,
            indent=4
        )