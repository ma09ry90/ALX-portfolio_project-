from flask import Flask, render_template, redirect, url_for, flash, request, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import User, Book, Schedule, Collaboration, db
from flask_mail import Mail, Message
from datetime import datetime
from extension import db

UPLOAD_FOLDER = 'uploads'

# Ensure that the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create Flask app instance
app = Flask(__name__, static_folder='static')
app.config.from_object('config.Config')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.urandom(24)

# Initialize the extensions
db.init_app(app)
mail = Mail(app)


@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('Please fill out all fields')
            return redirect('/signup')

        # Corrected hash method
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Add the user to the database
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful!')
        return redirect('/login')

    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        books = Book.query.filter_by(user_id=session['user_id']).all()
        return render_template('dashboard.html', books=books)
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' in session:
        if request.method == 'POST':
            title = request.form.get('title')
            author = request.form.get('author')
            category = request.form.get('category')
            file = request.files.get('file')

            # Debugging print statements
            print(f"Title: {title}")
            print(f"Author: {author}")
            print(f"Category: {category}")
            print(f"File: {file}")

            if not title or not author or not category or not file or file.filename == '':
                flash('All fields are required and a file must be selected.')
                return redirect(request.url)

            file_path = file.filename  # Only the filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))

            # Add book to the database
            new_book = Book(title=title, author=author, file_path=file_path, category=category, user_id=session['user_id'])
            db.session.add(new_book)
            db.session.commit()

            flash('Book uploaded successfully!')
            return redirect(url_for('dashboard'))

        return render_template('upload.html')
    return redirect(url_for('login'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/search', methods=['GET'])
def search():
    if 'user_id' in session:
        query = request.args.get('query')
        books = Book.query.filter(
            (Book.title.like(f'%{query}%')) | 
            (Book.author.like(f'%{query}%'))).filter_by(user_id=session['user_id']).all()
        return render_template('search.html', books=books)
    return redirect(url_for('login'))

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if 'user_id' in session:
        if request.method == 'POST':
            book_id = request.form['book_id']
            reading_time = datetime.strptime(request.form['reading_time'], '%Y-%m-%dT%H:%M')
            
            new_schedule = Schedule(user_id=session['user_id'], book_id=book_id, reading_time=reading_time)
            db.session.add(new_schedule)
            db.session.commit()

            # Send email notification
            book = Book.query.get(book_id)
            user = User.query.get(session['user_id'])
            msg = Message('Reading Schedule Reminder', sender='your-email@example.com', recipients=[user.email])
            msg.body = f"Reminder: It's time to read '{book.title}' by {book.author}!"
            mail.send(msg)

            flash('Reading schedule created successfully, an email reminder will be sent!')
            return redirect(url_for('dashboard'))
        
        books = Book.query.filter_by(user_id=session['user_id']).all()
        return render_template('schedule.html', books=books)
    return redirect(url_for('login'))

@app.route('/invite', methods=['GET', 'POST'])
def invite():
    if 'user_id' in session:
        if request.method == 'POST':
            book_id = request.form['book_id']
            collaborator_username = request.form['collaborator_username']
            permission = request.form['permission']

            collaborator = User.query.filter_by(username=collaborator_username).first()
            if collaborator:
                new_collaboration = Collaboration(book_id=book_id, collaborator_id=collaborator.id, permission=permission)
                db.session.add(new_collaboration)
                db.session.commit()

                flash('User successfully invited!')
                return redirect(url_for('dashboard'))
            else:
                flash('User not found!')
        
        books = Book.query.filter_by(user_id=session['user_id']).all()
        return render_template('invite.html', books=books)
    return redirect(url_for('login'))
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
