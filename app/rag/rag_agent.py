from pathlib import Path

import numpy as np

from app.services.scanner_service import (
    scan_documents
)

from app.rag.chunker import (
    split_text
)

from app.rag.embeddings import (
    create_embeddings
)

from app.rag.vector_store import (
    VectorStore
)

from app.rag.loaders.pdf_loader import load_pdf
from app.rag.loaders.word_loader import load_word
from app.rag.loaders.excel_loader import load_excel
from app.rag.loaders.csv_loader import load_csv
from app.rag.loaders.txt_loader import load_txt
from app.rag.loaders.ppt_loader import load_ppt


def load_document(path):

    suffix = Path(path).suffix.lower()

    if suffix == ".pdf":
        return load_pdf(path)

    elif suffix in [".docx"]:
        return load_word(path)

    elif suffix in [".xlsx", ".xls"]:
        return load_excel(path)

    elif suffix == ".csv":
        return load_csv(path)

    elif suffix == ".txt":
        return load_txt(path)

    elif suffix == ".pptx":
        return load_ppt(path)

    return ""


def build_knowledge_base():

    files = scan_documents()

    all_chunks = []

    for file in files:

        text = load_document(
            file["path"]
        )

        chunks = split_text(text)

        all_chunks.extend(chunks)

    embeddings = create_embeddings(
        all_chunks
    )

    store = VectorStore()

    store.build(
        embeddings,
        all_chunks
    )

    store.save()

    return len(all_chunks)