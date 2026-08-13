# =========================================================
# Database Connection Pool
# =========================================================

import os

from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError


# =========================================================
# Load environment variables
# =========================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not found")


# =========================================================
# Connection Pool
# =========================================================

pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)


# =========================================================
# Get Healthy Connection
# =========================================================

def get_conn():

    conn = pool.getconn()

    try:

        # Check whether connection is alive
        if conn.closed:
            pool.putconn(
                conn,
                close=True
            )

            conn = pool.getconn()

        else:

            cur = conn.cursor()

            try:
                cur.execute("SELECT 1")
            finally:
                cur.close()

    except Exception:

        # Broken connection
        try:
            pool.putconn(
                conn,
                close=True
            )
        except Exception:
            pass

        # Create fresh connection
        conn = pool.getconn()

    return conn


# =========================================================
# Release Connection
# =========================================================

def release_conn(conn):

    if conn:

        try:

            if conn.closed:
                pool.putconn(
                    conn,
                    close=True
                )
            else:
                pool.putconn(conn)

        except Exception:

            try:
                pool.putconn(
                    conn,
                    close=True
                )
            except Exception:
                pass


# =========================================================
# Get Cursor
# =========================================================

def get_cursor(conn):

    return conn.cursor(
        cursor_factory=RealDictCursor
    )


























# import os
# from dotenv import load_dotenv
# from psycopg2.pool import ThreadedConnectionPool
# from psycopg2.extras import RealDictCursor

# load_dotenv()

# DATABASE_URL = os.getenv("DATABASE_URL")

# if not DATABASE_URL:
#     raise RuntimeError("DATABASE_URL not found")

# pool = ThreadedConnectionPool(
#     minconn=1,
#     maxconn=10,
#     dsn=DATABASE_URL
# )


# def get_conn():
#     return pool.getconn()


# def release_conn(conn):
#     pool.putconn(conn)


# def get_cursor(conn):
#     return conn.cursor(cursor_factory=RealDictCursor)





















# # import os
# # import psycopg2
# # from psycopg2.extras import RealDictCursor
# # from dotenv import load_dotenv

# # load_dotenv()


# # def get_conn():
# #     return psycopg2.connect(
# #         os.getenv("DATABASE_URL"),
# #         cursor_factory=RealDictCursor
# #     )