import json
import pandas as pd

from openai import OpenAI

from app.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


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
        SELECT
        SUM(price * quantity) AS total_sales
        FROM sales;
        """

    else:

        return """
        SELECT *
        FROM sales
        LIMIT 20;
        """


def dataframe_to_text(df: pd.DataFrame):

    if df.empty:
        return "No data found."

    return df.to_string(index=False)


def ask_llm(question: str, dataframe: pd.DataFrame):

    data = dataframe_to_text(dataframe)

    prompt = f"""
You are a Business Analyst.

Question:

{question}

Database Result:

{data}

Explain the answer in professional English.
"""

    response = client.chat.completions.create(

        model="gpt-4.1",

        messages=[

            {
                "role": "system",
                "content": "You are a business analyst."
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        temperature=0.2

    )

    return response.choices[0].message.content