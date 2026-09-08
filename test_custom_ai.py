from app.custom_ai.custom_ai_engine import custom_ai_engine
from app.database_manager import create_database_engine_from_saved_connection


DATABASE_ID = 2

questions = [
    
    
    "Which employees have the highest salary?",
    "How much inventory do we have?",
    
    "What is the total debit?",
    "How many sarees were produced?",
]


engine = None

try:
    print("=" * 70)
    print("CUSTOM ENTERPRISE AI - FULL PIPELINE TEST")
    print("=" * 70)

    print(f"\nConnecting to database ID: {DATABASE_ID}")

    engine = create_database_engine_from_saved_connection(DATABASE_ID)

    print("Database connection successful.")
    print()

    for question in questions:

        print("=" * 70)
        print("QUESTION:")
        print(question)
        print("=" * 70)

        try:
            result = custom_ai_engine.answer(
                question=question,
                engine=engine,
            )

            print("\nINTENT:")
            print(result["intent"])

            print("\nENTITIES:")
            print(result["entities"])

            print("\nMETRICS:")
            print(result["metrics"])

            print("\nBUSINESS CONTEXT:")
            for context in result["business_context"].get("contexts", []):
                print(
                    f"  {context.get('concept')} "
                    f"→ {context.get('meaning')}"
                )

            print("\nREASONING:")
            print(result["reasoning"])

            print("\nPLAN:")
            print(result["plan"])

            print("\nGENERATED SQL:")
            print(result["sql"])

            print("\nEXECUTION:")
            print(result["execution"])

            print("\nFINAL ANSWER:")
            print(result["answer"])

        except Exception as exc:

            print("\nERROR:")
            print(type(exc).__name__)
            print(str(exc))

        print()

finally:

    if engine is not None:
        engine.dispose()

    print("=" * 70)
    print("TEST FINISHED")
    print("=" * 70)