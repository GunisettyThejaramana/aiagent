from datetime import date

from app.database import SessionLocal, engine, Base
from app.models import Sales, Employee, Revenue, Operation


# Create tables if they don't already exist
Base.metadata.create_all(bind=engine)


def insert_sample_data():
    db = SessionLocal()

    try:
        
        if db.query(Sales).count() == 0:

            sales = [
                Sales(
                    customer_name="Ravi Kumar",
                    product_name="Laptop",
                    quantity=2,
                    price=65000,
                    sale_date=date(2026, 7, 1)
                ),
                Sales(
                    customer_name="Anjali Sharma",
                    product_name="Mouse",
                    quantity=5,
                    price=850,
                    sale_date=date(2026, 7, 2)
                ),
                Sales(
                    customer_name="Kiran Reddy",
                    product_name="Keyboard",
                    quantity=3,
                    price=1800,
                    sale_date=date(2026, 7, 3)
                ),
                Sales(
                    customer_name="Rahul Singh",
                    product_name="Monitor",
                    quantity=4,
                    price=14500,
                    sale_date=date(2026, 7, 5)
                ),
                Sales(
                    customer_name="Priya Patel",
                    product_name="Printer",
                    quantity=1,
                    price=22000,
                    sale_date=date(2026, 7, 7)
                )
            ]

            db.add_all(sales)

        
        if db.query(Employee).count() == 0:

            employees = [
                Employee(
                    employee_name="Arun Kumar",
                    department="IT",
                    designation="Software Engineer",
                    salary=65000,
                    joining_date=date(2022, 5, 10),
                    manager_name="Suresh"
                ),
                Employee(
                    employee_name="Meena Devi",
                    department="HR",
                    designation="HR Manager",
                    salary=75000,
                    joining_date=date(2021, 2, 15),
                    manager_name="Anita"
                ),
                Employee(
                    employee_name="Ramesh",
                    department="Finance",
                    designation="Accountant",
                    salary=58000,
                    joining_date=date(2023, 1, 20),
                    manager_name="Prakash"
                ),
                Employee(
                    employee_name="Sneha",
                    department="Sales",
                    designation="Sales Executive",
                    salary=47000,
                    joining_date=date(2024, 4, 12),
                    manager_name="Karthik"
                ),
                Employee(
                    employee_name="Vijay",
                    department="Operations",
                    designation="Operations Manager",
                    salary=82000,
                    joining_date=date(2020, 10, 8),
                    manager_name="CEO"
                )
            ]

            db.add_all(employees)

        
        if db.query(Revenue).count() == 0:

            revenue = [
                Revenue(
                    month="January",
                    year=2026,
                    amount=350000,
                    source="Sales"
                ),
                Revenue(
                    month="February",
                    year=2026,
                    amount=410000,
                    source="Sales"
                ),
                Revenue(
                    month="March",
                    year=2026,
                    amount=520000,
                    source="Online"
                ),
                Revenue(
                    month="April",
                    year=2026,
                    amount=610000,
                    source="Retail"
                ),
                Revenue(
                    month="May",
                    year=2026,
                    amount=700000,
                    source="Enterprise"
                )
            ]

            db.add_all(revenue)

        
        if db.query(Operation).count() == 0:

            operations = [
                Operation(
                    task_name="Server Maintenance",
                    department="IT",
                    status="Completed",
                    completion_percent=100
                ),
                Operation(
                    task_name="Recruitment Drive",
                    department="HR",
                    status="In Progress",
                    completion_percent=70
                ),
                Operation(
                    task_name="Quarterly Audit",
                    department="Finance",
                    status="Completed",
                    completion_percent=100
                ),
                Operation(
                    task_name="Warehouse Inspection",
                    department="Operations",
                    status="Pending",
                    completion_percent=20
                ),
                Operation(
                    task_name="Customer Follow-up",
                    department="Sales",
                    status="Completed",
                    completion_percent=100
                )
            ]

            db.add_all(operations)

        db.commit()

        print("=" * 50)
        print("Sample data inserted successfully.")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(e)

    finally:
        db.close()


if __name__ == "__main__":
    insert_sample_data()