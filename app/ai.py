import pandas as pd


def ask_llm(
    question: str,
    dataframe: pd.DataFrame,
    language="en-US"
):
    question = question.lower().strip()

    
    if dataframe.empty:

        if language == "ta-IN":
            return "தரவுத்தளத்தில் தகவல் இல்லை."

        elif language == "hi-IN":
            return "डेटाबेस में कोई डेटा नहीं मिला।"

        return "No data found in database."

   
    if (
        "total sales" in question
        or "sales amount" in question
        or "overall sales" in question
    ):

        total = dataframe.iloc[0, 0]

        if pd.isna(total):
            total = 0

        total = float(total)

        if language == "ta-IN":
            return f"மொத்த விற்பனை ₹{total:,.2f}"

        elif language == "hi-IN":
            return f"कुल बिक्री ₹{total:,.2f}"

        return f"Your total sales is ₹{total:,.2f}"

    
    elif (
        "total revenue" in question
        or "overall revenue" in question
    ):

        revenue = dataframe.iloc[0, 0]

        if pd.isna(revenue):
            revenue = 0

        revenue = float(revenue)

        if language == "ta-IN":
            return f"மொத்த வருவாய் ₹{revenue:,.2f}"

        elif language == "hi-IN":
            return f"कुल राजस्व ₹{revenue:,.2f}"

        return f"Your total revenue is ₹{revenue:,.2f}"

    
    elif (
        "top customer" in question
        or "top customers" in question
        or "best customer" in question
    ):

        customer = dataframe.iloc[0]["customer_name"]

        if "revenue" in dataframe.columns:
            amount = float(dataframe.iloc[0]["revenue"])
        else:
            amount = float(dataframe.iloc[0, 1])

        if language == "ta-IN":
            return (
                f"முக்கிய வாடிக்கையாளர் "
                f"{customer} (₹{amount:,.2f})"
            )

        elif language == "hi-IN":
            return (
                f"सबसे बड़ा ग्राहक "
                f"{customer} (₹{amount:,.2f})"
            )

        return (
            f"Your top customer is "
            f"{customer} with revenue of ₹{amount:,.2f}"
        )

    
    elif (
        "top product" in question
        or "best selling product" in question
        or "which product sold the most" in question
        or "highest selling product" in question
        or "most sold product" in question
    ):

        product = dataframe.iloc[0]["product_name"]

        if "total_quantity" in dataframe.columns:
            qty = int(dataframe.iloc[0]["total_quantity"])

        elif "quantity" in dataframe.columns:
            qty = int(dataframe.iloc[0]["quantity"])

        else:
            qty = 0

        if language == "ta-IN":
            return (
                f"அதிகம் விற்கப்பட்ட பொருள் "
                f"{product} ({qty})"
            )

        elif language == "hi-IN":
            return (
                f"सबसे अधिक बिकने वाला उत्पाद "
                f"{product} ({qty})"
            )

        return (
            f"The best-selling product is "
            f"{product} with quantity {qty}"
        )

    
    elif (
        "employee count" in question
        or "total employees" in question
        or ("employee" in question and "count" in question)
    ):

        if "total_employees" in dataframe.columns:

            total = int(dataframe.iloc[0]["total_employees"])

        else:

            total = len(dataframe)

        if language == "ta-IN":
            return f"மொத்த பணியாளர்கள் {total}"

        elif language == "hi-IN":
            return f"कुल कर्मचारी {total}"

        return f"Total employees: {total}"

    
    elif "salary" in question:

        count = len(dataframe)

        if language == "ta-IN":
            return f"{count} பணியாளர்களின் சம்பள விவரங்கள் கிடைத்தன"

        elif language == "hi-IN":
            return f"{count} कर्मचारियों का वेतन विवरण मिला"

        return f"Found salary information for {count} employees."

    
    elif "profit" in question:

        value = dataframe.iloc[0, 0]

        if pd.isna(value):
            value = 0

        value = float(value)

        if language == "ta-IN":
            return f"லாபம் ₹{value:,.2f}"

        elif language == "hi-IN":
            return f"लाभ ₹{value:,.2f}"

        return f"Profit is ₹{value:,.2f}"

    
    elif "today" in question:

        count = len(dataframe)

        if language == "ta-IN":
            return f"இன்று {count} விற்பனை பதிவுகள் உள்ளன"

        elif language == "hi-IN":
            return f"आज {count} बिक्री रिकॉर्ड मिले"

        return f"Today you have {count} sales records."

    
    elif "employee" in question:

        return f"Found {len(dataframe)} employee records."

    
    elif "sales" in question:

        return f"Found {len(dataframe)} sales records."

    
    elif "revenue" in question:

        return f"Found {len(dataframe)} revenue records."

    
    elif (
        "operation" in question
        or "task" in question
    ):

        return f"Found {len(dataframe)} operation records."

    
    rows = len(dataframe)

    if language == "ta-IN":
        return f"{rows} பதிவுகள் கிடைத்தன."

    elif language == "hi-IN":
        return f"{rows} रिकॉर्ड मिले।"

    return f"I found {rows} records based on your query."