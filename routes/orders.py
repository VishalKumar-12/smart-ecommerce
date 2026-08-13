from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models.product import get_product_by_id
from models.order import (
    get_cart_items, add_to_cart, update_cart_item, remove_from_cart,
    place_order, get_orders_by_user
)

orders_bp = Blueprint("orders", __name__)


def login_required():
    return "user_id" in session


@orders_bp.route("/cart")
def cart():
    if not login_required():
        flash("Please log in to view your cart.", "error")
        return redirect(url_for("auth.login"))
    items = get_cart_items(session["user_id"])
    total = sum(item["price"] * item["quantity"] for item in items)
    return render_template("cart.html", items=items, total=total)


@orders_bp.route("/cart/add/<int:product_id>", methods=["POST"])
def add(product_id):
    if not login_required():
        flash("Please log in to add items to your cart.", "error")
        return redirect(url_for("auth.login"))

    product = get_product_by_id(product_id)
    if not product or product["stock"] <= 0:
        flash("This product is currently out of stock.", "error")
        return redirect(url_for("products.list_products"))

    quantity = int(request.form.get("quantity", 1))
    add_to_cart(session["user_id"], product_id, quantity)
    flash(f"{product['name']} added to cart.", "success")
    return redirect(request.referrer or url_for("products.list_products"))


@orders_bp.route("/cart/update/<int:cart_id>", methods=["POST"])
def update(cart_id):
    if not login_required():
        return redirect(url_for("auth.login"))
    quantity = int(request.form.get("quantity", 1))
    update_cart_item(cart_id, quantity)
    return redirect(url_for("orders.cart"))


@orders_bp.route("/cart/remove/<int:cart_id>", methods=["POST"])
def remove(cart_id):
    if not login_required():
        return redirect(url_for("auth.login"))
    remove_from_cart(cart_id)
    flash("Item removed from cart.", "success")
    return redirect(url_for("orders.cart"))


@orders_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not login_required():
        flash("Please log in to check out.", "error")
        return redirect(url_for("auth.login"))

    items = get_cart_items(session["user_id"])
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("orders.cart"))

    total = sum(item["price"] * item["quantity"] for item in items)

    if request.method == "POST":
        address = request.form.get("address", "").strip()
        if not address:
            flash("Please provide a delivery address.", "error")
            return render_template("checkout.html", items=items, total=total)

        order_id = place_order(session["user_id"], address, items)
        flash(f"Order #{order_id} placed successfully!", "success")
        return redirect(url_for("orders.orders_history"))

    return render_template("checkout.html", items=items, total=total)


@orders_bp.route("/orders")
def orders_history():
    if not login_required():
        flash("Please log in to view your orders.", "error")
        return redirect(url_for("auth.login"))
    orders = get_orders_by_user(session["user_id"])
    return render_template("orders.html", orders=orders)
