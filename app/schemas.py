from datetime import date
from pydantic import BaseModel


# =========================================
# Sales Schema
# =========================================
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


# =========================================
# AI Request Schema
# =========================================
class QuestionRequest(BaseModel):
    question: str
    language: str = "en-US"


# =========================================
# AI Response Schema
# =========================================
class AIResponse(BaseModel):
    answer: str
    data: list