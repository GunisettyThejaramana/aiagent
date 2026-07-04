from datetime import date
from pydantic import BaseModel


# ==================================
# SALES SCHEMAS
# ==================================

class SalesBase(BaseModel):
    customer_name: str
    product_name: str
    quantity: int
    price: float
    sale_date: date


class SalesCreate(SalesBase):
    pass


class SalesResponse(SalesBase):
    id: int

    class Config:
        from_attributes = True


# ==================================
# AI REQUEST SCHEMA
# ==================================

class QuestionRequest(BaseModel):

    user_id: str = "default_user"

    question: str

    language: str = "en-US"


# ==================================
# AI RESPONSE SCHEMA
# ==================================

class AIResponse(BaseModel):

    answer: str

    data: list