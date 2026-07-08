import pandas as pd

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database import get_db

from app import crud
from app import schemas

from app.ai import ask_llm

from app.memory import (
    add_message,
    get_memory
)

from app.agents.sales_agent import generate_sales_sql
from app.agents.hr_agent import generate_hr_sql
from app.agents.finance_agent import generate_finance_sql
from app.agents.router_agent import route_question

# NEW
from app.services.search_service import SearchService


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

    print(f"Question : {request.question}")
    print(f"User ID  : {request.user_id}")
    print(f"Language : {request.language}")

    user_id = request.user_id

    add_message(
        user_id,
        "user",
        request.question
    )

    history = get_memory(user_id)

    source = route_question(request.question)

    sql = None

    if source == "sales":
        sql = generate_sales_sql(request.question)

    elif source == "hr":
        sql = generate_hr_sql(request.question)

    elif source == "finance":
        sql = generate_finance_sql(request.question)

    else:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine data source"
        )

    if not sql:

        return {
            "source": source,
            "question": request.question,
            "sql": None,
            "answer": "No SQL generated.",
            "rows": []
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

    try:

        # -----------------------------------------
        # DATABASE DATA FOUND
        # -----------------------------------------
        if not dataframe.empty:

            answer = ask_llm(
                request.question,
                dataframe,
                request.language
            )

            data_source = "database"

        # -----------------------------------------
        # DATABASE EMPTY → SEARCH LOCAL DOCUMENTS
        # -----------------------------------------
        else:

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

                data_source = "local_documents"

            else:

                answer = (
                    "No information found in either "
                    "the database or local documents."
                )

                data_source = "none"

    except Exception as e:

        answer = f"LLM Error: {str(e)}"
        data_source = "error"

    add_message(
        user_id,
        "assistant",
        answer
    )

    return {
        "source": source,
        "data_source": data_source,
        "question": request.question,
        "sql": sql,
        "answer": answer,
        "rows": dataframe.to_dict(
            orient="records"
        ),
        "memory_count": len(history)
    }