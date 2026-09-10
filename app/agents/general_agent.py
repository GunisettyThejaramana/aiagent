"""
General Agent
Handles questions that do not clearly belong to a specific domain
(HR, Finance, Sales, Operations, Inventory, Production).

It can:
- Use dynamic SQL generation when a database engine is available
- Fall back to a helpful natural language response
"""

from typing import Optional, Any
from sqlalchemy.engine import Engine

from app.agents.dynamic_sql_agent import generate_sql
from app.llm.client import llm_client


def generate_general_sql(question: str, engine: Optional[Engine] = None) -> str:
    """
    Generate a safe SQL query for a general question.
    Falls back to dynamic SQL agent when an engine is provided.
    """
    if engine is not None:
        try:
            return generate_sql(question, engine)
        except Exception as e:
            print(f"[GeneralAgent] Dynamic SQL failed: {e}")

    # Fallback safe query
    return "SELECT 1 AS placeholder;"


def answer_general_question(
    question: str,
    context: Optional[str] = None,
    language: str = "en-US"
) -> str:
    """
    Generate a natural language answer for general / out-of-domain questions.
    """
    system_prompt = """
You are a helpful Enterprise AI Assistant.
Answer the user's question clearly and professionally.
If the question is about company data but no specific data is provided,
politely explain that you need more context or a connected database.
Keep the answer concise.
"""

    user_prompt = f"Question: {question}"
    if context:
        user_prompt += f"\n\nAdditional context:\n{context}"

    try:
        answer = llm_client.generate(system_prompt, user_prompt)
        return answer
    except Exception as e:
        if language == "ta-IN":
            return "மன்னிக்கவும், தற்போது பதில் அளிக்க முடியவில்லை."
        if language == "hi-IN":
            return "क्षमा करें, इस समय उत्तर नहीं दे पा रहा हूँ।"
        return f"Sorry, I could not generate an answer right now. ({str(e)})"


def handle_general(
    question: str,
    engine: Optional[Engine] = None,
    language: str = "en-US"
) -> dict[str, Any]:
    """
    Main entry point for the general agent.
    Returns a structured response.
    """
    sql = None
    data = []
    answer = ""

    if engine is not None:
        try:
            sql = generate_general_sql(question, engine)
            # Note: actual execution is usually done by the caller / sql_executor
        except Exception:
            sql = None

    answer = answer_general_question(question, language=language)

    return {
        "agent": "general",
        "answer": answer,
        "sql": sql,
        "data": data,
        "success": True
    }