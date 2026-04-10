from flask import Flask, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = "test_secret_key"  # In production, use a secure and random secret key. 

def get_db_connection():
    conn = sqlite3.connect("budget.db")
    # Switching from plain tuples to sqlite3.Row object.
    conn.row_factory = sqlite3.Row
    #Returns the database from the function
    return conn

def init_db():
    conn = get_db_connection()
    with open("schema.sql", mode="r") as f:
        sql = f.read()

    conn.executescript(sql)
    conn.commit()
    conn.close()
    print("Database initialised successfully")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        conn = get_db_connection()
        username = request.form.get('username')
        password = request.form.get('password')
        cfm_password = request.form.get('cfm-password')

        if username.strip() == "" and password.strip() == "":
            error = "Invalid input (Both username and passwords)"
        if username.strip() == "":
            print("Username cannot be empty")
            error = "Username cannot be empty. Please try again."
        elif password.strip() == "":
            print("Username cannot be empty")
            error = "Password cannot be empty. Please try again."
        else:
            if password == cfm_password:
                print("Both passwords are same.")
                hashed_password = generate_password_hash(password)
                try:
                    conn.execute("INSERT INTO users (username, password) VALUES(?, ?)", (username, hashed_password))
                    conn.commit()
                    conn.close()
                    return redirect(url_for("login"))
                except sqlite3.IntegrityError:
                    error = "Username already taken. Please choose another."
                    conn.close()
                except Exception as e:
                    error = f"An error occured: {e}"
                    conn.close()
            else:
                error = "Passwords do not match. Please try again."

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        conn = get_db_connection()
        entered_username = request.form.get("username")
        entered_password = request.form.get("password")
        user = conn.execute("SELECT * FROM users where username=?", (entered_username,)).fetchone()
        if user is None:
            error = "Username not found"
        else:
            password_is_valid = check_password_hash(user["password"], entered_password)
            if password_is_valid:
                session['user_id'] = user['id']  # write to session
                return redirect(url_for("dashboard"))
            else:
                error = "Incorrect password. Please try again."
    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    else:
        conn = get_db_connection()
        expenses = conn.execute("SELECT * FROM expenses WHERE user_id=?", (session['user_id'],)).fetchall()
        conn.close()
        return render_template("dashboard.html", expenses=expenses)

@app.route("/add", methods=["POST"])
def add_expense():
    amount = request.form.get("amount")
    category = request.form.get("category")
    description = request.form.get("description")
    date = str(datetime.date.today())
    if amount.strip() != "" and category.strip() != "" and description.strip() != "":
        conn = get_db_connection()
        conn.execute("INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)", (session['user_id'], amount, category, description, date))
        conn.commit()
        conn.close()
        session['success_message'] = "Expense added successfully!"
        
    return redirect(url_for("dashboard"))

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))



if __name__ == "__main__":
    init_db()
    app.run(debug=True)