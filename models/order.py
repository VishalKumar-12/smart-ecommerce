from datetime import datetime, timedelta

from database import get_conn,release_conn, get_cursor


# Order lifecycle
ORDER_STAGES = [
    "placed",
    "shipped",
    "out_for_delivery",
    "delivered",
]

ESTIMATED_DELIVERY_DAYS = 5


def get_cart_items(user_id):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT cart.id AS cart_id,
               cart.quantity,
               products.*
        FROM cart
        JOIN products
            ON cart.product_id = products.id
        WHERE cart.user_id = %s
        """,
        (user_id,),
    )

    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return rows


def add_to_cart(user_id, product_id, quantity=1):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT *
        FROM cart
        WHERE user_id = %s
        AND product_id = %s
        """,
        (user_id, product_id),
    )

    existing = cur.fetchone()

    if existing:
        cur.execute(
            """
            UPDATE cart
            SET quantity = quantity + %s
            WHERE id = %s
            """,
            (quantity, existing["id"]),
        )

    else:
        cur.execute(
            """
            INSERT INTO cart
            (user_id, product_id, quantity)
            VALUES (%s, %s, %s)
            """,
            (user_id, product_id, quantity),
        )

    conn.commit()

    cur.close()
    release_conn(conn)


def update_cart_item(cart_id, quantity):
    conn = get_conn()
    cur = get_cursor(conn)

    if quantity <= 0:
        cur.execute(
            "DELETE FROM cart WHERE id = %s",
            (cart_id,),
        )
    else:
        cur.execute(
            """
            UPDATE cart
            SET quantity = %s
            WHERE id = %s
            """,
            (quantity, cart_id),
        )

    conn.commit()

    cur.close()
    release_conn(conn)


def remove_from_cart(cart_id):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        "DELETE FROM cart WHERE id = %s",
        (cart_id,),
    )

    conn.commit()

    cur.close()
    release_conn(conn)


def clear_cart(user_id):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        "DELETE FROM cart WHERE user_id = %s",
        (user_id,),
    )

    conn.commit()

    cur.close()
    release_conn(conn)


def place_order(user_id, address, cart_items):

    conn = get_conn()
    cur = get_cursor(conn)

    total = sum(
        item["price"] * item["quantity"]
        for item in cart_items
    )

    # PostgreSQL: RETURNING id
    cur.execute(
        """
        INSERT INTO orders
        (user_id, total, status, address)
        VALUES (%s, %s, 'placed', %s)
        RETURNING id
        """,
        (user_id, total, address),
    )

    order_id = cur.fetchone()["id"]

    for item in cart_items:

        cur.execute(
            """
            INSERT INTO order_items
            (order_id, product_id, seller_id, quantity, price)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                order_id,
                item["id"],
                item["seller_id"],
                item["quantity"],
                item["price"],
            ),
        )

        cur.execute(
            """
            UPDATE products
            SET stock = stock - %s
            WHERE id = %s
            """,
            (
                item["quantity"],
                item["id"],
            ),
        )

    cur.execute(
        "DELETE FROM cart WHERE user_id = %s",
        (user_id,),
    )

    conn.commit()

    cur.close()
    conn.close()

    return order_id


def get_orders_by_user(user_id):

    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT *
        FROM orders
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )

    orders = cur.fetchall()

    result = []

    for order in orders:

        cur.execute(
            """
            SELECT order_items.*,
                   products.name,
                   products.image
            FROM order_items
            JOIN products
                ON order_items.product_id = products.id
            WHERE order_id = %s
            """,
            (order["id"],),
        )

        items = cur.fetchall()

        status = (
            order["status"]
            if order["status"] in ORDER_STAGES
            else "placed"
        )

        stage_index = (
            ORDER_STAGES.index(status)
            if status in ORDER_STAGES
            else 0
        )

        estimated_delivery = None

        try:

            placed_dt = order["created_at"]

            if isinstance(placed_dt, str):
                placed_dt = datetime.strptime(
                    placed_dt,
                    "%Y-%m-%d %H:%M:%S"
                )

            estimated_delivery = (
                placed_dt
                + timedelta(days=ESTIMATED_DELIVERY_DAYS)
            ).strftime("%d %b %Y")

        except (ValueError, TypeError):
            estimated_delivery = None

        result.append(
            {
                "order": order,
                "items": items,
                "status": status,
                "stage_index": stage_index,
                "is_cancelled": (
                    order["status"] == "cancelled"
                ),
                "estimated_delivery": estimated_delivery,
            }
        )

    cur.close()
    release_conn(conn)

    return result


def get_purchased_categories(user_id):

    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT DISTINCT products.category
        FROM order_items
        JOIN orders
            ON order_items.order_id = orders.id
        JOIN products
            ON order_items.product_id = products.id
        WHERE orders.user_id = %s
        """,
        (user_id,),
    )

    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return [
        r["category"]
        for r in rows
        if r["category"]
    ]


def get_orders_for_seller(seller_id):

    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT order_items.*,
               products.name AS product_name,
               orders.created_at,
               orders.status,
               orders.id AS order_id
        FROM order_items
        JOIN orders
            ON order_items.order_id = orders.id
        JOIN products
            ON order_items.product_id = products.id
        WHERE order_items.seller_id = %s
        ORDER BY orders.created_at DESC
        """,
        (seller_id,),
    )

    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return rows


def get_orders_for_seller_grouped(seller_id):

    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT DISTINCT
               orders.id AS order_id,
               orders.status,
               orders.address,
               orders.created_at,
               users.id AS customer_id,
               users.name AS customer_name,
               users.email AS customer_email
        FROM orders
        JOIN order_items
            ON order_items.order_id = orders.id
        JOIN users
            ON orders.user_id = users.id
        WHERE order_items.seller_id = %s
        ORDER BY orders.created_at DESC
        """,
        (seller_id,),
    )

    orders = cur.fetchall()

    result = []

    for order in orders:

        cur.execute(
            """
            SELECT order_items.*,
                   products.name AS product_name
            FROM order_items
            JOIN products
                ON order_items.product_id = products.id
            WHERE order_items.order_id = %s
            AND order_items.seller_id = %s
            """,
            (
                order["order_id"],
                seller_id,
            ),
        )

        items = cur.fetchall()

        subtotal = sum(
            i["price"] * i["quantity"]
            for i in items
        )

        result.append(
            {
                "order": order,
                "items": items,
                "subtotal": subtotal,
            }
        )

    cur.close()
    release_conn(conn)

    return result


def update_order_status(order_id, status):

    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        UPDATE orders
        SET status = %s
        WHERE id = %s
        """,
        (status, order_id),
    )

    conn.commit()

    cur.close()
    release_conn(conn)


def get_all_orders_admin():

    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT orders.*,
               users.name AS customer_name,
               users.email AS customer_email
        FROM orders
        JOIN users
            ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
        """
    )

    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return rows