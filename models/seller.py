from database import get_conn, get_cursor, release_conn


def get_seller_stats(seller_id):

    conn = get_conn()
    cur = get_cursor(conn)

    # Total products
    cur.execute(
        """
        SELECT COUNT(*) AS c
        FROM products
        WHERE seller_id = %s
        """,
        (seller_id,)
    )

    product_count = cur.fetchone()["c"]

    # Total stock
    cur.execute(
        """
        SELECT COALESCE(SUM(stock), 0) AS s
        FROM products
        WHERE seller_id = %s
        """,
        (seller_id,)
    )

    total_stock = cur.fetchone()["s"]

    # Total sales
    cur.execute(
        """
        SELECT COALESCE(SUM(quantity * price), 0) AS total
        FROM order_items
        WHERE seller_id = %s
        """,
        (seller_id,)
    )

    total_sales = cur.fetchone()["total"]

    # Number of orders
    cur.execute(
        """
        SELECT COUNT(DISTINCT order_id) AS c
        FROM order_items
        WHERE seller_id = %s
        """,
        (seller_id,)
    )

    orders_count = cur.fetchone()["c"]

    # Low stock products
    cur.execute(
        """
        SELECT *
        FROM products
        WHERE seller_id = %s
        AND stock <= 5
        """,
        (seller_id,)
    )

    low_stock = cur.fetchall()

    cur.close()
    release_conn(conn)

    return {
        "product_count": product_count,
        "total_stock": total_stock,
        "total_sales": total_sales,
        "orders_count": orders_count,
        "low_stock": low_stock,
    }