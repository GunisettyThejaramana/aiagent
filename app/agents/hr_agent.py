def generate_hr_sql(question):

    q = question.lower()

    if (
        "employee count" in q
        or "how many employees" in q
        or "employees are there" in q
        or "total employees" in q
    ):
        return """
        SELECT COUNT(*) AS total_employees
        FROM employees
        """

    elif (
        "salary" in q
        or "salaries" in q
    ):
        return """
        SELECT employee_name,
               salary
        FROM employees
        """

    return """
    SELECT *
    FROM employees
    LIMIT 10
    """