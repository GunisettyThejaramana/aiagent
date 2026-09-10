"""
Generic AI answer generation.

This module deliberately contains no company-specific business
keywords or database column names.
"""

import json
from datetime import date, datetime
from decimal import Decimal

import pandas as pd


# ================================================================
# LLM CLIENT
# ================================================================
#
# Try to use the project's existing LLM client.
#
# The project may have the client in different locations depending
# on how the AI engine was created. We try the common locations
# without breaking the application if one is unavailable.
#

llm_client = None

try:
    from app.services.llm_client import llm_client
except Exception:
    try:
        from app.llm_client import llm_client
    except Exception:
        try:
            from app.custom_ai.llm_client import llm_client
        except Exception:
            llm_client = None


# ================================================================
# SAFE VALUE CONVERSION
# ================================================================

def _safe_value(value):
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


# ================================================================
# LLM GENERATION HELPER
# ================================================================

def _generate_with_llm(system_prompt, user_prompt):
    """
    Generate an answer using the configured LLM client.

    Returns:
        str | None

    If the LLM client is unavailable or generation fails,
    None is returned so that the caller can use a fallback.
    """

    if llm_client is None:
        print(
            "LLM client is not configured. "
            "Using fallback answer."
        )

        return None

    try:
        answer = llm_client.generate(
            system_prompt,
            user_prompt
        )

        if answer:
            return str(answer).strip()

    except Exception as exc:
        print(
            "LLM generation failed:",
            exc
        )

    return None


# ================================================================
# DOCUMENT FALLBACK
# ================================================================

def _document_fallback(
    question,
    dataframe
):
    """
    Basic fallback for document questions when an LLM is
    unavailable.

    This does not invent information. It returns the most
    relevant document content that was actually retrieved.
    """

    if (
        dataframe is None
        or dataframe.empty
        or "Document Content" not in dataframe.columns
    ):
        return (
            "I found relevant document content, "
            "but I could not generate a concise answer."
        )

    contents = (
        dataframe["Document Content"]
        .astype(str)
        .tolist()
    )

    if not contents:
        return (
            "I found relevant document content, "
            "but I could not generate a concise answer."
        )

    # Use the first relevant document.
    content = contents[0].strip()

    if not content:
        return (
            "I found relevant document content, "
            "but I could not generate a concise answer."
        )

    # Keep fallback response reasonably short.
    if len(content) > 1500:
        content = content[:1500].rstrip() + "..."

    return (
        "I found the following relevant information "
        "in the documents:\n\n"
        f"{content}"
    )


# ================================================================
# DATABASE FALLBACK
# ================================================================

def _database_fallback(records):
    """
    Basic fallback for database results when the LLM is unavailable.
    """

    if not records:
        return "No matching information was found."

    # One row + one column.
    if (
        len(records) == 1
        and len(records[0]) == 1
    ):
        value = next(
            iter(
                records[0].values()
            )
        )

        if isinstance(
            value,
            (int, float)
        ):
            return (
                f"The result is {value:,}."
            )

        return (
            f"The result is {value}."
        )

    # One row with multiple columns.
    if len(records) == 1:
        values = records[0]

        parts = []

        for key, value in values.items():
            if isinstance(
                value,
                (int, float)
            ):
                value_text = f"{value:,}"
            else:
                value_text = str(value)

            parts.append(
                f"{key}: {value_text}"
            )

        return "\n".join(parts)

    return (
        f"I found {len(records)} "
        f"matching records."
    )


# ================================================================
# MAIN AI ANSWER FUNCTION
# ================================================================

def ask_llm(
    question: str,
    dataframe: pd.DataFrame,
    language="en-US"
):
    """
    Generate an answer from either:

    1. Document search results
    2. Database query results

    The function automatically detects document results by looking
    for the "Document Content" column.
    """

    # ============================================================
    # EMPTY RESULT
    # ============================================================

    if (
        dataframe is None
        or dataframe.empty
    ):

        if language == "ta-IN":
            return (
                "தகவல் எதுவும் கிடைக்கவில்லை."
            )

        if language == "hi-IN":
            return (
                "कोई जानकारी नहीं मिली।"
            )

        return (
            "No matching information was found."
        )

    # ============================================================
    # DOCUMENT QUESTION
    # ============================================================

    if (
        "Document Content"
        in dataframe.columns
    ):

        document_context = "\n\n".join(
            dataframe[
                "Document Content"
            ]
            .astype(str)
            .tolist()
        )

        # Prevent unnecessarily huge prompts.
        document_context = (
            document_context[:30000]
        )

        system_prompt = """
You are an enterprise document question-answering assistant.

Use ONLY the supplied document context.

Answer the user's actual question directly.

Do NOT return the entire document.

Do NOT copy large sections of the document unless the user
explicitly asks for the full text.

Do NOT invent information.

If the answer is not present in the supplied context, say that
it was not found.

For numerical questions, give the exact value found in the
document.

Keep the answer concise.
"""

        user_prompt = f"""
USER QUESTION:

{question}

DOCUMENT CONTEXT:

{document_context}

Answer the question directly and concisely.
"""

        # --------------------------------------------------------
        # TRY LLM
        # --------------------------------------------------------

        answer = _generate_with_llm(
            system_prompt,
            user_prompt
        )

        if answer:
            return answer

        # --------------------------------------------------------
        # FALLBACK
        # --------------------------------------------------------

        print(
            "Using document content fallback."
        )

        return _document_fallback(
            question,
            dataframe
        )

    # ============================================================
    # DATABASE RESULT
    # ============================================================

    records = []

    for _, row in (
        dataframe
        .head(100)
        .iterrows()
    ):

        records.append(
            {
                str(key):
                    _safe_value(value)

                for key, value
                in row.to_dict().items()
            }
        )

    # ============================================================
    # DATABASE SYSTEM PROMPT
    # ============================================================

    system_prompt = """
You are an enterprise data answer generator.

Answer the user's question using ONLY the supplied database result.

Do not invent facts.

Do not assume meanings that are not supported by the result.

Give a concise direct answer.

For numerical results, clearly show the number.

If the result contains a single value, answer with that value
directly rather than explaining the database query.
"""

    user_prompt = f"""
USER QUESTION:

{question}

DATABASE RESULT:

{json.dumps(
    records,
    indent=2,
    default=str
)}

Answer directly.
"""

    # ============================================================
    # TRY LLM
    # ============================================================

    answer = _generate_with_llm(
        system_prompt,
        user_prompt
    )

    if answer:
        return answer

    # ============================================================
    # DATABASE FALLBACK
    # ============================================================

    print(
        "Using database result fallback."
    )

    return _database_fallback(
        records
    )