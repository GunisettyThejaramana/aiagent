import pandas as pd

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app import schemas
from app.ai import generate_sql
from app.ai import ask_llm


router = APIRouter()


# =========================================
# Home
# =========================================
@router.get("/")
def home():
    return {
        "message": "Enterprise AI Assistant Running"
    }


# =========================================
# Create Sales
# =========================================
@router.post("/sales")
def create_sale(
    sale: schemas.SalesCreate,
    db: Session = Depends(get_db)
):
    return crud.create_sale(db, sale)


# =========================================
# Get Sales
# =========================================
@router.get("/sales")
def get_sales(
    db: Session = Depends(get_db)
):
    return crud.get_sales(db)


# =========================================
# Ask AI
# =========================================
@router.post("/ask")
def ask_ai(
    request: schemas.QuestionRequest,
    db: Session = Depends(get_db)
):
    sql = generate_sql(request.question)

    dataframe = pd.read_sql(
        sql,
        db.bind
    )

    answer = ask_llm(
        request.question,
        dataframe,
        request.language   # <-- language added
    )

    return {
        "question": request.question,
        "sql": sql,
        "answer": answer,
        "rows": dataframe.to_dict(
            orient="records"
        )
    }