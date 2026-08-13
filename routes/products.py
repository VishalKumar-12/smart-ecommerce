from flask import Blueprint, render_template, request, session

from models.product import get_all_products, get_product_by_id, get_categories
from ai.recommendation import recommend_for_user, recommend_similar_products
import time
products_bp = Blueprint("products", __name__)


@products_bp.route("/")
def index():
    featured = get_all_products()[:8]
    recommendations = []
    if "user_id" in session:
        recommendations = recommend_for_user(session["user_id"], limit=6)
    return render_template("index.html", featured=featured, recommendations=recommendations)


@products_bp.route("/products")
def list_products():
    category = request.args.get("category")
    search = request.args.get("q")
    items = get_all_products(category=category, search=search)
    categories = get_categories()
    return render_template(
        "products.html", products=items, categories=categories,
        selected_category=category, search=search or ""
    )


@products_bp.route("/products/<int:product_id>")
def product_details(product_id):

    start = time.time()

    product = get_product_by_id(product_id)
    print("Product DB:", time.time() - start)

    start = time.time()

    similar = recommend_similar_products(product_id) if product else []
    print("Recommendation:", time.time() - start)

    start = time.time()

    result = render_template(
        "product-details.html",
        product=product,
        similar=similar
    )

    print("Template:", time.time() - start)

    return result