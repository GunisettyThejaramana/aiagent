import json
from pathlib import Path

from langchain.schema import Document


def load_json(path: str):
    """
    Load a JSON file and return LangChain Document objects.
    """

    json_path = Path(path)

    if not json_path.exists():
        print(f"JSON file not found: {json_path}")
        return []

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            content = json.dumps(data, indent=2)

        elif isinstance(data, list):
            content = "\n".join(
                json.dumps(item, indent=2)
                for item in data
            )

        else:
            content = str(data)

        return [
            Document(
                page_content=content,
                metadata={
                    "source": str(json_path),
                    "file_type": "json"
                }
            )
        ]

    except Exception as e:
        print(f"Error loading JSON '{json_path}': {e}")
        return []