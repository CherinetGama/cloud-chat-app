import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "amu_lab_secret_key_123" # ሚስጥራዊ ቁልፍ

# SQLite ዳታቤዝ ማዋቀር
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# የፋይል ወይም ፎቶ መላኪያ ማዋቀር
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# የፎቶዎች ማስቀመጫ ፎልደር ከሌለ እንዲፈጠር ማድረግ
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = SQLAlchemy(app)

# --- የዳታቤዝ ሞዴሎች (Database Models) ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(500), nullable=True)
    image_path = db.Column(db.String(200), nullable=True)

# ፋይሉ የሚፈቀድ የፎቶ አይነት መሆኑን መፈተሻ
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ዳታቤዙን መጀመሪያ ላይ መፍጠር
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        hashed_pw = generate_password_hash('admin123', method='pbkdf2:sha256')
        admin_user = User(username='admin', password=hashed_pw)
        db.session.add(admin_user)
        db.session.commit()

# --- የፍላስክ መንገዶች (Routes) ---

# 1. ዋናው የቻት ገጽ (Index)
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = session['username']
    users = User.query.filter(User.username != current_user).all()
    
    messages = Message.query.filter(
        (Message.receiver == 'Everyone') | 
        (Message.sender == current_user) | 
        (Message.receiver == current_user)
    ).all()
    
    return render_template('index.html', users=users, messages=messages)

# 2. መልዕክት እና ፎቶ መላኪያ (Send Message & Photo)
@app.route('/send', methods=['POST'])
def send():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    sender = session['username']
    receiver = request.form.get('receiver', 'Everyone')
    content = request.form.get('content', '')
    
    file = request.files.get('file')
    file_url = None
    
    if file and file.filename != '' and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"{sender}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = f"uploads/{filename}"
        
    if content or file_url:
        new_msg = Message(sender=sender, receiver=receiver, content=content, image_path=file_url)
        db.session.add(new_msg)
        db.session.commit()
        
    return redirect(url_for('index'))

# 3. መግቢያ ገጽ (Login)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower() # ወደ small letter ይቀይራል
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash("ያልተሳካ ሙከራ! እባክዎ መረጃውን ያረጋግጡ።")
            return redirect(url_for('login'))
            
    return render_template('login.html')

# 4. አዲስ ተጠቃሚ መመዝገቢያ (Register - ለአድሚን ብቻ)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' not in session or session['username'] != 'admin':
        return "ይህንን ገጽ ለመጠቀም የአድሚን ፈቃድ ያስፈልጋል!", 403
        
    if request.method == 'POST':
        username = request.form.get('username').strip().lower() # በትንሽ ሆሄ እንዲመዘገብ
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash("ይህ ተጠቃሚ ስም አስቀድሞ ተመዝግቧል!")
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        # እዚህ ጋ መልዕክቱን 'flash' እናደርጋለን
        flash(f'ተጠቃሚ "{username}" በተሳካ ሁኔታ ተመዝግቧል!')
        return redirect(url_for('index')) # ወደ ዋናው ገጽ ይመልሰዋል
        
    return render_template('register.html')

# 5. መውጫ (Logout)
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
