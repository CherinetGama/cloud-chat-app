import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_msc_security_key'

def get_db_connection():
    conn = sqlite3.connect('chat.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Users Table
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     username TEXT UNIQUE NOT NULL, 
                     password TEXT NOT NULL,
                     role TEXT DEFAULT 'user')''')
    # Messages Table - 'receiver' የሚል ተጨመረ
    conn.execute('''CREATE TABLE IF NOT EXISTS messages 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT NOT NULL, 
                     receiver TEXT NOT NULL, 
                     content TEXT NOT NULL)''')
    
    admin_exists = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash('admin123')
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', hashed_pw, 'admin'))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    user = session['username']
    
    # ለግለሰቡ የተላኩ ወይም ግለሰቡ የላካቸውን መልእክቶች ብቻ ማሳያ
    messages = conn.execute('''SELECT * FROM messages 
                               WHERE receiver = 'Public' 
                               OR name = ? 
                               OR receiver = ? 
                               ORDER BY id ASC''', (user, user)).fetchall()
    
    # ለሜሴጅ መላኪያ የሚሆኑ የተጠቃሚዎች ዝርዝር
    users = conn.execute('SELECT username FROM users WHERE username != ?', (user,)).fetchall()
    conn.close()
    
    return render_template('index.html', 
                           messages=messages, 
                           current_user=user, 
                           all_users=users,
                           role=session.get('role'))

@app.route('/send', methods=['POST'])
def send():
    if 'username' not in session: return redirect(url_for('login'))
    
    content = request.form.get('content')
    receiver = request.form.get('receiver', 'Public') # ተቀባይ ካልተመረጠ ለሁሉም (Public) ይሆናል
    
    if content:
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (name, receiver, content) VALUES (?, ?, ?)', 
                     (session['username'], receiver, content))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

# የቀሩት (login, register, logout) እንዳሉ ይቀጥላሉ...
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        flash('Invalid login')
    return render_template('login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def register():
    if session.get('role') != 'admin': return "Unauthorized", 403
    if request.method == 'POST':
        new_u, new_p = request.form['username'], request.form['password']
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (new_u, generate_password_hash(new_p)))
            conn.commit()
            conn.close()
            flash('Success!')
        except: flash('Error!')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))
