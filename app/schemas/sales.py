from pydantic import BaseModel
from datetime import date


class SalesCreate(BaseModel):
    product_name: str
    quantity: int
    amount: float
    sale_date: date


class SalesResponse(SalesCreate):
    id: int

    class Config:
        from_attributes = True