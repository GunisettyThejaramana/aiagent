from pathlib import Path

from bs4 import BeautifulSoup
from langchain.schema import Document


def load_html(path: str):
    """
    Load an HTML file and return LangChain Document objects.
    """

    html_path = Path(path)

    if not html_path.exists():
        print(f"HTML file not found: {html_path}")
        return []

    try:
        with open(html_path, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")

        # Extract visible text
        text = soup.get_text(separator="\n", strip=True)

        return [
            Document(
                page_content=text,
                metadata={
                    "source": str(html_path),
                    "file_type": "html"
                }
            )
        ]

    except Exception as e:
        print(f"Error loading HTML '{html_path}': {e}")
        return []