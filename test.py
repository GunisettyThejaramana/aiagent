from app.custom_ai.business_language_engine import (
    business_language_engine,
)

from app.custom_ai.business_context_engine import (
    business_context_engine,
)


questions = [
    "Who has the highest outstanding balance?",
    "Show the workers with the biggest advance",
    "Which employees have the highest salary?",
    "How much inventory do we have?",
    "What is the total credit?",
    "What is the total debit?",
    "What was the revenue last month?",
    "How many sarees were produced?",
]


for question in questions:

    print("=" * 70)

    print("QUESTION:")
    print(question)

    language_result = (
        business_language_engine.understand(
            question
        )
    )

    context_result = (
        business_context_engine.understand(
            question=question,
            business_language_result=language_result,
        )
    )

    print("\nCONTEXTS:")

    for context in context_result["contexts"]:

        print(
            f"\nConcept: {context['concept']}"
        )

        print(
            f"Meaning: {context['meaning']}"
        )

        print(
            f"Confidence: {context['confidence']}"
        )

        print(
            f"Matched context: "
            f"{context['matched_context']}"
        )

        print(
            "Preferred columns:",
            context[
                "preferred_column_keywords"
            ],
        )

        print(
            "Preferred tables:",
            context[
                "preferred_table_keywords"
            ],
        )

        print(
            "Avoid tables:",
            context[
                "avoid_table_keywords"
            ],
        )

        print(
            "Avoid columns:",
            context[
                "avoid_column_keywords"
            ],
        )