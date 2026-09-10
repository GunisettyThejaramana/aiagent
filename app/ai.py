"""
Generic AI answer generation.

This module deliberately contains no company-specific business
keywords or database column names.
"""

import json
from datetime import date, datetime
from decimal import Decimal

import pandas as pd




def _safe_value(
    value
):

    if isinstance(
        value,
        Decimal
    ):

        return float(
            value
        )

    if isinstance(
        value,
        (
            date,
            datetime
        )
    ):

        return value.isoformat()

    try:

        json.dumps(
            value
        )

        return value

    except Exception:

        return str(
            value
        )


def ask_llm(
    question: str,
    dataframe: pd.DataFrame,
    language="en-US"
):

    # ================================================================
    # EMPTY RESULT
    # ================================================================

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

    # ================================================================
    # DOCUMENT QUESTION
    # ================================================================

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

Do NOT copy large sections of the document unless the user explicitly
asks for the full text.

Do NOT invent information.

If the answer is not present in the supplied context, say that it
was not found.
"""

        user_prompt = f"""
USER QUESTION:

{question}

DOCUMENT CONTEXT:

{document_context}

Answer the question directly and concisely.
"""

        try:

            answer = (
                llm_client.generate(
                    system_prompt,
                    user_prompt
                )
            )

            if answer:

                return answer.strip()

        except Exception as exc:

            print(
                "Document answer generation failed:",
                exc
            )

        return (
            "I found relevant document content, "
            "but I could not generate a concise answer."
        )

    # ================================================================
    # DATABASE RESULT
    # ================================================================

    records = []

    for _, row in (
        dataframe.head(100)
        .iterrows()
    ):

        records.append(
            {
                str(key):
                    _safe_value(value)

                for (
                    key,
                    value
                )
                in row.to_dict().items()
            }
        )

    system_prompt = """
You are an enterprise data answer generator.

Answer the user's question using ONLY the supplied database result.

Do not invent facts.

Do not assume meanings that are not supported by the result.

Give a concise direct answer.
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

    try:

        answer = (
            llm_client.generate(
                system_prompt,
                user_prompt
            )
        )

        if answer:

            return answer.strip()

    except Exception as exc:

        print(
            "Database answer generation failed:",
            exc
        )

    # ================================================================
    # GENERIC FALLBACK
    # ================================================================

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
                f"The result is "
                f"{value:,}."
            )

        return (
            f"The result is "
            f"{value}."
        )

    return (
        f"I found {len(records)} "
        f"matching records."
    )