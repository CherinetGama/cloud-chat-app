import os
import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# ዳታቤዙ የሚቀመጥበትን ቦታ ማስተካከል
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'chat.db')

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ዳታቤዙን ለመጀመሪያ ጊዜ መፍጠር
def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT)')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    messages = conn.execute('SELECT * FROM messages').fetchall()
    conn.close()
    return render_template('index.html', messages=messages)

# ሌላው የኮድህ ክፍል ይቀጥላል...
@app.route('/send', methods=['POST'])
def send():
    user = request.form.get('user')
    content = request.form.get('content')
    if user and content:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute("INSERT INTO messages (user, content) VALUES (?, ?)", (user, content))
        conn.commit()
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    # Cloud ላይ እንዲሰራ host='0.0.0.0' አስፈላጊ ነው
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
