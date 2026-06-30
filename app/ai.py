import pandas as pd



def generate_sql(question: str):
    question = question.lower()

    if "today" in question:
        return """
        SELECT *
        FROM sales
        WHERE sale_date = CURRENT_DATE;
        """

    elif "top customer" in question:
        return """
        SELECT customer_name,
               SUM(price * quantity) AS total
        FROM sales
        GROUP BY customer_name
        ORDER BY total DESC
        LIMIT 5;
        """

    elif "top product" in question:
        return """
        SELECT product_name,
               SUM(quantity) AS quantity
        FROM sales
        GROUP BY product_name
        ORDER BY quantity DESC
        LIMIT 5;
        """

    elif "total sales" in question:
        return """
        SELECT COALESCE(SUM(price * quantity), 0) AS total_sales
        FROM sales;
        """

    else:
        return """
        SELECT *
        FROM sales
        LIMIT 20;
        """



def ask_llm(question: str, dataframe: pd.DataFrame, language="en-US"):
    question = question.lower()

    if dataframe.empty:
        if language == "ta-IN":
            return "தரவுத்தளத்தில் தகவல் இல்லை."
        elif language == "hi-IN":
            return "डेटाबेस में कोई डेटा नहीं मिला।"
        else:
            return "No data found in database."

    
    if "total sales" in question:
        total = dataframe.iloc[0, 0]

        if total is None or pd.isna(total):
            total = 0

        total = float(total)

        if language == "ta-IN":
            return f"உங்கள் மொத்த விற்பனை ரூபாய் {total:,.2f}"
        elif language == "hi-IN":
            return f"आपकी कुल बिक्री ₹{total:,.2f} है"
        else:
            return f"Your total sales is ₹{total:,.2f}"

    
    elif "top customer" in question:
        customer = dataframe.iloc[0]["customer_name"]
        total = dataframe.iloc[0]["total"]

        if total is None or pd.isna(total):
            total = 0

        total = float(total)

        if language == "ta-IN":
            return f"உங்கள் முக்கிய வாடிக்கையாளர் {customer}. வாங்கியது ரூபாய் {total:,.2f}"
        elif language == "hi-IN":
            return f"आपके सबसे बड़े ग्राहक {customer} हैं। कुल खरीद ₹{total:,.2f}"
        else:
            return f"Your top customer is {customer} with purchase of ₹{total:,.2f}"

    
    elif "top product" in question:
        product = dataframe.iloc[0]["product_name"]
        qty = dataframe.iloc[0]["quantity"]

        if qty is None or pd.isna(qty):
            qty = 0

        qty = int(qty)

        if language == "ta-IN":
            return f"அதிகம் விற்கப்பட்ட பொருள் {product}. அளவு {qty}"
        elif language == "hi-IN":
            return f"सबसे ज्यादा बिकने वाला उत्पाद {product} है। मात्रा {qty}"
        else:
            return f"Your best selling product is {product} with quantity {qty}"

    elif "today" in question:
        count = len(dataframe)

        if language == "ta-IN":
            return f"இன்று {count} விற்பனை பதிவுகள் உள்ளன"
        elif language == "hi-IN":
            return f"आज {count} बिक्री रिकॉर्ड मिले"
        else:
            return f"Today you have {count} sales records"

    
    else:
        rows = len(dataframe)

        if language == "ta-IN":
            return f"{rows} பதிவுகள் கண்டுபிடிக்கப்பட்டன"
        elif language == "hi-IN":
            return f"{rows} रिकॉर्ड मिले"
        else:
            return f"I found {rows} records based on your query"