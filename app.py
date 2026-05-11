from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

# ዳታቤዝ ዝግጅት
def init_db():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user TEXT, content TEXT)''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute("SELECT * FROM messages ORDER BY id DESC")
    msgs = c.fetchall()
    conn.close()
    return render_template('index.html', messages=msgs)

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
