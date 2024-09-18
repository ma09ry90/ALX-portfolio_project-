from flask_sqlalchemy import SQLAlchemy
from extension import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author = db.Column(db.String(100))
    file_path = db.Column(db.String(200))
    category = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, author, file_path, category, user_id):
        self.title = title
        self.author = author
        self.file_path = file_path
        self.category = category
        self.user_id = user_id

class Collaboration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    collaborator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    permission = db.Column(db.String(50))  # 'view', 'download', 'organize'

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    reading_time = db.Column(db.DateTime, nullable=False)