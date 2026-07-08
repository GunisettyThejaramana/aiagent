def route_question(question: str):

    q = question.lower().strip()

    hr_keywords = [
        "employee",
        "employees",
        "salary",
        "leave",
        "department",
        "hr",
        "manager",
        "designation"
    ]

    finance_keywords = [
        "revenue",
        "expense",
        "budget",
        "finance",
        "profit",
        "loss",
        "income"
    ]

    sales_keywords = [
        "sales",
        "customer",
        "customers",
        "product",
        "products",
        "order",
        "orders"
    ]

    operations_keywords = [
        "operation",
        "operations",
        "task",
        "tasks",
        "project",
        "projects"
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

    
    if any(keyword in q for keyword in hr_keywords):
        return "hr"

    
    if any(keyword in q for keyword in finance_keywords):
        return "finance"

    
    if any(keyword in q for keyword in sales_keywords):
        return "sales"

    
    if any(keyword in q for keyword in operations_keywords):
        return "operations"

   
    if any(keyword in q for keyword in inventory_keywords):
        return "inventory"

    
    if any(keyword in q for keyword in production_keywords):
        return "production"

    
    return "documents"