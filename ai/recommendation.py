from database import get_conn, release_conn, get_cursor


# =========================================================
# 1. Generate Product Embedding
# =========================================================

def generate_product_embedding(product_id):

    # Embedding model ko sirf jab explicitly zarurat ho tab import karo
    from ai.embeddings import create_embedding

    conn = get_conn()
    cur = get_cursor(conn)

    try:
        cur.execute(
            "SELECT * FROM products WHERE id = %s",
            (product_id,)
        )

        product = cur.fetchone()

        if not product:
            return False

        embedding = create_embedding(product)

        cur.execute(
            """
            UPDATE products
            SET embedding = %s
            WHERE id = %s
            """,
            (embedding, product_id)
        )

        conn.commit()

        return True

    finally:
        cur.close()
        release_conn(conn)


# =========================================================
# 2. Embedding Based Similar Products
# =========================================================

def recommend_similar_products(product_id, limit=6):

    conn = get_conn()
    cur = get_cursor(conn)

    try:
        cur.execute(
            "SELECT * FROM products WHERE id = %s",
            (product_id,)
        )

        product = cur.fetchone()

        if not product:
            return []

        # IMPORTANT:
        # Render ke 512 MB server par embedding model
        # load nahi karna.
        #
        # Agar product ke paas already embedding hai,
        # PostgreSQL/pgvector se similarity search karo.
        #
        # Agar embedding nahi hai, simply return [].

        if not product["embedding"]:
            return []

        cur.execute(
            """
            SELECT
                *,
                1 - (embedding <=> %s::vector) AS similarity
            FROM products
            WHERE id != %s
              AND stock > 0
              AND embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (
                product["embedding"],
                product_id,
                product["embedding"],
                limit
            )
        )

        return cur.fetchall()

    finally:
        cur.close()
        release_conn(conn)


# =========================================================
# 3. Collaborative Filtering
# =========================================================

def recommend_collaborative(user_id, limit=6):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            SELECT DISTINCT product_id
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.user_id = %s
            """,
            (user_id,)
        )

        purchased = {
            row["product_id"]
            for row in cur.fetchall()
        }

        if not purchased:
            return get_popular_products(limit)

        cur.execute(
            """
            SELECT
                o.user_id,
                COUNT(*) AS common_products
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id = ANY(%s)
              AND o.user_id != %s
            GROUP BY o.user_id
            ORDER BY common_products DESC
            LIMIT 10
            """,
            (list(purchased), user_id)
        )

        similar_users = [
            row["user_id"]
            for row in cur.fetchall()
        ]

        if not similar_users:
            return get_popular_products(limit)

        cur.execute(
            """
            SELECT
                p.*,
                COUNT(*) AS recommendation_score
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON p.id = oi.product_id
            WHERE o.user_id = ANY(%s)
              AND p.stock > 0
              AND NOT (p.id = ANY(%s))
            GROUP BY p.id
            ORDER BY recommendation_score DESC,
                     p.created_at DESC
            LIMIT %s
            """,
            (
                similar_users,
                list(purchased),
                limit
            )
        )

        return cur.fetchall()

    finally:
        cur.close()
        release_conn(conn)


# =========================================================
# 4. Popular Products
# =========================================================

def get_popular_products(limit=6):

    conn = get_conn()
    cur = get_cursor(conn)

    try:

        cur.execute(
            """
            SELECT
                p.*,
                COALESCE(SUM(oi.quantity), 0) AS sold
            FROM products p

            LEFT JOIN order_items oi
                ON p.id = oi.product_id

            WHERE p.stock > 0

            GROUP BY p.id

            ORDER BY sold DESC,
                     p.created_at DESC

            LIMIT %s
            """,
            (limit,)
        )

        return cur.fetchall()

    finally:
        cur.close()
        release_conn(conn)


# =========================================================
# 5. Main Personalized Recommendation
# =========================================================

def recommend_for_user(user_id, limit=6):

    recommendations = recommend_collaborative(
        user_id,
        limit
    )

    if not recommendations:
        recommendations = get_popular_products(limit)

    return recommendations


# from database import get_conn, release_conn, get_cursor
# from ai.embeddings import create_embedding


# # =========================================================
# # 1. Generate Product Embedding
# # =========================================================

# def generate_product_embedding(product_id):

#     conn = get_conn()
#     cur = get_cursor(conn)

#     try:
#         cur.execute(
#             "SELECT * FROM products WHERE id = %s",
#             (product_id,)
#         )

#         product = cur.fetchone()

#         if not product:
#             return False

#         embedding = create_embedding(product)

#         cur.execute(
#             """
#             UPDATE products
#             SET embedding = %s
#             WHERE id = %s
#             """,
#             (embedding, product_id)
#         )

#         conn.commit()

#         return True

#     finally:
#         cur.close()
#         release_conn(conn)


# # =========================================================
# # 2. Embedding Based Similar Products
# # =========================================================

# def recommend_similar_products(product_id, limit=6):

#     conn = get_conn()
#     cur = get_cursor(conn)

#     try:
#         cur.execute(
#             "SELECT * FROM products WHERE id = %s",
#             (product_id,)
#         )

#         product = cur.fetchone()

#         if not product:
#             return []

#         # Embedding nahi hai to generate karo
#         if not product["embedding"]:

#             embedding = create_embedding(product)

#             cur.execute(
#                 """
#                 UPDATE products
#                 SET embedding = %s
#                 WHERE id = %s
#                 """,
#                 (embedding, product_id)
#             )

#             conn.commit()

#             product["embedding"] = embedding

#         # Similar products
#         cur.execute(
#             """
#             SELECT
#                 *,
#                 1 - (embedding <=> %s::vector) AS similarity
#             FROM products
#             WHERE id != %s
#               AND stock > 0
#               AND embedding IS NOT NULL
#             ORDER BY embedding <=> %s::vector
#             LIMIT %s
#             """,
#             (
#                 product["embedding"],
#                 product_id,
#                 product["embedding"],
#                 limit
#             )
#         )

#         return cur.fetchall()

#     finally:
#         cur.close()
#         release_conn(conn)


# # =========================================================
# # 3. Collaborative Filtering
# # =========================================================

# def recommend_collaborative(user_id, limit=6):

#     conn = get_conn()
#     cur = get_cursor(conn)

#     try:

#         # Current user ke purchased products
#         cur.execute(
#             """
#             SELECT DISTINCT product_id
#             FROM order_items oi
#             JOIN orders o ON oi.order_id = o.id
#             WHERE o.user_id = %s
#             """,
#             (user_id,)
#         )

#         purchased = {
#             row["product_id"]
#             for row in cur.fetchall()
#         }

#         # New user → popular products
#         if not purchased:
#             return get_popular_products(limit)

#         # Similar users find karo
#         cur.execute(
#             """
#             SELECT
#                 o.user_id,
#                 COUNT(*) AS common_products
#             FROM order_items oi
#             JOIN orders o ON oi.order_id = o.id
#             WHERE oi.product_id = ANY(%s)
#               AND o.user_id != %s
#             GROUP BY o.user_id
#             ORDER BY common_products DESC
#             LIMIT 10
#             """,
#             (list(purchased), user_id)
#         )

#         similar_users = [
#             row["user_id"]
#             for row in cur.fetchall()
#         ]

#         # Similar users nahi mile
#         if not similar_users:
#             return get_popular_products(limit)

#         # Similar users ne kya purchase kiya
#         cur.execute(
#             """
#             SELECT
#                 p.*,
#                 COUNT(*) AS recommendation_score
#             FROM order_items oi
#             JOIN orders o ON oi.order_id = o.id
#             JOIN products p ON p.id = oi.product_id
#             WHERE o.user_id = ANY(%s)
#               AND p.stock > 0
#               AND NOT (p.id = ANY(%s))
#             GROUP BY p.id
#             ORDER BY recommendation_score DESC,
#                      p.created_at DESC
#             LIMIT %s
#             """,
#             (
#                 similar_users,
#                 list(purchased),
#                 limit
#             )
#         )

#         return cur.fetchall()

#     finally:
#         cur.close()
#         release_conn(conn)


# # =========================================================
# # 4. Popular Products
# # =========================================================

# def get_popular_products(limit=6):

#     conn = get_conn()
#     cur = get_cursor(conn)

#     try:

#         cur.execute(
#             """
#             SELECT
#                 p.*,
#                 COALESCE(SUM(oi.quantity), 0) AS sold
#             FROM products p

#             LEFT JOIN order_items oi
#                 ON p.id = oi.product_id

#             WHERE p.stock > 0

#             GROUP BY p.id

#             ORDER BY sold DESC,
#                      p.created_at DESC

#             LIMIT %s
#             """,
#             (limit,)
#         )

#         return cur.fetchall()

#     finally:
#         cur.close()
#         release_conn(conn)


# # =========================================================
# # 5. Main Personalized Recommendation
# # =========================================================

# def recommend_for_user(user_id, limit=6):

#     recommendations = recommend_collaborative(
#         user_id,
#         limit
#     )

#     # Fallback
#     if not recommendations:
#         recommendations = get_popular_products(limit)

#     return recommendations
