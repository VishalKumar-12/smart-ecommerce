# =========================================================
# AI Product Assistant - Lightweight RAG + Groq
# =========================================================

import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from database import (
    get_conn,
    get_cursor,
    release_conn
)

load_dotenv()


# =========================================================
# Groq + Llama
# =========================================================

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# Product Search
# =========================================================

def retrieve_products(question, limit=3):

    conn = get_conn()
    cur = None

    try:

        cur = get_cursor(conn)

        # -------------------------------------------------
        # Clean user question
        # -------------------------------------------------

        search = question.lower().strip()

        # -------------------------------------------------
        # Common words that are not useful for searching
        # -------------------------------------------------

        stop_words = {
            "i",
            "want",
            "need",
            "a",
            "an",
            "the",
            "for",
            "to",
            "me",
            "please",
            "show",
            "give",
            "get",
            "looking",
            "lookingfor",
            "can",
            "you",
            "do",
            "have",
            "some",
            "my",
            "is",
            "are",
            "of",
            "with",
            "on",
            "in",
            "from",
            "and",
            "or",
            "buy",
            "purchase",
            "find"
        }

        # -------------------------------------------------
        # Extract useful keywords
        # -------------------------------------------------

        words = search.split()

        keywords = []

        for word in words:

            word = word.strip(".,!?;:")

            if (
                word
                and word not in stop_words
                and len(word) >= 2
            ):
                keywords.append(word)

        # -------------------------------------------------
        # Remove duplicate keywords
        # -------------------------------------------------

        keywords = list(dict.fromkeys(keywords))

        # -------------------------------------------------
        # No useful keywords
        # -------------------------------------------------

        if not keywords:
            return []

        # -------------------------------------------------
        # Build dynamic SQL search
        # -------------------------------------------------

        conditions = []
        params = []

        for keyword in keywords:

            conditions.append(
                """
                (
                    name ILIKE %s
                    OR description ILIKE %s
                    OR category ILIKE %s
                )
                """
            )

            search_term = f"%{keyword}%"

            params.extend([
                search_term,
                search_term,
                search_term
            ])

        # -------------------------------------------------
        # Combine conditions
        # -------------------------------------------------

        where_clause = " OR ".join(conditions)

        # -------------------------------------------------
        # SQL Query
        # -------------------------------------------------

        query = f"""
            SELECT
                id,
                name,
                category,
                price,
                description,
                stock
            FROM products
            WHERE stock > 0
            AND (
                {where_clause}
            )
            ORDER BY created_at DESC
            LIMIT %s
        """

        params.append(limit)

        # -------------------------------------------------
        # Execute query
        # -------------------------------------------------

        cur.execute(
            query,
            params
        )

        return cur.fetchall()

    finally:

        if cur:
            cur.close()

        release_conn(conn)


# =========================================================
# Product Context
# =========================================================

def create_product_context(products):

    if not products:

        return "No relevant products were found."

    context = []

    for product in products:

        context.append(
            f"""
Product ID: {product['id']}
Name: {product['name']}
Category: {product['category']}
Price: ₹{product['price']}
Description: {product['description']}
Stock: {product['stock']}
"""
        )

    return "\n".join(context)


# =========================================================
# Greeting Detection
# =========================================================

def is_greeting(question):

    text = question.lower().strip()

    greetings = {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "helo",
        "good morning",
        "good afternoon",
        "good evening"
    }

    return text in greetings


# =========================================================
# Generate Chatbot Response
# =========================================================

def generate_chatbot_response(question):

    # -----------------------------------------------------
    # Greeting
    # -----------------------------------------------------

    if is_greeting(question):

        return {
            "answer": (
                "Hello! 👋 How can I help you "
                "with our products?"
            ),
            "products": []
        }

    # -----------------------------------------------------
    # Retrieve products
    # -----------------------------------------------------

    products = retrieve_products(
        question,
        limit=3
    )

    # -----------------------------------------------------
    # Create product context
    # -----------------------------------------------------

    product_context = create_product_context(
        products
    )

    # -----------------------------------------------------
    # AI Prompt
    # -----------------------------------------------------

    prompt = f"""
You are a product assistant for this e-commerce website.

STRICT RULES:

1. Answer ONLY using the PRODUCT CONTEXT provided below.

2. Never use outside knowledge.

3. Never guess or assume product information.

4. Never invent product names, prices, features,
specifications, ratings, availability or stock.

5. If the requested information is not present
in PRODUCT CONTEXT, say:

"I don't have that information in the available
product data."

6. If no relevant products were retrieved,
do not recommend any product.

7. If the user asks for a price range, strictly
respect that range.

8. If the user asks something unrelated to products,
politely say that you can only help with
product-related questions.

9. Keep the answer concise and directly answer
what the user asked.

10. Do not add unrelated information.

PRODUCT CONTEXT:
{product_context}

USER QUESTION:
{question}

ANSWER:
"""

    # -----------------------------------------------------
    # Generate AI response
    # -----------------------------------------------------

    response = llm.invoke(prompt)

    # -----------------------------------------------------
    # Return response
    # -----------------------------------------------------

    return {
        "answer": response.content,
        "products": [
            dict(product)
            for product in products
        ]
    }
