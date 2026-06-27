from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Date

from app.database import Base


class Sales(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)

    customer_name = Column(
        String(255),
        nullable=False
    )

    product_name = Column(
        String(255),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    price = Column(
        Float,
        nullable=False
    )

    sale_date = Column(
        Date,
        nullable=False
    )

    def __repr__(self):
        return (
            f"<Sales(id={self.id}, "
            f"customer={self.customer_name})>"
        )