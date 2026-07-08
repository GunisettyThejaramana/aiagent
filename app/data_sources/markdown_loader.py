from pathlib import Path

from langchain.schema import Document


def load_markdown(path: str):
    """
    Load a Markdown (.md) file and return LangChain Document objects.
    """

    md_path = Path(path)

    if not md_path.exists():
        print(f"Markdown file not found: {md_path}")
        return []

    try:
        with open(md_path, "r", encoding="utf-8") as file:
            text = file.read()

        return [
            Document(
                page_content=text,
                metadata={
                    "source": str(md_path),
                    "file_type": "markdown"
                }
            )
        ]

    except Exception as e:
        print(f"Error loading Markdown '{md_path}': {e}")
        return []