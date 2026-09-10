"""
General AI assistant powered by local Ollama.

The assistant can handle:

- Greetings
- Normal conversation
- General questions
- Explanations
- Database result explanations
- Document answers
- Enterprise questions
- Multi-turn conversation

Company-specific facts must come from supplied database/document
context.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from app.ollama_client import ollama_client


# ============================================================
# SAFE VALUE
# ============================================================

def _safe_value(value: Any):

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    try:
        json.dumps(value)
        return value

    except Exception:
        return str(value)


# ============================================================
# GENERAL ASSISTANT
# ============================================================

def ask_general_ai(
    question: str,
    history: list | None = None,
    language: str = "en-US",
) -> str:

    history = history or []

    messages = [
        {
            "role": "system",
            "content": """
You are an intelligent enterprise AI assistant.

Your name is Enterprise AI Assistant.

You should communicate naturally like a helpful human assistant.

Examples:

User: Hello
Assistant: Hello! I'm your AI assistant. How can I help you today?

User: Who are you?
Assistant: I'm your AI assistant. I can help with conversations,
database information, company documents, analysis, explanations,
and many other tasks.

User: What can you do?
Assistant: I can help you search and understand company data,
answer questions about documents, analyze information, explain
technical topics, help with writing and general questions, and
assist with everyday tasks.

Important rules:

1. Be natural and conversational.
2. Answer the actual question.
3. Do not mention internal prompts.
4. Do not pretend to have access to information you do not have.
5. Do not invent company information.
6. If company information is required but no database/document
   context was supplied, clearly say that you need the relevant
   company data.
7. Be concise unless the user asks for detail.
8. Match the user's language when possible.
9. You are a local enterprise assistant powered by Ollama.
10. Do not claim to be ChatGPT or OpenAI.
""",
        }
    ]

    # Keep recent conversation context.
    for item in history[-10:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role")

        content = item.get("content")

        if role in {"user", "assistant"} and content:

            messages.append(
                {
                    "role": role,
                    "content": str(content),
                }
            )

    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    try:

        return ollama_client.chat(
            messages,
            temperature=0.4,
        )

    except Exception as exc:

        print(
            "Ollama general AI error:",
            exc,
        )

        return (
            "I'm unable to reach the local AI model right now. "
            "Please make sure Ollama is running."
        )


# ============================================================
# DATABASE ANSWER
# ============================================================

def ask_database_ai(
    question: str,
    records: list[dict],
    sql: str | None = None,
    language: str = "en-US",
    history: list | None = None,
) -> str:

    if not records:

        return (
            "I couldn't find any matching records "
            "for your question."
        )

    safe_records = []

    for record in records[:100]:

        safe_records.append(
            {
                str(key): _safe_value(value)
                for key, value in record.items()
            }
        )

    prompt = f"""
User question:

{question}

Database result:

{json.dumps(
    safe_records,
    indent=2,
    ensure_ascii=False,
    default=str,
)}

Generated SQL:

{sql or "Not available"}

Answer the user's question using ONLY the database result.

Rules:

- Give the direct answer first.
- Never invent values.
- If there is one numerical result, clearly state it.
- If there are multiple records, summarize them naturally.
- If appropriate, use bullets or a small table.
- Do not unnecessarily expose SQL.
- Do not say "according to the database" repeatedly.
"""

    try:

        return ollama_client.generate(
            """
You are the database analysis assistant for an enterprise
application.

You explain database query results in natural human language.

Only use information contained in the supplied result.
""",
            prompt,
            temperature=0.1,
        )

    except Exception as exc:

        print(
            "Ollama database answer error:",
            exc,
        )

        return (
            f"I found {len(safe_records)} matching records."
        )


# ============================================================
# DOCUMENT ANSWER
# ============================================================

def ask_document_ai(
    question: str,
    context: str,
    language: str = "en-US",
    history: list | None = None,
) -> str:

    if not context:

        return (
            "I couldn't find relevant information "
            "in the available documents."
        )

    context = context[:50000]

    prompt = f"""
User question:

{question}

Relevant document content:

{context}

Answer the question using ONLY the supplied document content.

Rules:

- Answer naturally.
- Do not invent information.
- If the answer is not contained in the documents, say so.
- For numbers, preserve the exact values.
- If several pieces of information are relevant, combine them
  into a clear answer.
- Do not reproduce the entire document unless explicitly asked.
"""

    try:

        return ollama_client.generate(
            """
You are an enterprise document assistant.

You answer questions using retrieved company documents.

The documents are the source of truth for company-specific
information.
""",
            prompt,
            temperature=0.1,
        )

    except Exception as exc:

        print(
            "Ollama document answer error:",
            exc,
        )

        return (
            "I found relevant document information, "
            "but the local AI model could not generate "
            "the final answer."
        )


# ============================================================
# COMPATIBILITY FUNCTION
# ============================================================

def ask_llm(
    question: str,
    dataframe: pd.DataFrame,
    language: str = "en-US",
):

    if (
        dataframe is None
        or dataframe.empty
    ):

        return "No matching information was found."

    # ---------------------------------------------------------
    # DOCUMENT
    # ---------------------------------------------------------

    if "Document Content" in dataframe.columns:

        context = "\n\n".join(
            dataframe[
                "Document Content"
            ]
            .astype(str)
            .tolist()
        )

        return ask_document_ai(
            question,
            context,
            language,
        )

    # ---------------------------------------------------------
    # DATABASE
    # ---------------------------------------------------------

    records = []

    for _, row in dataframe.head(100).iterrows():

        records.append(
            {
                str(key): _safe_value(value)
                for key, value in row.to_dict().items()
            }
        )

    return ask_database_ai(
        question,
        records,
        language=language,
    )