from groq import Groq
import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()
GROQ_MODEL = os.getenv('GROQ_MODEL')
db_path = Path(__file__).parent / 'db.sqlite'
client_sql = Groq()

sql_prompt = """
You are an expert at translating natural language product-related questions into valid SQL queries using the schema provided below.

You must strictly follow the format and rules. NEVER invent new table or column names.

<schema>
Table: product

Columns:
- product_link: string (hyperlink to the product)
- title: string (name of the product)
- brand: string (brand of the product)
- price: integer (price in Indian Rupees)
- discount: float (e.g., 0.1 = 10% off)
- avg_rating: float (0 to 5 scale, 5 is highest)
- total_ratings: integer (number of ratings received)
</schema>

Instructions:
1. Only generate queries for valid, relevant questions about the product table.
2. Always use SELECT * FROM product ... — include all fields.
3. Wrap brand names using LOWER(brand) = 'brandname' to ensure case-insensitive comparison. DO NOT use ILIKE.
4. Always wrap your output strictly inside <SQL> and </SQL> tags — no explanation, no markdown.
5. End the query with a semicolon `;`.
6. Do not hallucinate tokens, don't include invalid syntax or placeholders.
7. If the question is unclear or not related to this schema, return only:  
   <SQL>--</SQL>

Example:
<SQL>
SELECT * FROM product WHERE LOWER(brand) = 'puma' AND price BETWEEN 5000 AND 10000;
</SQL>
"""


def generate_sql_query(question):
    chat_completion = client_sql.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": sql_prompt
            },
            {
                "role": "user",
                "content": question
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.3,
        max_tokens=1200
    )
    return chat_completion.choices[0].message.content


def run_query(query):
    if query.strip().upper().startswith('SELECT'):
        with sqlite3.connect(db_path) as connection:
            df = pd.read_sql_query(query, connection)
            return df
    return None


def sql_chain(question):
    sql_query = generate_sql_query(question)
    pattern = "<SQL>(.*?)</SQL>"
    matches = re.findall(pattern, sql_query, re.DOTALL)
    if len(matches) == 0:
        return "Sorry LLm could not generate query for this question"
    print("sql query:", matches[0].strip())
    response = run_query(matches[0].strip())
    if response is None:
        return "Sorry there was problem while executing the query"

    context = response.to_dict(orient='records')
    answer = data_comprehension(question, context)
    return answer


comprehension_prompt = """
You are an expert at interpreting user product questions and responding with a clean, formatted summary of the matching products.

You will receive:
- A natural language question
- A list of product data in this format: title, price, discount, avg_rating, product_link

Your task:
- Filter and display only relevant products based on the question.
- Format each product in the following way:
  {index}. {title}: Rs. {price} ({discount_percent} percent off), Rating: {avg_rating_rounded} <{product_link}>

Formatting Rules:
- Round discount to whole number (e.g., 0.25 → 25 percent off)
- Round rating to 1 decimal (e.g., 4.28 → 4.3)
- Return only the formatted product list. Do NOT include explanations.
- If the question is irrelevant or nonsensical, return:
  "Invalid question. Please ask a clear question about the product data."
- If no products match, return:
  "No matching products found."

Example output:
1. Campus Women Running Shoes: Rs. 1104 (35 percent off), Rating: 4.4 <link>
2. Puma Men Sports Sneakers: Rs. 5499 (20 percent off), Rating: 4.2 <link>
"""


def data_comprehension(question, context):
    chat_completion = client_sql.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": comprehension_prompt
            },
            {
                "role": "user",
                "content": f'Question: {question} Data: {context}'
            }
        ],
        model=os.environ['GROQ_MODEL'],
        temperature=0.3,

    )
    return chat_completion.choices[0].message.content


if __name__ == "__main__":
    question = "show me all the nike shoes between price range of 4000 to 5000"
    answer = sql_chain(question)
    print(answer)
