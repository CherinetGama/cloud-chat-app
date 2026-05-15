import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'amu_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# የዳታቤዝ ሰንጠረዦች
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ዳታቤዝ መፍጠር
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        db.session.add(User(username='admin', password=hashed_pw))
        db.session.commit()

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    return render_template('index.html', messages=messages)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        flash('ያልተሳካ ሙከራ! እባክህ መረጃህን አረጋግጥ።')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('ይህ ስም ቀድሞ ተይዟል!')
        else:
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.add(User(username=username, password=hashed_pw))
            db.session.commit()
            flash('በተሳካ ሁኔታ ተመዝግበሃል! አሁን መግባት ትችላለህ።')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/send', methods=['POST'])
def send():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form.get('content')
    if content:
        new_msg = Message(sender=session['username'], content=content)
        db.session.add(new_msg)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
