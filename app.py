@app.route('/register', methods=['GET', 'POST'])
def register():
    # አድሚን መሆኑን ማረጋገጥ - አድሚን ካልገባ ወደ መግቢያ ገጽ ይመልሰዋል
    if 'username' not in session or session['username'] != 'admin':
        flash('ተጠቃሚ ለመመዝገብ መጀመሪያ እንደ አድሚን መግባት አለብህ!')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('ይህ ስም ቀድሞ ተይዟል!')
        else:
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.add(User(username=username, password=hashed_pw))
            db.session.commit()
            flash(f'ተጠቃሚ {username} በተሳካ ሁኔታ ተመዝግቧል!')
            return redirect(url_for('home')) # ከተመዘገበ በኋላ ወደ ሆም ይመልሰዋል
            
    return render_template('register.html')
