from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from psycopg2.errors import UniqueViolation

from database import get_conn, release_conn, get_cursor


def create_user(name, email, password, role="customer"):
    conn = get_conn()
    cur = get_cursor(conn)

    try:
        cur.execute(
            """
            INSERT INTO users
            (name, email, password, role)
            VALUES (%s, %s, %s, %s)
            """,
            (
                name,
                email,
                generate_password_hash(password),
                role
            )
        )

        conn.commit()
        return True

    except UniqueViolation:
        conn.rollback()
        return False

    finally:
        cur.close()
        release_conn(conn)


def get_user_by_email(email):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE email = %s
        """,
        (email,)
    )

    row = cur.fetchone()

    cur.close()
    release_conn(conn)

    return row


def get_user_by_id(user_id):
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT *
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    release_conn(conn)

    return row


def verify_password(user_row, password):
    return check_password_hash(
        user_row["password"],
        password
    )


def get_all_users():
    conn = get_conn()
    cur = get_cursor(conn)

    cur.execute(
        """
        SELECT
            id,
            name,
            email,
            role,
            created_at
        FROM users
        ORDER BY created_at DESC
        """
    )

    rows = cur.fetchall()

    cur.close()
    release_conn(conn)

    return rows