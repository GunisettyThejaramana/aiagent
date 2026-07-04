from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import Date

from app.database import Base




class Sales(Base):
    __tablename__ = "sales"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

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




class Employee(Base):
    __tablename__ = "employees"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    employee_name = Column(
        String(255),
        nullable=False
    )

    department = Column(
        String(255),
        nullable=False
    )

    designation = Column(
        String(255),
        nullable=False
    )

    salary = Column(
        Float,
        nullable=False
    )

    joining_date = Column(
        Date,
        nullable=False
    )

    manager_name = Column(
        String(255),
        nullable=True
    )

    def __repr__(self):
        return (
            f"<Employee(id={self.id}, "
            f"name={self.employee_name})>"
        )




class Revenue(Base):
    __tablename__ = "revenue"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    month = Column(
        String(20),
        nullable=False
    )

    year = Column(
        Integer,
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    source = Column(
        String(255),
        nullable=True
    )

    def __repr__(self):
        return (
            f"<Revenue(id={self.id}, "
            f"amount={self.amount})>"
        )
    



class Operation(Base):
    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)

    task_name = Column(String(255))

    department = Column(String(255))

    status = Column(String(50))

    completion_percent = Column(Integer)
