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


router = APIRouter()


# ==================================
# HOME
# ==================================

@router.get("/")
def home():
    return {
        "message": "Enterprise AI Assistant Running"
    }


# ==================================
# SALES APIs
# ==================================

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


# ==================================
# AI QUESTION ANSWERING
# ==================================

@router.post("/ask")
def ask_ai(
    request: schemas.QuestionRequest,
    db: Session = Depends(get_db)
):

    # --------------------------
    # MEMORY
    # --------------------------

    user_id = request.user_id

    add_message(
        user_id,
        "user",
        request.question
    )

    history = get_memory(user_id)

    # --------------------------
    # ROUTE QUESTION
    # --------------------------

    source = route_question(
        request.question
    )

    sql = None

    # --------------------------
    # SALES
    # --------------------------

    if source == "sales":

        sql = generate_sales_sql(
            request.question
        )

    # --------------------------
    # HR
    # --------------------------

    elif source == "hr":

        sql = generate_hr_sql(
            request.question
        )

    # --------------------------
    # FINANCE
    # --------------------------

    elif source == "finance":

        sql = generate_finance_sql(
            request.question
        )

    else:

        raise HTTPException(
            status_code=400,
            detail="Unable to determine data source"
        )

    # --------------------------
    # SQL NOT GENERATED
    # --------------------------

    if not sql:

        return {
            "source": source,
            "question": request.question,
            "sql": None,
            "answer": "No SQL generated for this question.",
            "rows": []
        }

    # --------------------------
    # EXECUTE SQL
    # --------------------------

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

    # --------------------------
    # GENERATE ANSWER
    # --------------------------

    try:

        answer = ask_llm(
            request.question,
            dataframe,
            request.language
        )

    except Exception as e:

        answer = f"LLM Error: {str(e)}"

    # --------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------

    add_message(
        user_id,
        "assistant",
        answer
    )

    # --------------------------
    # RESPONSE
    # --------------------------

    return {
        "source": source,
        "question": request.question,
        "sql": sql,
        "answer": answer,
        "rows": dataframe.to_dict(
            orient="records"
        ),
        "memory_count": len(history)
    }