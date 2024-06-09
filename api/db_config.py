from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
# from datetime import timedelta


app = Flask(__name__,template_folder='templates')
# app.permanent_session_lifetime = timedelta(minutes=30)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite3"
db = SQLAlchemy(app)
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.secret_key = "secret_key0"

class Song(db.Model):
    __tablename__ = 'Song'
    id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    album = db.Column(db.String, db.ForeignKey('Album.name'), nullable=False)
    lyrics = db.Column(db.String, nullable=False)
    release_date = db.Column(db.DATE, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey("User.id"),  nullable=False)
    url = db.Column(db.TEXT)
    flagged = db.Column(db.String, nullable=False, default="False")
    likes = db.Column(db.Integer)

    def __init__(self, name, lyrics, release_date, creator_id, album, url=None, flagged="False"):
        self.name = name
        self.lyrics = lyrics
        self.release_date = release_date
        self.creator_id = creator_id
        self.album = album
        self.url = url
        self.flagged = flagged
        self.likes = 0

    def isflagged(self):
        return self.flagged=="True"

class Album(db.Model):
    __tablename__ = 'Album'
    id = id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String, nullable=False, unique=True)
    genre = db.Column(db.String, nullable=False, unique=True)
    artist = db.Column(db.String, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('User.id'), nullable=False)
    flagged = db.Column(db.String, nullable=False, default="False")

    def __init__(self, name, genre, artist, creator_id, flagged="False"):
        self.name = name
        self.genre = genre
        self.artist = artist
        self.creator_id = creator_id
        self.flagged = flagged


class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)
    flagged = db.Column(db.String, nullable=False, default="False")

    def __init__(self, name, email, password, role, flagged="False"):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.role = role
        self.flagged = flagged
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

    def isflagged(self):
        return self.flagged=="True"
    
class Admin(db.Model):
    __tablename__ = 'Admin'
    id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        #Hashed password for security
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
    
class Like(db.Model):
    __tablename__ = 'Like'
    id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"),  nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey("Song.id"),  nullable=False)

    def __init__(self, user_id, song_id):
        self.user_id = user_id
        self.song_id = song_id

class UserPlaylist(db.Model):
    __tablename__ = 'UserPlaylist'
    id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    name = db.Column(db.String,  nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("User.id"),  nullable=False)

    def __init__(self, user_id, name):
        self.name = name
        self.user_id = user_id
        
class Playlist(db.Model):
    __tablename__ = 'Playlist'
    id = db.Column(db.Integer, nullable=False, primary_key=True, unique=True, autoincrement=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey("UserPlaylist.id"),  nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey("Song.id"),  nullable=False)

    def __init__(self, playlist_id, song_id):
        self.playlist_id = playlist_id
        self.song_id = song_id


with app.app_context():
    db.create_all()

default_album = "No Album"

def create_admin():
    with app.app_context():
        existing_admin = Admin.query.first()
        if existing_admin is None:
            admin = Admin("Admin", "admin@musicpy.com", "admin")
            db.session.add(admin)
            db.session.commit()

        existing_album = Album.query.filter_by(name=default_album).first()
        if existing_album is None:
            album = Album(default_album, "Mixed", "Multiple Artists", -1)
            db.session.add(album)
            db.session.commit()

if __name__=="__main__":
    User()
    Song()
    Album()
    Admin()
    Like()
    Playlist()
    app
    db
    default_album
    create_admin()