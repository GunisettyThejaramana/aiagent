def generate_operations_sql(question):

    q = question.lower()

    if "pending tasks" in q:
        return """
        SELECT *
        FROM operations
        WHERE status='Pending'
        """

    if "completed tasks" in q:
        return """
        SELECT *
        FROM operations
        WHERE status='Completed'
        """

    return """
    SELECT *
    FROM operations
    LIMIT 10
    """