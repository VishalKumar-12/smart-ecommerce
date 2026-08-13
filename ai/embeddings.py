from sentence_transformers import SentenceTransformer


# =========================================================
# AI MODEL
# =========================================================

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

model = None


# =========================================================
# LOAD MODEL
# =========================================================

def get_model():

    global model

    if model is None:
        model = SentenceTransformer(
            MODEL_NAME,
            device="cpu"
        )

    return model


# =========================================================
# CREATE PRODUCT TEXT
# =========================================================

def create_product_text(product):

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

    text = create_product_text(product)

    embedding = get_model().encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()