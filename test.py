from app.custom_ai.document_knowledge_cache import document_knowledge_cache
from app.custom_ai.document_reasoning_engine import document_reasoning_engine


print("=" * 70)
print("DOCUMENT REASONING ENGINE TEST")
print("=" * 70)

print("\nLoading document cache...")

documents = document_knowledge_cache.get_documents()

print("Cached documents:", len(documents))

if not documents:
    print("ERROR: No documents found in cache.")
    raise SystemExit(1)


questions = [
    "What is mentioned about salary?",
    "What does the employee policy say about salary?",
    "What are the rules?",
    "What information is available about employees?",
]


for question in questions:

    print("\n" + "-" * 70)
    print("QUESTION:", question)
    print("-" * 70)

    result = document_reasoning_engine.process(
        question,
        documents,
    )

    print("\nSuccess:", result["success"])
    print("Matched:", result["matched"])
    print(
        "Matched documents:",
        result.get("matched_document_count", 0),
    )

    print("\nQuestion terms:")
    print(result.get("question_terms"))

    print("\nAnswer:")
    print(result["answer"])

    print("\nEvidence:")

    for index, item in enumerate(
        result.get("evidence", []),
        start=1,
    ):
        print(f"\n[{index}] Score: {item['score']}")
        print(item["text"])

        source = item.get("metadata", {}).get("source")

        if source:
            print("Source:", source)


print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)