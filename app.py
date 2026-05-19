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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), default='Everyone')
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    # አድሚን ከሌለ በታችኛው ኬዝ መፍጠር
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        db.session.add(User(username='admin', password=hashed_pw))
        db.session.commit()

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = session['username']
    # ለሁሉም የተላኩ ወይም ለዚህ ሰው ብቻ የመጡ/የተላኩ መልዕክቶችን ማምጣት
    messages = Message.query.filter(
        (Message.receiver == 'Everyone') | 
        (Message.receiver == current_user) | 
        (Message.sender == current_user)
    ).order_by(Message.timestamp.asc()).all()
    
    # ለሜሴጅ መምረጫ የሚሆኑ ተጠቃሚዎችን ማምጣት (ከራሱ ውጪ ያሉትን)
    users = User.query.filter(User.username != current_user).all()
    return render_template('index.html', messages=messages, users=users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower() # ወደ ትንሽ ሆሄ መቀየር
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = username
            return redirect(url_for('home'))
        flash('ያልተሳካ ሙከራ! እባክህ መረጃህን አረጋግጥ።')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' not in session or session['username'] != 'admin':
        flash('ተጠቃሚ ለመመዝገብ መጀመሪያ እንደ አድሚን መግባት አለብህ!')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username').strip().lower() # ስሙን ወደ Small letter ይቀይረዋል
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('ይህ ስም ቀድሞ ተይዟል! (በካፒታልም ይሁን በስማል)')
        else:
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.add(User(username=username, password=hashed_pw))
            db.session.commit()
            flash(f'ተጠቃሚ "{username}" በተሳካ ሁኔታ ተመዝግቧል!') # የስኬት መልዕክት
            return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/send', methods=['POST'])
def send():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    content = request.form.get('content')
    receiver = request.form.get('receiver', 'Everyone')
    if content:
        new_msg = Message(sender=session['username'], receiver=receiver, content=content)
        db.session.add(new_msg)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
