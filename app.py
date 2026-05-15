import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_msc_security_key'

# 1. የዳታቤዝ ቦታን ማስተካከል (Render ላይ ስህተት እንዳይፈጠር)
# ዳታቤዙ በ "instance" ፎልደር ውስጥ እንዲሆን ያደርጋል
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'chat.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # ተጠቃሚዎች ሰንጠረዥ
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     username TEXT UNIQUE NOT NULL, 
                     password TEXT NOT NULL,
                     role TEXT DEFAULT 'user')''')
    # መልእክቶች ሰንጠረዥ
    conn.execute('''CREATE TABLE IF NOT EXISTS messages 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT NOT NULL, 
                     receiver TEXT NOT NULL, 
                     content TEXT NOT NULL)''')
    
    # የ Admin አካውንት መኖሩን ማረጋገጥ
    admin_exists = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash('admin123')
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     ('admin', hashed_pw, 'admin'))
    
    conn.commit()
    conn.close()

# አፑ ሲጀምር ዳታቤዙን ይፈጥራል
init_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = session['username']
    
    # መልእክቶችን መፈለጊያ (Logic ተስተካክሏል)
    messages = conn.execute('''SELECT * FROM messages 
                               WHERE receiver = 'Public' 
                               OR name = ? 
                               OR receiver = ? 
                               ORDER BY id ASC''', (user, user)).fetchall()
    
    # የሌሎች ተጠቃሚዎች ዝርዝር
    users = conn.execute('SELECT username FROM users WHERE username != ?', (user,)).fetchall()
    conn.close()
    
    return render_template('index.html', 
                           messages=messages, 
                           current_user=user, 
                           all_users=users,
                           role=session.get('role'))

@app.route('/send', methods=['POST'])
def send():
    if 'username' not in session: 
        return redirect(url_for('login'))
    
    content = request.form.get('content')
    receiver = request.form.get('receiver', 'Public')
    
    if content:
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO messages (name, receiver, content) VALUES (?, ?, ?)', 
                         (session['username'], receiver, content))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error: {e}")
            flash("Message could not be sent.")
            
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower().strip()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def register():
    if session.get('role') != 'admin': 
        return "Unauthorized", 403
        
    if request.method == 'POST':
        new_u = request.form['username'].lower().strip()
        new_p = request.form['password']
        
        if not new_u or not new_p:
            flash('Fill all fields!')
            return redirect(url_for('register'))
            
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                         (new_u, generate_password_hash(new_p)))
            conn.commit()
            conn.close()
            flash('Success!')
        except sqlite3.IntegrityError:
            flash('Username already exists!')
        except Exception as e:
            flash(f'Error: {e}')
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Render ላይ እንዲሰራ ፖርቱን ማስተካከል
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
