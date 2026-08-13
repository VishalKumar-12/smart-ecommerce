import os

from dotenv import load_dotenv

# =========================================================
# Load environment variables FIRST
# =========================================================

load_dotenv()

print(
    "GROQ KEY LOADED:",
    bool(os.getenv("GROQ_API_KEY"))
)


# =========================================================
# Imports
# =========================================================

import psycopg2

from psycopg2.extras import RealDictCursor

from flask import Flask, g


# =========================================================
# Routes / Blueprints
# =========================================================

from routes.auth import auth_bp
from routes.products import products_bp
from routes.orders import orders_bp
from routes.seller import seller_bp
from routes.admin import admin_bp
from routes.chatbot import chatbot_bp


# =========================================================
# Flask App
# =========================================================

app = Flask(__name__)


app.secret_key = os.getenv(
    "SECRET_KEY",
    "smart-ecommerce-secret-key-change-in-production"
)


# =========================================================
# Database Configuration
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")


if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL not found in .env"
    )


# =========================================================
# Database Connection
# =========================================================

def get_db():

    if "db" not in g:

        g.db = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )

    return g.db


# =========================================================
# New Database Connection
# =========================================================

def get_conn():

    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


# =========================================================
# Close Database Connection
# =========================================================

@app.teardown_appcontext
def close_db(exception=None):

    db = g.pop("db", None)

    if db:

        db.close()


# =========================================================
# Initialize Database
# =========================================================

def init_db():

    conn = get_db()

    cur = conn.cursor()


    # =====================================================
    # Users
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'customer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    # =====================================================
    # Products
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            seller_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price NUMERIC(10,2) NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            category TEXT,
            image TEXT,
            embedding vector(384),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (seller_id)
                REFERENCES users(id)
        )
    """)


    # =====================================================
    # Cart
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (user_id)
                REFERENCES users(id),
            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
    """)


    # =====================================================
    # Orders
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total NUMERIC(10,2) NOT NULL,
            status TEXT NOT NULL DEFAULT 'placed',
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
        )
    """)


    # =====================================================
    # Order Items
    # =====================================================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            seller_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price NUMERIC(10,2) NOT NULL,
            FOREIGN KEY (order_id)
                REFERENCES orders(id),
            FOREIGN KEY (product_id)
                REFERENCES products(id)
        )
    """)


    # =====================================================
    # Create Default Admin
    # =====================================================

    from werkzeug.security import generate_password_hash


    cur.execute(
        """
        SELECT id
        FROM users
        WHERE role = %s
        LIMIT 1
        """,
        ("admin",)
    )


    if not cur.fetchone():

        cur.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (%s, %s, %s, %s)
            """,
            (
                "Admin",
                "admin@smartshop.com",
                generate_password_hash("admin123"),
                "admin"
            )
        )


    # =====================================================
    # Commit Changes
    # =====================================================

    conn.commit()

    cur.close()


# =========================================================
# Register Blueprints
# =========================================================

app.register_blueprint(auth_bp)

app.register_blueprint(products_bp)

app.register_blueprint(orders_bp)

app.register_blueprint(seller_bp)

app.register_blueprint(admin_bp)

app.register_blueprint(chatbot_bp)


# =========================================================
# Debug - Registered Routes
# =========================================================

print("\n========== REGISTERED ROUTES ==========")

print(app.url_map)

print("=======================================\n")


# =========================================================
# Run Application
# =========================================================

if __name__ == "__main__":

    with app.app_context():

        init_db()


    app.run(
        debug=True
    )