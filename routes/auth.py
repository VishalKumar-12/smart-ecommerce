from flask import Blueprint, render_template, request, redirect, url_for, session, flash

from models.user import create_user, get_user_by_email, verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "customer")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if role not in ("customer", "seller"):
            role = "customer"

        created = create_user(name, email, password, role)
        if not created:
            flash("An account with this email already exists.", "error")
            return render_template("register.html")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if not user or not verify_password(user, password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["role"] = user["role"]

        flash(f"Welcome back, {user['name']}!", "success")

        if user["role"] == "admin":
            return redirect(url_for("admin.dashboard"))
        elif user["role"] == "seller":
            return redirect(url_for("seller.dashboard"))
        return redirect(url_for("products.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("products.index"))
