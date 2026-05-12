import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ዳታቤዙ በክላውድ ላይ በትክክል እንዲቀመጥ መንገዱን ማስተካከል።
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'chat.db')

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ዳታቤዙ እና ሰንጠረዡ (Table) መኖራቸውን ማረጋገጥ።
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # ቴብሉ መኖሩን ቼክ አድርጎ ከሌለ ይፈጥረዋል
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# አፑ ስራ ሲጀምር ዳታቤዙን እንዲያዘጋጅ
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/send', methods=['POST'])
def send():
    name = request.form.get('name')
    content = request.form.get('content')
    
    if name and content:
        conn = get_db_connection()
        conn.execute('INSERT INTO messages (name, content) VALUES (?, ?)', (name, content))
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
