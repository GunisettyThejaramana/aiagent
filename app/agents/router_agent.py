def route_question(question):

    q = question.lower()

    hr_keywords = [
        "employee",
        "employees",
        "salary",
        "leave",
        "department"
    ]

    finance_keywords = [
        "revenue",
        "expense",
        "budget",
        "finance"
    ]
    inventory_keywords = [
    "inventory",
    "stock",
    "warehouse"
]

    production_keywords = [
    "production",
    "machine",
    "factory"
]

    sales_keywords = [
        "sales",
        "customer",
        "product"
    ]

    operations_keywords = [
    "operation",
    "task",
    "project",
    "production"
]

    if any(k in q for k in hr_keywords):
        return "hr"

    if any(k in q for k in finance_keywords):
        return "finance"

    if any(k in q for k in sales_keywords):
        return "sales"
    

    if any(k in q for k in operations_keywords):
        return "operations"
    

    if any(
    k in q
    for k in inventory_keywords
):
        return "inventory"

    if any(
    k in q
    for k in production_keywords
):
        return "production"

    return "sales"