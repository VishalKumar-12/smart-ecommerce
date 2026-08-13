from sentence_transformers import SentenceTransformer


# =========================================================
# AI MODEL
# =========================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


# =========================================================
# CREATE PRODUCT TEXT
# =========================================================

def create_product_text(product):
    """
    Product ke important fields ko ek text me convert karta hai.
    """

    name = product.get("name", "") or ""
    description = product.get("description", "") or ""
    category = product.get("category", "") or ""

    text = f"""
Product: {name}
Category: {category}
Description: {description}
"""

    return text.strip()


# =========================================================
# CREATE EMBEDDING
# =========================================================

def create_embedding(product):
    """
    Product ka 384-dimensional embedding generate karta hai.
    """

    text = create_product_text(product)

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()