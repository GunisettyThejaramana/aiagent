from app.indexing.document_index import DocumentIndex

index = DocumentIndex()

documents = index.build()

print(f"Indexed {len(documents)} documents.")