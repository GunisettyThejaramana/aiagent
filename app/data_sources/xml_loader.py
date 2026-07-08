import xml.etree.ElementTree as ET
from pathlib import Path

from langchain.schema import Document


def load_xml(path: str):
    """
    Load an XML file and return LangChain Document objects.
    """

    xml_path = Path(path)

    if not xml_path.exists():
        print(f"XML file not found: {xml_path}")
        return []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        content = []

        for element in root.iter():
            if element.text and element.text.strip():
                content.append(element.text.strip())

        text = "\n".join(content)

        return [
            Document(
                page_content=text,
                metadata={
                    "source": str(xml_path),
                    "file_type": "xml"
                }
            )
        ]

    except Exception:
       return []