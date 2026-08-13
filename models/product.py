from database import get_conn, release_conn, get_cursor


def get_all_products(category=None, search=None):
    conn = get_conn()
    cur = get_cursor(conn)

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        query += " AND category = %s"
        params.append(category)

    if search:
        query += " AND (name ILIKE %s OR description ILIKE %s)"
        params.extend([
            f"%{search}%",
            f"%{search}%"
        ])

    query += " ORDER BY category ASC, created_at DESC"

    cur.execute(query, params)
    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return rows


def get_product_by_id(product_id):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT *
        FROM products
        WHERE id = %s
        """,
        (product_id,)
    )

    row = cur.fetchone()

    cur.close()
    release_conn(conn)

    return row


def get_products_by_seller(seller_id):
    conn = get_conn()
    cur = get_cursor(conn)

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

    cur.close()
    release_conn(conn)

    return rows


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
            image
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            seller_id,
            name,
            description,
            price,
            stock,
            category,
            image
        )
    )

    conn.commit()

    cur.close()
    release_conn(conn)


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
                image = %s
            WHERE id = %s
            """,
            (
                name,
                description,
                price,
                stock,
                category,
                image,
                product_id
            )
        )
    else:
        cur.execute(
            """
            UPDATE products
            SET
                name = %s,
                description = %s,
                price = %s,
                stock = %s,
                category = %s
            WHERE id = %s
            """,
            (
                name,
                description,
                price,
                stock,
                category,
                product_id
            )
        )

    conn.commit()

    cur.close()
    release_conn(conn)


def update_stock(product_id, new_stock):
    conn = get_conn()
    cur = get_cursor(conn)

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

    cur.close()
    release_conn(conn)


def delete_product(product_id):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT COUNT(*) AS count
        FROM order_items
        WHERE product_id = %s
        """,
        (product_id,)
    )

    result = cur.fetchone()

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

        cur.close()
        release_conn(conn)

        return "archived"

    cur.execute(
        """
        DELETE FROM products
        WHERE id = %s
        """,
        (product_id,)
    )

    conn.commit()

    cur.close()
    release_conn(conn)

    return "deleted"


def get_categories():
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT DISTINCT category
        FROM products
        WHERE category IS NOT NULL
        ORDER BY category ASC
        """
    )

    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return [
        row["category"]
        for row in rows
    ]


def get_all_products_admin():
    conn = get_conn()
    cur = get_cursor(conn)

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

    cur.close()
    release_conn(conn)

    return rows