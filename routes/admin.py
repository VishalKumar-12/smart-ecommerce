from flask import Blueprint, render_template, session, redirect, url_for, flash

from models.user import get_all_users
from models.product import get_all_products_admin
from models.order import get_all_orders_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    return session.get("role") == "admin"


@admin_bp.route("/dashboard")
def dashboard():
    if not admin_required():
        flash("Admin access only.", "error")
        return redirect(url_for("auth.login"))

    users = get_all_users()
    products = get_all_products_admin()
    orders = get_all_orders_admin()

    total_revenue = sum(o["total"] for o in orders)

    stats = {
        "total_users": len(users),
        "total_sellers": len([u for u in users if u["role"] == "seller"]),
        "total_customers": len([u for u in users if u["role"] == "customer"]),
        "total_products": len(products),
        "total_orders": len(orders),
        "total_revenue": total_revenue,
    }

    return render_template(
        "admin/dashboard.html", stats=stats, users=users, products=products, orders=orders
    )
