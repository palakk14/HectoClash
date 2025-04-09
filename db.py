import os
import psycopg2
import psycopg2.extras
import bcrypt


def get_db_connection():
    try:
        db_url = os.environ.get("DATABASE_URL")
        if db_url is None:
            raise ValueError("DATABASE_URL not set in environment variables")
        return psycopg2.connect(db_url, sslmode='require')
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def create_table():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cur = conn.cursor()
        create_script = '''CREATE TABLE IF NOT EXISTS player(
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(160) NOT NULL,
                            email VARCHAR(160) NOT NULL,
                            password VARCHAR(160) NOT NULL,
                            score INT)'''
        cur.execute(create_script)
        conn.commit()
    except Exception as error:
        print(error)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def is_email_exists(email):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cur = conn.cursor()
        query = "SELECT COUNT(*) FROM player WHERE email = %s"
        cur.execute(query, (email,))
        count = cur.fetchone()[0]
        return count > 0
    except Exception as error:
        print(f"Error checking email existence: {error}")
        return False
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def store(name, email, password):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cur = conn.cursor()
        score = 0
        if is_email_exists(email):
            print("error")
            return False
        else:
            insert_script = 'INSERT INTO player(name, email, password, score) VALUES (%s, %s, %s, %s)'
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            insert_value = (name, email, hashed_password.decode('utf-8'), score)
            cur.execute(insert_script, insert_value)
            conn.commit()
            return True
    except Exception as e:
        print(f"Error storing user: {e}")
        return False
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def valid_user(email, password):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cur = conn.cursor()
        query = "SELECT password FROM player WHERE email = %s"
        cur.execute(query, (email,))
        result = cur.fetchone()
        if result is None:
            return False
        stored_password = result[0].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_password)
    except Exception as error:
        print(f"Error validating user: {error}")
        return False
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def can_register(email):
    return not is_email_exists(email)


def getname(email):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return None
        cur = conn.cursor()
        query = "SELECT name FROM player WHERE email = %s"
        cur.execute(query, (email,))
        result = cur.fetchone()
        return result[0] if result else None
    except Exception as error:
        print(f"Error getting name: {error}")
        return None
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def fetch_user_by_email(email):
    conn = get_db_connection()
    if conn is None:
        return None, "Database connection failed."
    try:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT * FROM player WHERE email = %s", (email,))
        user = cursor.fetchone()
        return user, None
    except Exception as e:
        return None, str(e)
    finally:
        cursor.close()
        conn.close()


def update_user_score(email, score):
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        if conn is None:
            return False
        cur = conn.cursor()
        query = "SELECT score FROM player WHERE email = %s"
        cur.execute(query, (email,))
        result = cur.fetchone()
        if result is not None:
            current_score = result[0] if result[0] is not None else 0
            new_score = current_score + score
            update_query = "UPDATE player SET score = %s WHERE email = %s"
            cur.execute(update_query, (new_score, email))
            conn.commit()
            print(f"Updated score for {email}: {current_score} + {score} = {new_score}")
            return True
        return False
    except Exception as error:
        print(f"Error updating score: {error}")
        return False
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
