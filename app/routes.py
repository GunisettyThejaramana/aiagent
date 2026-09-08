import pandas as pd

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.ai import ask_llm
from app.memory import add_message, get_memory

from app.agents.sales_agent import generate_sales_sql
from app.agents.hr_agent import generate_hr_sql
from app.agents.finance_agent import generate_finance_sql


from app.agents.router_agent import route_question

from app.services.search_service import SearchService

from app.database_manager import (
    create_database_engine_from_saved_connection
)

from app.agents.dynamic_sql_agent import (
    generate_dynamic_sql
)
router = APIRouter()

search_service = SearchService()


@router.get("/")
def home():
    return {
        "message": "Enterprise AI Assistant Running"
    }


@router.post("/sales")
def create_sale(
    sale: schemas.SalesCreate,
    db: Session = Depends(get_db)
):
    return crud.create_sale(db, sale)


@router.get("/sales")
def get_sales(
    db: Session = Depends(get_db)
):
    return crud.get_sales(db)


@router.post("/ask")
def ask_ai(
    request: schemas.QuestionRequest,
    db: Session = Depends(get_db)
):

    print("\n" + "=" * 60)
    print("🚀 NEW REQUEST")
    print("=" * 60)

    print(f"Question    : {request.question}")
    print(f"User ID     : {request.user_id}")
    print(f"Language    : {request.language}")
    print(f"Database ID : {request.database_id}")

    user_id = request.user_id

    add_message(
        user_id,
        "user",
        request.question
    )

    history = get_memory(user_id)

    # --------------------------------------------------
    # CASE 1:
    # User selected a database.
    # --------------------------------------------------

    if request.database_id is not None:

        selected_engine = None

        try:

            print(
                f"Connecting to database "
                f"{request.database_id}..."
            )

            selected_engine = (
                create_database_engine_from_saved_connection(
                    request.database_id
                )
            )

            print(
                "Selected database connection successful."
            )

            # ------------------------------------------
            # Generate SQL using actual database schema
            # ------------------------------------------

            sql = generate_dynamic_sql(
                request.question,
                selected_engine
            )

            print("Generated SQL:")
            print(sql)

            # ------------------------------------------
            # Execute SQL
            # ------------------------------------------

            dataframe = pd.read_sql(
                sql,
                selected_engine
            )

            print(
                f"Rows returned: {len(dataframe)}"
            )

            # ------------------------------------------
            # Generate natural-language answer
            # ------------------------------------------

            answer = ask_llm(
                request.question,
                dataframe,
                request.language
            )

            add_message(
                user_id,
                "assistant",
                answer
            )

            return {
                "source": "database",
                "data_source": "selected_database",
                "database_id": request.database_id,
                "question": request.question,
                "sql": sql,
                "answer": answer,
                "rows": dataframe.to_dict(
                    orient="records"
                ),
                "memory_count": len(history)
            }

        except ValueError as exc:

            print(
                f"Database validation error: {exc}"
            )

            raise HTTPException(
                status_code=400,
                detail=str(exc)
            )

        except Exception as exc:

            print(
                f"Database query error: {exc}"
            )

            raise HTTPException(
                status_code=400,
                detail=f"Database query failed: {str(exc)}"
            )

        finally:

            if selected_engine is not None:

                selected_engine.dispose()

    # --------------------------------------------------
    # CASE 2:
    # No database selected.
    #
    # Keep your existing application behavior.
    # --------------------------------------------------

    source = route_question(
        request.question
    )

    print(
        f"Detected Source : {source}"
    )

    if source == "documents":

        result = search_service.search_local_documents(
            request.question
        )

        documents = result["documents"]

        if documents:

            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )

            document_df = pd.DataFrame(
                {
                    "Document Content": [context]
                }
            )

            answer = ask_llm(
                request.question,
                document_df,
                request.language
            )

            add_message(
                user_id,
                "assistant",
                answer
            )

            return {
                "source": "documents",
                "data_source": "local_documents",
                "question": request.question,
                "sql": None,
                "answer": answer,
                "rows": [],
                "memory_count": len(history)
            }

        return {
            "source": "documents",
            "data_source": "local_documents",
            "question": request.question,
            "sql": None,
            "answer": "No matching local documents found.",
            "rows": [],
            "memory_count": len(history)
        }

    sql = None

    if source == "sales":

        sql = generate_sales_sql(
            request.question
        )

    elif source == "hr":

        sql = generate_hr_sql(
            request.question
        )

    elif source == "finance":

        sql = generate_finance_sql(
            request.question
        )

    elif source in [
        "operations",
        "inventory",
        "production"
    ]:

        sql = None

    else:

        sql = None

    if sql is None:

        result = search_service.search_local_documents(
            request.question
        )

        documents = result["documents"]

        if documents:

            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )

            document_df = pd.DataFrame(
                {
                    "Document Content": [context]
                }
            )

            answer = ask_llm(
                request.question,
                document_df,
                request.language
            )

            return {
                "source": source,
                "data_source": "local_documents",
                "question": request.question,
                "sql": None,
                "answer": answer,
                "rows": [],
                "memory_count": len(history)
            }

        return {
            "source": source,
            "data_source": "none",
            "question": request.question,
            "sql": None,
            "answer": "No information found.",
            "rows": [],
            "memory_count": len(history)
        }

    try:

        dataframe = pd.read_sql(
            sql,
            db.bind
        )

    except Exception as e:

        return {
            "source": source,
            "question": request.question,
            "sql": sql,
            "answer": f"SQL Error: {str(e)}",
            "rows": []
        }

    if dataframe.empty:

        result = search_service.search_local_documents(
            request.question
        )

        documents = result["documents"]

        if documents:

            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )

            document_df = pd.DataFrame(
                {
                    "Document Content": [context]
                }
            )

            answer = ask_llm(
                request.question,
                document_df,
                request.language
            )

            return {
                "source": source,
                "data_source": "local_documents",
                "question": request.question,
                "sql": sql,
                "answer": answer,
                "rows": [],
                "memory_count": len(history)
            }

    answer = ask_llm(
        request.question,
        dataframe,
        request.language
    )

    add_message(
        user_id,
        "assistant",
        answer
    )

    return {
        "source": source,
        "data_source": "database",
        "question": request.question,
        "sql": sql,
        "answer": answer,
        "rows": dataframe.to_dict(
            orient="records"
        ),
        "memory_count": len(history)
    }