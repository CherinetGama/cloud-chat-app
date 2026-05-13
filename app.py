import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # ለሴሽን አስፈላጊ ነው

# ዳታቤዝ ግንኙነት
def get_db_connection():
    conn = sqlite3.connect('chat.db')
    conn.row_factory = sqlite3.Row
    return conn

# ዳታቤዙን መጀመሪያ ላይ ለማዘጋጀት
def init_db():
    conn = get_db_connection()
    # የተጠቃሚዎች ቴብል
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     username TEXT UNIQUE NOT NULL, 
                     password TEXT NOT NULL,
                     role TEXT DEFAULT 'user')''')
    # የመልእክቶች ቴብል
    conn.execute('''CREATE TABLE IF NOT EXISTS messages 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT NOT NULL, 
                     content TEXT NOT NULL)''')
    
    # መጀመሪያ ላይ አድሚን ለመፍጠር (username: admin, password: admin123)
    admin_exists = conn.execute('SELECT * FROM users WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        hashed_pw = generate_password_hash('admin123')
        conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                     ('admin', hashed_pw, 'admin'))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages ORDER BY id ASC').fetchall()
    conn.close()
    return render_template('index.html', messages=messages, current_user=session['username'])

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
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def register():
    # አድሚን ብቻ እንዲመዘግብ
    if session.get('role') != 'admin':
        return "Unauthorized", 403
        
    if request.method == 'POST':
        new_user = request.form['username']
        new_pass = request.form['password']
        hashed_pw = generate_password_hash(new_pass)
        
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (new_user, hashed_pw))
            conn.commit()
            conn.close()
            flash(f'User {new_user} registered successfully!')
        except:
            flash('Username already exists!')
            
    return render_template('register.html')

@app.route('/send', methods=['POST'])
def send():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    content = request.form.get('content')
    if content:
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (name, content) VALUES (?, ?)', (session['username'], content))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
