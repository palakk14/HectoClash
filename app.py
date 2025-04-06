from flask import Flask, render_template
import psycopg2
from psycopg2 import OperationalError
import psycopg2.extras


def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="secrets",
            user="postgres",
            password="your_new_password",
            port=5432
        )
        return conn
    except OperationalError as e:
        print(f"Error: {e}")
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
    finally:
        cursor.close()
        conn.close()




