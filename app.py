import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'amu_secret_key_2026'

# ፋይሎች የሚቀመጡበትን ቦታ መወሰን
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ዳታቤዙን በራስ-ሰር የሚያስተካክል እና አድሚን የሚፈጥር ፈንክሽን
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. የ users ቴብል መኖሩን ማረጋገጥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    # 2. የ messages ቴብል መኖሩን ማረጋገጥ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT,
            receiver TEXT DEFAULT 'Public',
            file_url TEXT
        )
    ''')
    
    # 3. file_url ኮለምን በ messages ቴብል ላይ መጨመሩን ማረጋገጥ
    try:
        cursor.execute('ALTER TABLE messages ADD COLUMN file_url TEXT')
    except sqlite3.OperationalError:
        pass # ቀድሞ ካለ ምንም አያደርግም

    # 4. አድሚን ተጠቃሚ ከሌለ መፍጠር (admin / admin123)
    try:
        admin_exists = cursor.execute('SELECT * FROM users WHERE username = "admin"').fetchone()
        if not admin_exists:
            hashed_pw = generate_password_hash('admin123')
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', 
                           ('admin', hashed_pw, 'admin'))
            conn.commit()
    except Exception as e:
        print(f"Admin creation error: {e}")
        
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    messages = conn.execute('''
        SELECT * FROM messages 
        WHERE receiver = 'Public' 
        OR receiver = ? 
        OR name = ?
    ''', (session['username'], session['username'])).fetchall()
    
    all_users = conn.execute('SELECT username FROM users WHERE username != ?', (session['username'],)).fetchall()
    conn.close()
    return render_template('index.html', messages=messages, current_user=session['username'], role=session.get('role'), all_users=all_users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower() 
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        flash('ያልተሳካ ሙከራ! እባክዎ ስም ወይም የይለፍ ቃል ያረጋግጡ።')
    return render_template('login.html')

@app.route('/send', methods=['POST'])
def send():
    if 'username' not in session: return redirect(url_for('login'))
    
    content = request.form.get('content')
    receiver = request.form.get('receiver', 'Public')
    file = request.files.get('file')
    
    file_url = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = filename
        if not content: content = f"Sent a file: {filename}"

    if content or file_url:
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (name, content, receiver, file_url) VALUES (?, ?, ?, ?)',
                     (session['username'], content, receiver, file_url))
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/admin/register', methods=['GET', 'POST'])
def register():
    if session.get('role') != 'admin': return "ፍቃድ የለዎትም!", 403
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, password, role))
            conn.commit()
            flash('ተጠቃሚው በትክክል ተመዝግቧል!')
        except:
            flash('ይህ ስም ቀድሞ ተይዟል!')
        conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db() # አፑ ሲነሳ ዳታቤዙን በራሱ ያስተካክላል
    app.run(debug=True)
