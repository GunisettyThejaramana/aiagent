from sqlalchemy.orm import Session

from app import models
from app.schemas import SalesCreate


def create_sale(
    db: Session,
    sale: SalesCreate
):
    db_sale = models.Sales(
        customer_name=sale.customer_name,
        product_name=sale.product_name,
        quantity=sale.quantity,
        price=sale.price,
        sale_date=sale.sale_date
    )

    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)

    return db_sale


def get_sale(
    db: Session,
    sale_id: int
):
    return (
        db.query(models.Sales)
        .filter(models.Sales.id == sale_id)
        .first()
    )


def get_sales(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(models.Sales)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_sale(
    db: Session,
    sale_id: int
):
    sale = get_sale(db, sale_id)

    if not sale:
        return None

    db.delete(sale)
    db.commit()

    return sale


def total_sales_amount(
    db: Session
):
    sales = db.query(models.Sales).all()

    return sum(
        sale.price * sale.quantity
        for sale in sales
    )