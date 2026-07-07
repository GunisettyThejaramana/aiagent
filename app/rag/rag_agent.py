from openai import OpenAI

from app.config import settings
from app.rag.retriever import retriever


class RAGAgent:
    """
    Enterprise RAG Agent

    Retrieves relevant documents from the vector database
    and generates an answer using the LLM.
    """

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY
        )

    def answer(self, question: str) -> str:

        # Retrieve relevant documents
        documents = retriever.search_documents(
            question,
            k=5
        )

        if not documents:
            return "No relevant information found."

        # Build context
        context = "\n\n".join(
            doc.page_content
            for doc in documents
        )

        # System Prompt
        system_prompt = """
You are an Enterprise AI Assistant.

Answer only using the provided context.

If the answer is not available,
say:

"I couldn't find that information."

Do not make up answers.
"""

        # Call OpenAI
        response = self.client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {
                    "role": "system",
                    "content": system_prompt
                },

                {
                    "role": "user",
                    "content":
                    f"""
Context:

{context}

Question:

{question}
"""
                }
            ],

            temperature=0
        )

        return response.choices[0].message.content


rag_agent = RAGAgent()