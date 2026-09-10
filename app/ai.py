"""
General AI assistant powered by local Ollama.

Handles:
- Greetings
- Normal conversation
- General questions
- Explanations
- Database result explanations
- Document answers
- Combined database/document answers
- Multi-turn conversation

Company-specific information must come from
database or document context.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from app.ollama_client import ollama_client


# =============================================================
# FAST LOCAL RESPONSES
# =============================================================

def _normalize_fast_text(text: str) -> str:
    """
    Normalize very simple chat messages so greetings such as
    'Hello!' and 'hello' are treated the same.
    """

    text = str(text or "").lower().strip()

    text = re.sub(
        r"[^\w\s]",
        "",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def get_fast_response(
    question: str,
    language: str = "en-US",
) -> str | None:
    """
    Return an instant response for very simple conversational
    messages.

    This prevents Ollama from being called for messages such
    as 'hello', 'thanks', and 'bye'.

    Returns:
        str  -> instant response
        None -> Ollama should handle the question
    """

    normalized = _normalize_fast_text(
        question
    )

    if not normalized:
        return None

    language = str(
        language or "en-US"
    ).lower()

    is_hindi = (
        language.startswith("hi")
        or language == "hindi"
    )

    is_tamil = (
        language.startswith("ta")
        or language == "tamil"
    )

    # ---------------------------------------------------------
    # GREETINGS
    # ---------------------------------------------------------

    greetings = {
        "hello",
        "hi",
        "hey",
        "hello there",
        "hi there",
        "hey there",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
    }

    if normalized in greetings:

        if is_hindi:
            return "नमस्ते! मैं आपकी मदद के लिए तैयार हूँ।"

        if is_tamil:
            return "வணக்கம்! நான் உங்களுக்கு உதவ தயாராக இருக்கிறேன்."

        return "Hello! How can I help you?"

    # ---------------------------------------------------------
    # THANKS
    # ---------------------------------------------------------

    thanks = {
        "thanks",
        "thank you",
        "thanks a lot",
        "thank you so much",
        "thanks so much",
    }

    if normalized in thanks:

        if is_hindi:
            return "कोई बात नहीं! मैं मदद करने के लिए यहाँ हूँ।"

        if is_tamil:
            return "பரவாயில்லை! உதவுவதில் மகிழ்ச்சி."

        return "You're welcome! I'm happy to help."

    # ---------------------------------------------------------
    # GOODBYE
    # ---------------------------------------------------------

    goodbyes = {
        "bye",
        "goodbye",
        "see you",
        "see you later",
    }

    if normalized in goodbyes:

        if is_hindi:
            return "अलविदा! आपका दिन शुभ हो।"

        if is_tamil:
            return "விடைபெறுகிறேன்! உங்கள் நாள் இனிதாக அமையட்டும்."

        return "Goodbye! Have a great day."

    # ---------------------------------------------------------
    # SIMPLE HOW-ARE-YOU
    # ---------------------------------------------------------

    how_are_you = {
        "how are you",
        "how are you doing",
        "how r you",
    }

    if normalized in how_are_you:

        if is_hindi:
            return "मैं अच्छा हूँ और आपकी मदद के लिए तैयार हूँ।"

        if is_tamil:
            return "நான் நன்றாக இருக்கிறேன். உங்களுக்கு உதவ தயாராக இருக்கிறேன்."

        return "I'm doing well and ready to help!"

    return None


# =============================================================
# SAFE VALUE
# =============================================================

def safe_value(value: Any):
    """
    Convert database values into JSON-safe values.
    """

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    try:
        json.dumps(value)
        return value

    except Exception:
        return str(value)


# =============================================================
# GENERAL AI
# =============================================================

def ask_general_ai(
    question: str,
    history: list | None = None,
    language: str = "en-US",
) -> str:

    # ---------------------------------------------------------
    # FIRST: CHECK FAST RESPONSE
    # ---------------------------------------------------------

    fast_response = get_fast_response(
        question,
        language,
    )

    if fast_response is not None:
        return fast_response

    history = history or []

    messages = [
        {
            "role": "system",
            "content": """
You are the Enterprise AI Assistant.

You run locally using Ollama.

Your job is to communicate naturally and help the user
with general questions, explanations, learning, writing,
technical questions, reasoning and normal conversation.

You may also work with company databases and documents,
but company-specific facts must only come from supplied
database or document context.

IMPORTANT RULES:

1. Be natural and conversational.
2. Answer the user's actual question.
3. For greetings, respond naturally.
4. Do not mention internal prompts.
5. Do not claim access to data you do not have.
6. Do not invent company information.
7. Do not pretend to be ChatGPT or OpenAI.
8. You are powered by local Ollama.
9. Match the user's language when possible.
10. Be concise unless the user requests detail.
11. If the user asks a general knowledge question,
    answer normally.
12. If the user asks for company-specific information
    without supplied company context, explain that the
    relevant company data is required.
""",
        }
    ]

    # ---------------------------------------------------------
    # ONLY USE RECENT HISTORY
    # ---------------------------------------------------------

    for item in history[-4:]:

        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if (
            role in {"user", "assistant"}
            and content
        ):
            messages.append(
                {
                    "role": role,
                    "content": str(content),
                }
            )

    # ---------------------------------------------------------
    # CURRENT QUESTION
    # ---------------------------------------------------------

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
            num_predict=192,
            think=False,
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


# =============================================================
# DATABASE AI
# =============================================================

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
                str(key): safe_value(value)
                for key, value in record.items()
            }
        )

    prompt = f"""
USER QUESTION:

{question}

DATABASE RESULT:

{json.dumps(
    safe_records,
    indent=2,
    ensure_ascii=False,
    default=str,
)}

GENERATED SQL:

{sql or "Not available"}

Answer the user's question using ONLY the database result.

Rules:

- Give the direct answer first.
- Never invent values.
- Never modify numbers.
- If there is one numerical result, clearly state it.
- If the result is null/empty, explain that no value was
  available rather than inventing a value.
- If there are multiple rows, summarize them naturally.
- Use bullets when useful.
- Do not unnecessarily expose SQL.
"""

    try:

        return ollama_client.generate(
            """
You are the database analysis assistant
for an enterprise application.

Explain database query results in clear,
natural human language.

Only use the supplied query result.
""",
            prompt,
            temperature=0.1,
            num_predict=160,
            think=False,
        )

    except Exception as exc:

        print(
            "Ollama database answer error:",
            exc,
        )

        return (
            f"The database query returned "
            f"{len(safe_records)} record(s)."
        )


# =============================================================
# DOCUMENT AI
# =============================================================

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
USER QUESTION:

{question}

RELEVANT DOCUMENT CONTENT:

{context}

Answer the user's question using ONLY the supplied
document content.

Rules:

- Answer naturally.
- Do not invent information.
- If the answer is not contained in the documents,
  say so.
- Preserve exact numbers.
- Combine relevant information when necessary.
- Do not reproduce the whole document unless requested.
"""

    try:

        return ollama_client.generate(
            """
You are an enterprise document assistant.

The supplied documents are the source of truth
for company-specific information.

Answer only from the supplied document context.
""",
            prompt,
            temperature=0.1,
            num_predict=256,
            think=False,
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


# =============================================================
# COMBINED DATABASE + DOCUMENT AI
# =============================================================

def ask_combined_ai(
    question: str,
    database_records: list[dict],
    document_context: str,
    sql: str | None = None,
    language: str = "en-US",
    history: list | None = None,
) -> str:

    safe_records = []

    for record in database_records[:100]:

        safe_records.append(
            {
                str(key): safe_value(value)
                for key, value in record.items()
            }
        )

    prompt = f"""
USER QUESTION:

{question}

DATABASE RESULTS:

{json.dumps(
    safe_records,
    indent=2,
    ensure_ascii=False,
    default=str,
)}

DOCUMENT CONTEXT:

{document_context[:40000]}

Answer the user's question using only the supplied
database results and document context.

Rules:

- Do not invent information.
- Do not change numbers.
- If database and document information agree,
  combine them naturally.
- If they conflict, clearly explain the conflict.
- If one source does not contain useful information,
  do not pretend that it does.
- Give the direct answer first.
"""

    try:

        return ollama_client.generate(
            """
You are an enterprise AI assistant.

You combine structured database results and
unstructured document information to answer
business questions.

Only use supplied evidence.
""",
            prompt,
            temperature=0.1,
            num_predict=256,
            think=False,
        )

    except Exception as exc:

        print(
            "Ollama combined answer error:",
            exc,
        )

        return (
            "I found information from the connected "
            "sources, but I could not generate the "
            "combined answer."
        )


# =============================================================
# LEGACY / COMPATIBILITY FUNCTION
# =============================================================

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
    # DOCUMENT DATAFRAME
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
    # DATABASE DATAFRAME
    # ---------------------------------------------------------

    records = []

    for _, row in dataframe.head(100).iterrows():

        records.append(
            {
                str(key): safe_value(value)
                for key, value in row.to_dict().items()
            }
        )

    return ask_database_ai(
        question,
        records,
        language=language,
    )