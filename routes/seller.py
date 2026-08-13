import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

from models.product import (
    get_products_by_seller, create_product, update_product,
    update_stock, delete_product, get_product_by_id
)
from models.order import (
    get_orders_for_seller, get_orders_for_seller_grouped,
    update_order_status
)
from models.seller import get_seller_stats

VALID_STATUSES = ["placed", "shipped", "out_for_delivery", "delivered", "cancelled"]

seller_bp = Blueprint("seller", __name__, url_prefix="/seller")

UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "images"
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def seller_required():
    return session.get("role") == "seller"


@seller_bp.route("/dashboard")
def dashboard():
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    stats = get_seller_stats(session["user_id"])
    recent_orders = get_orders_for_seller(session["user_id"])[:5]

    return render_template(
        "seller/dashboard.html",
        stats=stats,
        recent_orders=recent_orders
    )


@seller_bp.route("/products")
def products():
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    items = get_products_by_seller(session["user_id"])
    return render_template("seller/products.html", products=items)


@seller_bp.route("/products/add", methods=["GET", "POST"])
def add_product():
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "0")
        stock = request.form.get("stock", "0")
        category = request.form.get("category", "").strip()

        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, image_filename))

        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash("Price and stock must be valid numbers.", "error")
            return render_template("seller/add-product.html")

        create_product(
            session["user_id"], name, description,
            price, stock, category, image_filename
        )

        flash("Product added successfully.", "success")
        return redirect(url_for("seller.products"))

    return render_template("seller/add-product.html")


@seller_bp.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    product = get_product_by_id(product_id)

    if not product or product["seller_id"] != session["user_id"]:
        flash("Product not found.", "error")
        return redirect(url_for("seller.products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()

        try:
            price = float(request.form.get("price", "0"))
            stock = int(request.form.get("stock", "0"))
        except ValueError:
            flash("Price and stock must be valid numbers.", "error")
            return render_template(
                "seller/add-product.html",
                product=product,
                edit_mode=True
            )

        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename:
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(UPLOAD_FOLDER, image_filename))

        update_product(
            product_id, name, description,
            price, stock, category, image_filename
        )

        flash("Product updated successfully.", "success")
        return redirect(url_for("seller.products"))

    return render_template(
        "seller/add-product.html",
        product=product,
        edit_mode=True
    )


@seller_bp.route("/products/delete/<int:product_id>", methods=["POST"])
def remove_product(product_id):
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    product = get_product_by_id(product_id)

    if product and product["seller_id"] == session["user_id"]:
        result = delete_product(product_id)

        if result == "archived":
            flash("Product removed from sale because it has previous orders.", "success")
        else:
            flash("Product deleted.", "success")
    else:
        flash("Product not found.", "error")

    return redirect(url_for("seller.products"))


@seller_bp.route("/orders")
def orders():
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    orders = get_orders_for_seller_grouped(session["user_id"])

    return render_template(
        "seller/orders.html",
        orders=orders,
        valid_statuses=VALID_STATUSES
    )


@seller_bp.route("/orders/update/<int:order_id>", methods=["POST"])
def update_status(order_id):
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    seller_orders = get_orders_for_seller_grouped(session["user_id"])
    seller_order_ids = {o["order"]["order_id"] for o in seller_orders}

    if order_id not in seller_order_ids:
        flash("You don't have permission to update this order.", "error")
        return redirect(url_for("seller.orders"))

    status = request.form.get("status", "placed")

    if status not in VALID_STATUSES:
        status = "placed"

    update_order_status(order_id, status)

    flash(
        f"Order #{order_id} marked as {status.replace('_', ' ')}.",
        "success"
    )

    return redirect(url_for("seller.orders"))


@seller_bp.route("/inventory")
def inventory():
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    products = get_products_by_seller(session["user_id"])
    return render_template("seller/inventory.html", products=products)


@seller_bp.route("/inventory/update/<int:product_id>", methods=["POST"])
def update_inventory(product_id):
    if not seller_required():
        flash("Seller access only.", "error")
        return redirect(url_for("auth.login"))

    product = get_product_by_id(product_id)

    if product and product["seller_id"] == session["user_id"]:
        try:
            stock = int(request.form.get("stock", product["stock"]))
            update_stock(product_id, stock)
            flash("Stock updated.", "success")
        except ValueError:
            flash("Stock must be a valid number.", "error")
    else:
        flash("Product not found.", "error")

    return redirect(url_for("seller.inventory"))