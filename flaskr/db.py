import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'database.db'

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        return None


def get_readonly_db_connection():
    conn = sqlite3.connect('file:database.db?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    with get_db_connection() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT,
            source TEXT,
            author_name TEXT,
            birthdate TEXT,
            author_memo TEXT,
            supplement_info TEXT
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            activity TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor = con.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'role' not in columns:
            con.execute("""
            ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'
            """)

def get_user(username):
    with get_readonly_db_connection() as con:
        user = con.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return user if user else None

def insert_quotes(quotes):
    with get_db_connection() as con:
        cur = con.cursor()
        for quote in quotes:
            cur.execute("""
            INSERT INTO quotes (quote, source, author_name, birthdate, author_memo, supplement_info)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (quote['quote'], quote['source'], quote['author_name'], quote['birthdate'], quote['author_memo'], quote['supplement_info']))
        con.commit()

def fetch_all_quotes():
    with get_readonly_db_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM quotes")
        return cur.fetchall()


def fetch_random_quote():
    with get_readonly_db_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchone()
        if row:
            return {
                'id': row[0],
                'quote': row[1],
                'source': row[2],
                'author_name': row[3],
                'birthdate': row[4],
                'author_memo': row[5],
                'supplement_info': row[6]
            }
        else:
            return None

def create_user(username, password, role='user'):
    hashed_password = generate_password_hash(password)
    with get_db_connection() as con:
        con.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed_password, role))


def get_user_password(username):
    with get_readonly_db_connection() as con:
        user = con.execute("SELECT password FROM users WHERE username = ?", (username,)).fetchone()
        return user["password"] if user else None
    
def get_user_role(username):
    with get_readonly_db_connection() as con:
        user = con.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
        return user["role"] if user else None

def update_user_role(username, new_role):
    with get_db_connection() as con:
        con.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, username))
        con.commit()

def log_activity(username, activity):
    with get_db_connection() as con:
        con.execute("INSERT INTO history (username, activity) VALUES (?, ?)", (username, activity))

def get_user_history(username):
    with get_readonly_db_connection() as con:
        history = con.execute("SELECT activity FROM history WHERE username = ?", (username,)).fetchall()
        return [row["activity"] for row in history]

