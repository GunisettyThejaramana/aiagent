import pandas as pd


def ask_llm(
    question: str,
    dataframe: pd.DataFrame,
    language="en-US"
):

    question = question.lower()

    # -----------------------------
    # NO DATA
    # -----------------------------

    if dataframe.empty:

        if language == "ta-IN":
            return "தரவுத்தளத்தில் தகவல் இல்லை."

        elif language == "hi-IN":
            return "डेटाबेस में कोई डेटा नहीं मिला।"

        return "No data found in database."

    # -----------------------------
    # SALES
    # -----------------------------

    if "total sales" in question:

        total = dataframe.iloc[0, 0]

        if pd.isna(total):
            total = 0

        total = float(total)

        if language == "ta-IN":
            return f"உங்கள் மொத்த விற்பனை ₹{total:,.2f}"

        elif language == "hi-IN":
            return f"आपकी कुल बिक्री ₹{total:,.2f} है"

        return f"Your total sales is ₹{total:,.2f}"

    elif "top customer" in question:

        customer = dataframe.iloc[0]["customer_name"]
        total = float(dataframe.iloc[0]["total"])

        if language == "ta-IN":
            return (
                f"உங்கள் முக்கிய வாடிக்கையாளர் "
                f"{customer}. வாங்கியது ₹{total:,.2f}"
            )

        elif language == "hi-IN":
            return (
                f"आपके सबसे बड़े ग्राहक "
                f"{customer} हैं। कुल खरीद ₹{total:,.2f}"
            )

        return (
            f"Your top customer is "
            f"{customer} with purchases of ₹{total:,.2f}"
        )

    elif "top product" in question:

        product = dataframe.iloc[0]["product_name"]
        qty = int(dataframe.iloc[0]["quantity"])

        if language == "ta-IN":
            return (
                f"அதிகம் விற்கப்பட்ட பொருள் "
                f"{product}. அளவு {qty}"
            )

        elif language == "hi-IN":
            return (
                f"सबसे ज्यादा बिकने वाला उत्पाद "
                f"{product} है। मात्रा {qty}"
            )

        return (
            f"Your best-selling product is "
            f"{product} with quantity {qty}"
        )

    elif "today" in question:

        count = len(dataframe)

        if language == "ta-IN":
            return f"இன்று {count} விற்பனை பதிவுகள் உள்ளன"

        elif language == "hi-IN":
            return f"आज {count} बिक्री रिकॉर्ड मिले"

        return f"Today you have {count} sales records"

    # -----------------------------
    # HR
    # -----------------------------

    elif "employee" in question and "count" in question:

        if "total_employees" in dataframe.columns:

            total = int(dataframe.iloc[0]["total_employees"])

            if language == "ta-IN":
                return f"மொத்த பணியாளர்கள்: {total}"

            elif language == "hi-IN":
                return f"कुल कर्मचारी: {total}"

            return f"Total employees: {total}"

    elif "salary" in question:

        count = len(dataframe)

        if language == "ta-IN":
            return (
                f"{count} பணியாளர்களின் சம்பள தகவல்கள் கிடைத்தன"
            )

        elif language == "hi-IN":
            return (
                f"{count} कर्मचारियों का वेतन डेटा मिला"
            )

        return f"Found salary information for {count} employees"

    # -----------------------------
    # FINANCE
    # -----------------------------

    elif "expense" in question:

        count = len(dataframe)

        if language == "ta-IN":
            return f"{count} செலவுத் தகவல்கள் கிடைத்தன"

        elif language == "hi-IN":
            return f"{count} खर्च रिकॉर्ड मिले"

        return f"Found {count} expense records"

    elif "profit" in question:

        if len(dataframe.columns) > 0:

            value = dataframe.iloc[0, 0]

            if pd.isna(value):
                value = 0

            value = float(value)

            if language == "ta-IN":
                return f"லாபம் ₹{value:,.2f}"

            elif language == "hi-IN":
                return f"लाभ ₹{value:,.2f}"

            return f"Profit is ₹{value:,.2f}"

    # -----------------------------
    # GENERIC RESPONSE
    # -----------------------------

    rows = len(dataframe)

    if language == "ta-IN":
        return f"{rows} பதிவுகள் கண்டுபிடிக்கப்பட்டன"

    elif language == "hi-IN":
        return f"{rows} रिकॉर्ड मिले"

    return f"I found {rows} records based on your query"