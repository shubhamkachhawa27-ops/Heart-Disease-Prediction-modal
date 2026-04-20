import bcrypt
from database import fetch_one, execute_query
import sqlite3

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

def create_user(name, age, gender, mobile, email, password):
    try:
        execute_query('INSERT INTO users (name, age, gender, mobile, email, password) VALUES (?, ?, ?, ?, ?, ?)', 
                      (name, age, gender, mobile, email, hash_password(password)))
        return True
    except sqlite3.IntegrityError:
        return False

def login_user_email(email, password):
    data = fetch_one('SELECT password, name, is_admin FROM users WHERE email = ?', (email,))
    if data and check_password(password, data[0]):
        return {"name": data[1], "is_admin": bool(data[2])}
    return None

def login_user_mobile(mobile):
    data = fetch_one('SELECT name, email, is_admin FROM users WHERE mobile = ?', (mobile,))
    if data:
        return {"name": data[0], "email": data[1], "is_admin": bool(data[2])}
    return None

def reset_password(email, mobile, new_password):
    data = fetch_one('SELECT id FROM users WHERE email = ? AND mobile = ?', (email, mobile))
    if data:
        execute_query('UPDATE users SET password = ? WHERE email = ?', (hash_password(new_password), email))
        return True
    return False
