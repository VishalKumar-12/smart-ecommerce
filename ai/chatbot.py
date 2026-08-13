# =========================================================
# AI Product Assistant - RAG + Llama
# =========================================================

import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq

from database import (
    get_conn,
    get_cursor,
    release_conn
)


# =========================================================
# Load environment variables
# =========================================================

load_dotenv()


# =========================================================
# 1. Load existing embedding model
# =========================================================

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# 2. Groq + Llama LLM
# =========================================================

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)


# =========================================================
# 3. Create embedding for user's question
# =========================================================

def create_query_embedding(question):

    embedding = embedding_model.encode(
        question,
        normalize_embeddings=True
    )

    return embedding.tolist()


# =========================================================
# 4. Retrieve relevant products using pgvector
# =========================================================

def retrieve_products(question, limit=5):

    conn = get_conn()
    cur = None

    try:

        # -------------------------------------------------
        # Create query embedding
        # -------------------------------------------------

        query_embedding = create_query_embedding(
            question
        )


        # -------------------------------------------------
        # Create cursor
        # -------------------------------------------------

        cur = get_cursor(conn)


        # -------------------------------------------------
        # pgvector similarity search
        # -------------------------------------------------

        cur.execute(
            """
            SELECT
                id,
                name,
                category,
                price,
                description,
                stock
            FROM products
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (
                query_embedding,
                limit
            )
        )


        products = cur.fetchall()

        return products


    finally:

        # -------------------------------------------------
        # Close cursor
        # -------------------------------------------------

        if cur:
            cur.close()


        # -------------------------------------------------
        # IMPORTANT:
        # Return connection to connection pool
        # -------------------------------------------------

        release_conn(conn)


# =========================================================
# 5. Create product context for LLM
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
# 6. Greeting Detection
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
# 7. Generate AI Assistant Response
# =========================================================

def generate_chatbot_response(question):

    # =====================================================
    # Greeting
    # =====================================================

    if is_greeting(question):

        return {
            "answer": (
                "Hello! 👋 How can I help you "
                "with our products?"
            ),
            "products": []
        }


    # =====================================================
    # RAG - Retrieve relevant products
    # =====================================================

    products = retrieve_products(
        question,
        limit=5
    )


    # =====================================================
    # Create product context
    # =====================================================

    product_context = create_product_context(
        products
    )


    # =====================================================
    # Prompt for Llama
    # =====================================================

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


    # =====================================================
    # Llama generates final answer
    # =====================================================

    response = llm.invoke(prompt)


    # =====================================================
    # Return answer + products
    # =====================================================

    return {
        "answer": response.content,
        "products": [
            dict(product)
            for product in products
        ]
    }