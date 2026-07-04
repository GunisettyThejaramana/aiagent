def generate_finance_sql(question):

    q = question.lower()

    if "revenue" in q:
        return """
        SELECT SUM(amount) AS total_revenue
        FROM revenue
        """

    return """
    SELECT *
    FROM revenue
    LIMIT 10
    """