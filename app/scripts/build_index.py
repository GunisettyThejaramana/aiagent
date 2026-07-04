from app.rag.document_loader import load_pdf
from app.rag.embeddings import get_embedding

docs = load_pdf("docs/hr_policy.pdf")

vectors = []

for doc in docs:
    vectors.append(
        get_embedding(doc.page_content)
    )

index.add(np.array(vectors))

faiss.write_index(
    index,
    "company_docs.index"
)