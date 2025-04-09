import os
import psycopg2
import psycopg2.extras
from psycopg2 import OperationalError


def get_db_connection():
    try:
        db_url = os.environ.get("DATABASE_URL")
        if db_url is None:
            raise ValueError("DATABASE_URL not set in environment variables")
        conn = psycopg2.connect(db_url, sslmode='require')
        return conn
    except OperationalError as e:
        print(f"Database connection error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def fetch_data():
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."

    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, name, score FROM player ORDER BY score DESC")
        rows = cursor.fetchall()
        return rows, None
    except Exception as e:
        return None, f"Query error: {e}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
