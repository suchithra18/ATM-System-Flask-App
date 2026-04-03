from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# -------- DATABASE SETUP --------
def get_db():
    conn = sqlite3.connect("bank.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            pin TEXT,
            balance REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# -------- HOME --------
@app.route('/')
def home():
    return redirect('/login')

# -------- REGISTER --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = ""
    if request.method == 'POST':
        name = request.form['name']
        pin = request.form['pin']

        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name, pin) VALUES (?, ?)", (name, pin))
            conn.commit()
            conn.close()
            return redirect('/login')
        except:
            error = "User already exists!"

    return render_template('register.html', error=error)

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == 'POST':
        name = request.form['name']
        pin = request.form['pin']

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE name=?", (name,)).fetchone()
        conn.close()

        if user is None:
            error = "❌ Account not found!"
        elif user['pin'] != pin:
            error = "❌ Wrong PIN!"
        else:
            session['user'] = name
            return redirect('/dashboard')

    return render_template('login.html', error=error)

# -------- DASHBOARD --------
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE name=?",
        (session['user'],)
    ).fetchone()

    # ---- HANDLE ACTIONS ----
    if request.method == 'POST':
        amount = float(request.form['amount'])

        # Validation
        if amount <= 0:
            return redirect('/dashboard')

        if 'deposit' in request.form:
            conn.execute(
                "UPDATE users SET balance = balance + ? WHERE name=?",
                (amount, session['user'])
            )

        elif 'withdraw' in request.form:
            if amount <= user['balance']:
                conn.execute(
                    "UPDATE users SET balance = balance - ? WHERE name=?",
                    (amount, session['user'])
                )
            else:
                return redirect('/dashboard')

        conn.commit()
        return redirect('/dashboard')

    conn.close()
    return render_template(
        'dashboard.html',
        name=user['name'],
        balance=user['balance']
    )

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)