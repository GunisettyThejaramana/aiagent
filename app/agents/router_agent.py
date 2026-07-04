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

    sales_keywords = [
        "sales",
        "customer",
        "product"
    ]

    if any(k in q for k in hr_keywords):
        return "hr"

    if any(k in q for k in finance_keywords):
        return "finance"

    if any(k in q for k in sales_keywords):
        return "sales"

    return "sales"