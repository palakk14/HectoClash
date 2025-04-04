from flask import Flask, render_template, request
import psycopg2
import bcrypt

app = Flask(__name__)

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="secrets",
    user="postgres",
    password="Anushka@123",
    port=5432
)
cursor = conn.cursor()

@app.route("/")
def home():
    return render_template("home.ejs")

@app.route("/login")
def login():
    return render_template("login.ejs")

@app.route("/register")
def register():
    return render_template("register.ejs")

@app.route("/register", methods=["POST"])
def register_user():
    name = request.form["name"]
    email = request.form["username"]
    password = request.form["password"].encode('utf-8')

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        return "Email already exists. Try logging in."
    else:
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                       (name, email, hashed.decode('utf-8')))
        conn.commit()
        return render_template("secrets.ejs")

@app.route("/login", methods=["POST"])
def login_user():
    email = request.form["username"]
    password = request.form["password"].encode('utf-8')

    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        stored_hashed = user[2]  # Assuming password is the 3rd column (index 2)
        try:
            # Ensure bcrypt can handle the stored password correctly
            if bcrypt.checkpw(password, stored_hashed.encode('utf-8')):
                return render_template("secrets.ejs")
            else:
                return "Incorrect Password"
        except ValueError as e:
            return f"Error with stored password hash: {str(e)}"
    else:
        return "User not found"


if __name__ == "__main__":
    app.run(debug=True, port=3000)
