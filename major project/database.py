import sqlite3

DB_NAME = "patients_system.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT, age INTEGER, gender TEXT,
        mobile TEXT UNIQUE, email TEXT UNIQUE, password TEXT, is_admin INTEGER DEFAULT 0)''')
        
    # Seed Admin User if not exists
    c.execute('SELECT * FROM users WHERE email = ?', ('shubhamkachhawa27@gmail.com',))
    if not c.fetchone():
        import bcrypt
        hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute('INSERT INTO users (name, age, gender, mobile, email, password, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  ('System Admin', 35, 'Other', '0000000000', 'shubhamkachhawa27@gmail.com', hashed, 1))

    # Predictions Table (replaces History)
    c.execute('''CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_email TEXT, date TEXT, risk_level REAL, result TEXT, 
        input_data TEXT)''')
        
    # Reminders Table
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_email TEXT, task TEXT, date TEXT)''')

    # Chats Table
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_email TEXT, message TEXT, response TEXT, timestamp TEXT)''')

    conn.commit()
    conn.close()

init_db()

# Query wrapper functions
def execute_query(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()
    
def fetch_all(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

def fetch_one(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchone()
    conn.close()
    return data
