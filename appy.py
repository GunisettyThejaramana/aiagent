from app.services.search_service import SearchService

service = SearchService()

documents = service.search_local_documents()

print(len(documents))

for doc in documents[:5]:
    print(doc.metadata)