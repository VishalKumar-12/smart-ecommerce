from database import get_conn, release_conn, get_cursor
from ai.embeddings import create_embedding


# =========================================================
# Get All Products
# =========================================================

def get_all_products(category=None, search=None):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        query = """
            SELECT *
            FROM products
            WHERE 1=1
        """

        params = []

        if category:

            query += """
                AND category = %s
            """

            params.append(category)

        if search:

            query += """
                AND (
                    name ILIKE %s
                    OR description ILIKE %s
                )
            """

            params.extend([
                f"%{search}%",
                f"%{search}%"
            ])

        query += """
            ORDER BY category ASC, created_at DESC
        """

        cur.execute(
            query,
            params
        )

        rows = cur.fetchall()

        return rows

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Get Product By ID
# =========================================================

def get_product_by_id(product_id):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            SELECT *
            FROM products
            WHERE id = %s
            """,
            (product_id,)
        )

        row = cur.fetchone()

        return row

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Get Products By Seller
# =========================================================

def get_products_by_seller(seller_id):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            SELECT *
            FROM products
            WHERE seller_id = %s
            ORDER BY category ASC, created_at DESC
            """,
            (seller_id,)
        )

        rows = cur.fetchall()

        return rows

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Create Product
# =========================================================

def create_product(
    seller_id,
    name,
    description,
    price,
    stock,
    category,
    image
):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        # -------------------------------------------------
        # Prepare product data for embedding
        # -------------------------------------------------

        product_data = {
            "name": name,
            "description": description,
            "category": category
        }

        # -------------------------------------------------
        # Generate 384-dimensional embedding
        # -------------------------------------------------

        embedding = create_embedding(
            product_data
        )

        # -------------------------------------------------
        # Insert product
        # -------------------------------------------------

        cur.execute(
            """
            INSERT INTO products
            (
                seller_id,
                name,
                description,
                price,
                stock,
                category,
                image,
                embedding
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                seller_id,
                name,
                description,
                price,
                stock,
                category,
                image,
                embedding
            )
        )

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Update Product
# =========================================================

def update_product(
    product_id,
    name,
    description,
    price,
    stock,
    category,
    image=None
):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        # -------------------------------------------------
        # Prepare product data for embedding
        # -------------------------------------------------

        product_data = {
            "name": name,
            "description": description,
            "category": category
        }

        # -------------------------------------------------
        # Generate NEW embedding
        #
        # Important:
        # If name/description/category changes,
        # embedding must also change.
        # -------------------------------------------------

        embedding = create_embedding(
            product_data
        )

        # -------------------------------------------------
        # Update product with image
        # -------------------------------------------------

        if image:

            cur.execute(
                """
                UPDATE products
                SET
                    name = %s,
                    description = %s,
                    price = %s,
                    stock = %s,
                    category = %s,
                    image = %s,
                    embedding = %s
                WHERE id = %s
                """,
                (
                    name,
                    description,
                    price,
                    stock,
                    category,
                    image,
                    embedding,
                    product_id
                )
            )

        # -------------------------------------------------
        # Update product without changing image
        # -------------------------------------------------

        else:

            cur.execute(
                """
                UPDATE products
                SET
                    name = %s,
                    description = %s,
                    price = %s,
                    stock = %s,
                    category = %s,
                    embedding = %s
                WHERE id = %s
                """,
                (
                    name,
                    description,
                    price,
                    stock,
                    category,
                    embedding,
                    product_id
                )
            )

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Update Stock
# =========================================================

def update_stock(
    product_id,
    new_stock
):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            UPDATE products
            SET stock = %s
            WHERE id = %s
            """,
            (
                new_stock,
                product_id
            )
        )

        conn.commit()

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Delete Product
# =========================================================

def delete_product(product_id):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        # -------------------------------------------------
        # Check whether product has previous orders
        # -------------------------------------------------

        cur.execute(
            """
            SELECT COUNT(*) AS count
            FROM order_items
            WHERE product_id = %s
            """,
            (product_id,)
        )

        result = cur.fetchone()

        # -------------------------------------------------
        # If product has orders:
        # Don't physically delete it.
        # Just set stock to 0.
        # -------------------------------------------------

        if result["count"] > 0:

            cur.execute(
                """
                UPDATE products
                SET stock = 0
                WHERE id = %s
                """,
                (product_id,)
            )

            conn.commit()

            return "archived"

        # -------------------------------------------------
        # Otherwise delete product
        # -------------------------------------------------

        cur.execute(
            """
            DELETE FROM products
            WHERE id = %s
            """,
            (product_id,)
        )

        conn.commit()

        return "deleted"

    except Exception:

        conn.rollback()

        raise

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Get Categories
# =========================================================

def get_categories():

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            SELECT DISTINCT category
            FROM products
            WHERE category IS NOT NULL
            ORDER BY category ASC
            """
        )

        rows = cur.fetchall()

        return [
            row["category"]
            for row in rows
        ]

    finally:

        cur.close()
        release_conn(conn)


# =========================================================
# Get All Products For Admin
# =========================================================

def get_all_products_admin():

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            SELECT
                products.*,
                users.name AS seller_name
            FROM products
            JOIN users
                ON products.seller_id = users.id
            ORDER BY products.created_at DESC
            """
        )

        rows = cur.fetchall()

        return rows

    finally:

        cur.close()
        release_conn(conn)