import psycopg2
import bcrypt
from psycopg2 import pool

# hostname = "localhost"
# database = "hectoc"
# username = "ace"
# password = "palak1411"
# port_id = 5432


def create_table():
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="your_new_password",
        host="localhost",
        port="5432")
        
        cur = conn.cursor()
        
        create_script = '''CREATE TABLE IF NOT EXISTS player(
                            id          SERIAL PRIMARY KEY,
                            name        varchar(40) NOT NULL,
                            email       varchar(40) NOT NULL,
                            password    varchar(40) NOT NULL,
                            score       int)'''
                            
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
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="your_new_password",
            host="localhost",
            port="5432")
        
        cur = conn.cursor()
        
        # Query to check if email exists
        query = "SELECT COUNT(*) FROM player WHERE email = %s"
        cur.execute(query, (email,))
        
        # Fetch the result (will be a tuple with one item)
        count = cur.fetchone()[0]
        
        # If count > 0, email exists
        return count > 0
        
    except Exception as error:
        print(f"Error checking email existence: {error}")
        return False  # Return False on error
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
                                    
def store(name, email, password):
    conn = None
    cur = None
    conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="your_new_password",
            host="localhost",
            port="5432")
        
    cur = conn.cursor()
    score=0
    if is_email_exists(email):
        print("error")
        return False
    else:
        insert_script = 'INSERT INTO player(name, email, password, score) VALUES (%s, %s, %s, %s)'
        insert_value = (name, email, password, score)
        cur.execute(insert_script, insert_value)
        conn.commit()
        return True
         # Indicate registration succeeded

    cur.close()
        
    conn.close()
            
def valid_user(email, password):
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="your_new_password",
            host="localhost",
            port="5432"
        )
        
        cur = conn.cursor()
        
        # Query to get password for the given email
        query = "SELECT password FROM player WHERE email = %s"
        cur.execute(query, (email,))
        result = cur.fetchone()
        
        if result is None:
            return False  # Email not found

        stored_password = result[0]

        return stored_password == password  # Plaintext comparison

    except Exception as error:
        print(f"Error validating user: {error}")
        return False
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


def can_register(email):
    return is_email_exists(email)    

def getname(email):
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="your_new_password",
            host="localhost",
            port="5432"
        )
        
        cur = conn.cursor()
        
        # Query to get name for the given email
        query = "SELECT name FROM player WHERE email = %s"
        cur.execute(query, (email,))
        result = cur.fetchone()
        
        if result is None:
            return None  # Email not found
        else:
            return result[0]  # Return the name

    except Exception as error:
        print(f"Error getting name: {error}")
        return None
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
     