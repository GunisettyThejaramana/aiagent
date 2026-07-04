def generate_sales_sql(question):

    q = question.lower()

    if "top customer" in q:
        return """
        SELECT customer_name,
               SUM(quantity * price) AS revenue
        FROM sales
        GROUP BY customer_name
        ORDER BY revenue DESC
        LIMIT 5
        """

    elif "top product" in q:
        return """
        SELECT product_name,
               SUM(quantity) AS qty
        FROM sales
        GROUP BY product_name
        ORDER BY qty DESC
        LIMIT 5
        """

    elif "total sales" in q:
        return """
        SELECT SUM(quantity * price) AS total_sales
        FROM sales
        """

    return """
    SELECT *
    FROM sales
    LIMIT 10
    """