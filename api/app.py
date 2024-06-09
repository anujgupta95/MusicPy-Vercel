from flask import Flask, render_template, redirect, url_for, session, request
from middleware import auth, guest, creator, admin
from db_config import User, Song, Admin, Like, Playlist, Album, UserPlaylist, app, db, create_admin, default_album
from datetime import datetime
import os

def str_to_date_obj(release_date):
    release_date_obj = datetime.strptime(release_date, '%Y-%m-%d').date()
    return release_date_obj

@app.route('/signup', methods=["GET", "POST"])
@guest
def signup():
    if request.method=="POST":
        name = request.form["name"].strip().capitalize()
        email = request.form["email"].lower()
        password = request.form["password"]
        role = request.form["role"]

        user = User.query.filter_by(email=email).first()
        if user is not None:
            return redirect(url_for('login', message="User already registered! Please sign in."))

        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login', message="Registration successful! You can now log in."))
    return render_template('signup.html')



@app.route('/login', methods=["GET", "POST"])
@guest
def login():
    message = request.args.get("message")
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user is None:
            return render_template('login.html', error="Please sign up First")
    
        if user.isflagged():
            return render_template('login.html',error=f"Your ID has been flagged, Please Contact support")
        
        if not user.check_password(password):
            return render_template('login.html',error="Please recheck your password")

        session["email"] = user.email
        if user.role == "Creator":
            session["role"] = user.role
        return redirect(url_for('index'))

    return render_template('login.html',message=message)

@app.route('/profile', methods=["GET", "POST"])
@auth
def profile():
    if request.method=="POST":
        name = request.form["name"].strip()
        role = request.form['role']

        user = User.query.filter_by(email=session["email"]).first()
        user.name = name
        user.role = role

        if user.role=="User":
            if "role" in session:
                session.pop("role", None)
        else:
            if "role" not in session:
                session['role'] = user.role
                
        db.session.commit()
        user = User.query.filter_by(email=session["email"]).first()
        return render_template('profile.html', user=user, message="Profile updated successfully!!")

    user = User.query.filter_by(email=session["email"]).first()
    return render_template('profile.html', user=user)


@app.route('/song/like/<int:song_id>/<string:return_page>', methods=["GET", "POST", "UPDATE"])
@auth
def like_song(song_id, return_page):
    song = Song.query.filter_by(id=song_id).first()
    user = User.query.filter_by(email=session["email"]).first()
    
    like = Like.query.filter_by(user_id=user.id, song_id=song_id).first()
    
    if like is None:
        like = Like(user.id, song.id)
        db.session.add(like)
        song.likes += 1
    else:
        db.session.delete(like)
        song.likes -= 1

    db.session.commit()
    return redirect(url_for(return_page))

@app.route('/song/like/<int:song_id>/<string:return_page>/<string:search>', methods=["GET", "POST", "UPDATE"])
@auth
def like_song_search(song_id, return_page,search):
    song = Song.query.filter_by(id=song_id).first()
    user = User.query.filter_by(email=session["email"]).first()
    
    like = Like.query.filter_by(user_id=user.id, song_id=song_id).first()
    
    if like is None:
        like = Like(user.id, song.id)
        db.session.add(like)
        song.likes += 1
    else:
        db.session.delete(like)
        song.likes -= 1

    db.session.commit()
    return redirect(url_for(return_page, search=search))

@app.route('/')
@auth
def index():
    user = User.query.filter_by(email=session["email"]).first()
    trending_songs = Song.query.filter_by(flagged="False").order_by(Song.likes.desc()).limit(10).all()
    
    user_playlists = UserPlaylist.query.filter_by(user_id=user.id).all()
    #using to get the playlist name while rendering
    user_playlists_dict = {}
    for user_playlist in user_playlists:
        user_playlists_dict[user_playlist.id] = user_playlist.name

    playlists = db.session.query(UserPlaylist.id, Song).join(Playlist, UserPlaylist.id == Playlist.playlist_id).join(Song, Playlist.song_id == Song.id).filter(Song.flagged == "False").all()
    #Using to find which song is in which playlist
    playlist_dict = {}
    for userplaylist_id, song in playlists:
        if userplaylist_id in playlist_dict:
            playlist_dict[userplaylist_id].append(song)
        else:
            playlist_dict[userplaylist_id] = [song]

    likes = Like.query.filter_by(user_id=user.id).all()
    likes_list= []
    for like in likes:
        likes_list.append(int(like.song_id))

    songs = Song.query.filter_by(flagged="False").all()
    albums_dict = dict()
    for song in songs:
        if song.album in albums_dict:
            albums_dict[song.album].append(song)
        else:
            albums_dict[song.album] = [song]

    return render_template('index.html', user=user,
                            trending_songs=trending_songs,
                            likes_list=likes_list,
                            playlist_dict=playlist_dict,
                            user_playlists_dict=user_playlists_dict,
                            albums_dict=albums_dict)
    



@app.route('/playlist', methods=["GET", "POST"])
@auth
def playlist():
    user = User.query.filter_by(email=session["email"]).first()
    if request.method == "POST":
        playlist_name = request.form["playlist_name"].strip()
        new_playlist = UserPlaylist(user_id=user.id, name=playlist_name)
        db.session.add(new_playlist)
        db.session.commit()
        return redirect(request.url)
    
    likes = Like.query.filter_by(user_id=user.id).all()
    likes_list= []
    for like in likes:
        likes_list.append(int(like.song_id))

    user_playlists = UserPlaylist.query.filter_by(user_id=user.id).all()
    #using to get the playlist name while rendering
    user_playlists_dict = {}
    for user_playlist in user_playlists:
        user_playlists_dict[user_playlist.id] = user_playlist.name

    playlists = db.session.query(UserPlaylist.id, Song).join(Playlist, UserPlaylist.id == Playlist.playlist_id).join(Song, Playlist.song_id == Song.id).filter(Song.flagged == "False", UserPlaylist.user_id==user.id).all()
    playlist_dict = {}
    for playlist_id, song in playlists:
        if playlist_id in playlist_dict:
            playlist_dict[playlist_id].append(song)
        else:
            playlist_dict[playlist_id] = [song]

    return render_template('playlist.html', user=user, likes_list=likes_list, user_playlists_dict=user_playlists_dict, playlist_dict=playlist_dict)


@app.route('/playlist/edit/<int:playlist_id>/<int:song_id>/<string:return_page>', methods=["GET", "POST", "UPDATE"])
@auth
def playlist_add_song(playlist_id, song_id, return_page):
    song_in_playlist = Playlist.query.filter_by(song_id=song_id, playlist_id=playlist_id).first()

    if song_in_playlist is None:
        newsong = Playlist(song_id=song_id, playlist_id=playlist_id)
        db.session.add(newsong)
    else:
        db.session.delete(song_in_playlist)

    db.session.commit()
    return redirect(url_for(return_page))

@app.route('/playlist/edit/<int:playlist_id>/<int:song_id>/<string:return_page>/<string:search>', methods=["GET", "POST", "UPDATE"])
@auth
def playlist_add_song_search(playlist_id, song_id, return_page, search):
    song_in_playlist = Playlist.query.filter_by(song_id=song_id, playlist_id=playlist_id).first()

    if song_in_playlist is None:
        newsong = Playlist(song_id=song_id, playlist_id=playlist_id)
        db.session.add(newsong)
    else:
        db.session.delete(song_in_playlist)

    db.session.commit()
    return redirect(url_for(return_page,search=search))


@app.route('/playlist/delete/<int:user_playlist_id>/<string:return_page>' , methods=["GET", "POST", "UPDATE"])
@auth
def delete_playlist(user_playlist_id, return_page):
    user_playlist = UserPlaylist.query.filter_by(id=user_playlist_id).first()
    songs_in_playlist = Playlist.query.filter_by(playlist_id=user_playlist_id).all()
    for song in songs_in_playlist:
        db.session.delete(song)

    db.session.delete(user_playlist)
    db.session.commit()
    return redirect(url_for(return_page))


@app.route('/search')
@auth
def search():
    search = request.args.get("search")
    user = User.query.filter_by(email=session["email"]).first()

    user_playlists = UserPlaylist.query.filter_by(user_id=user.id).all()
    user_playlists_dict = {}
    for user_playlist in user_playlists:
        user_playlists_dict[user_playlist.id] = user_playlist.name

    playlists = db.session.query(UserPlaylist.id, Song).join(Playlist, UserPlaylist.id == Playlist.playlist_id).join(Song, Playlist.song_id == Song.id).filter(Song.flagged == "False", UserPlaylist.user_id==user.id).all()
    playlist_dict = {}
    for playlist_id, song in playlists:
        if playlist_id in playlist_dict:
            playlist_dict[playlist_id].append(song)
        else:
            playlist_dict[playlist_id] = [song]

    likes = Like.query.filter_by(user_id=user.id).all()
    likes_list= []
    for like in likes:
        likes_list.append(int(like.song_id))

    # search_results = Song.query.filter_by(flagged="False").filter(Song.name.icontains(search)).order_by(Song.likes.desc()).all()
    search_results = db.session.query(Album, Song).join(Album, Album.name==Song.album
                                                    ).filter(Song.flagged=="False", Album.flagged=="False"
                                                    ).filter(Song.name.icontains(search) | Album.name.icontains(search) 
                                                    | Album.artist.icontains(search) | Album.genre.icontains(search)).order_by(Song.likes.desc()).all()  
    albums_dict = dict()
    for album, song in search_results:
        album_name = album.name
        if song.album in albums_dict:
            albums_dict[album_name].append(song)
        else:
            albums_dict[album_name] = [song]
    return render_template('search results.html', user=user,
                        search=search,albums_dict=albums_dict,
                        user_playlists_dict=user_playlists_dict,
                        playlist_dict=playlist_dict,likes_list=likes_list)

    

@app.route('/logout')
@auth
def logout():
    session.pop("email", None)
    if "role" in session:
        session.pop("role", None)
    return redirect('/login')


@app.route('/upload/song', methods=["GET", "POST"])
@creator
@auth
def upload_song():
    user = User.query.filter_by(email = session['email']).first()
    albums = Album.query.all()
    if request.method=="POST":
        name = request.form["name"].strip().capitalize()
        album = request.form["album"]
        release_date = str_to_date_obj(request.form['release_date']) #Converted to date object
        lyrics = request.form["lyrics"]
        mp3file = request.files["mp3file"]

        if mp3file and mp3file.filename.endswith('.mp3'):
            new_song = Song(name=name, album=album, lyrics=lyrics, release_date=release_date, creator_id=user.id)
            db.session.add(new_song)

            temp = Song.query.filter_by(name=name, lyrics=lyrics, release_date=release_date, creator_id=user.id).first()
            file_path = f"{app.config['UPLOAD_FOLDER']}/{temp.id}.mp3"
            mp3file.save(file_path)
            temp.url = file_path
            db.session.commit()

            return render_template('creator upload.html', message=f"Song uploaded successfully! ID: {temp.id}", user=user, albums=albums)
        else:
            return render_template('creator upload.html', error='Upload MP3 file only', user=user, albums=albums)
    return render_template('creator upload.html', user=user, albums=albums)

@app.route('/album/create', methods=["GET", "POST"])
@creator
@auth
def create_album():
    user = User.query.filter_by(email = session['email']).first()
    albums = Album.query.all()
    if request.method=="POST":
        name = request.form["name"].strip()
        genre = request.form["genre"].capitalize()
        artist = request.form["artist"].capitalize()

        existing_album = Album.query.filter_by(name=name, genre=genre).first()
        if existing_album:
            return render_template('creator upload.html', error=f"Album already exists!!", user=user, albums=albums)
        else:
            new_album = Album(name=name, genre=genre, artist=artist, creator_id=user.id)
            db.session.add(new_album)
            db.session.commit()
            return redirect(request.url)
    return render_template('creator album.html', user=user, albums=albums)

@app.route('/album/edit/<int:album_id>', methods=["GET", "POST"])
@creator
@auth
def edit_album(album_id):
    user = User.query.filter_by(email=session['email']).first()
    album = Album.query.filter_by(id=album_id).first()
    if request.method == "POST":
        clicked_button  = request.form["button"]
        if clicked_button == "save":
            old_album_name = album.name
            album.name = request.form["name"].strip()
            album.genre = request.form["genre"].capitalize()
            album.artist = request.form["artist"].capitalize()

            songs = Song.query.filter_by(album=old_album_name).all()

            for song in songs: 
                song.album = album.name
            db.session.commit()
            
            temp = Album.query.filter_by(id=album_id).first()
            return render_template('creator edit album.html', message="Album details edited successfully!!", user=user, album=temp)
        elif clicked_button == "delete":
            name = album.name
            songs = Song.query.filter_by(album=album.name).all()
            for song in songs: 
                song.album = default_album
            db.session.delete(album)
            db.session.commit()
            return redirect(url_for('create_album', message=f"Album {name} deleted successfully!!"))
    return render_template('creator edit album.html', user=user, album=album)

@app.route('/creator/dashboard')
@creator
@auth
def creator_dashboard():
        user = User.query.filter_by(email=session["email"]).first()
        albums = Album.query.filter_by(creator_id=user.id).all()
        songs = Song.query.filter_by(creator_id=user.id).order_by(Song.likes.desc()).all()
        songs_likes = []
        for song in songs:
            songs_likes.append(song.likes)

        flagged_songs = Song.query.filter_by(creator_id=user.id, flagged="True").all()
        message = request.args.get("message")
        count = {"songs_count": len(songs),
                "flagged_songs_count": len(flagged_songs),
                "albums_count": len(albums),
                "avg_rating" : round(sum(songs_likes)/len(songs_likes), 2) if len(songs_likes)>0 else 0}
        return render_template('creator dashboard.html',message=message, user=user, songs=songs, count=count)

@app.route('/song/edit/<int:song_id>', methods=["GET", "POST"])
@creator
def creator_edit_song(song_id):
    song = Song.query.filter_by(id=song_id).first()
    user = User.query.filter_by(email=session["email"]).first()
    albums = Album.query.all()
    if request.method == "POST":
        clicked_button  = request.form["button"]
        if clicked_button == "save":
            song.name = request.form["name"].strip().capitalize()
            song.album = request.form["album"]
            song.release_date = str_to_date_obj(request.form['release_date']) #Converted to date object
            song.lyrics = request.form["lyrics"]
            db.session.commit()
            
            temp = Song.query.filter_by(id=song_id).first()
            return render_template('creator edit song.html', song=temp, message="Song details edited successfully!!", user=user, albums=albums)
        else:
            name = song.name
            db.session.delete(song)
            os.remove(f"{app.config['UPLOAD_FOLDER']}/{song.id}.mp3")
            db.session.commit()
            return redirect(url_for('creator_dashboard', message=f"{name} deleted successfully!!",albums=albums))
    return render_template('creator edit song.html', song=song, user=user, albums=albums)


@app.route('/admin/login', methods=["GET", "POST"])
def admin_login():
    message = request.args.get("message")
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        admin = Admin.query.filter_by(email=email).first()

        if admin is None:
            return render_template('admin login.html', error="Please use admin credentials")

        if not admin.check_password(password):
            return render_template('admin login.html',error="Please recheck your password")

        if admin and admin.check_password(password):
            # session["role"] = "admin"
            session["admin"] = "admin"
            return redirect(url_for('admin_dashboard'))
    return render_template('admin login.html',message=message)

@app.route('/admin/dashboard')
@admin
def admin_dashboard():
        message = request.args.get("message")
        # admin = Admin.query.filter_by(email=session["email"]).first()
        users = User.query.filter_by(role="User").all()
        albums = Album.query.all()
        songs = Song.query.order_by(Song.likes.desc()).limit(5).all()
        creators = User.query.filter_by(role="Creator").all()
        flagged_songs = Song.query.filter_by(flagged="True").all()
        flagged_users = User.query.filter_by(flagged="True", role="User").all()
        flagged_creators = User.query.filter_by(flagged="True", role="Creator").all()
        count = {"songs_count" : len(songs), "users_count" : len(users),
                 "creators_count" : len(creators),
                 "albums_count" : len(albums),
                 "flagged_users" : len(flagged_users), "flagged_songs" : len(flagged_songs),
                 "flagged_creators" : len(flagged_creators)
                }

        return render_template('admin dashboard.html', songs=songs, message=message, count = count)

@app.route('/admin/song/all')
@admin
def admin_all_songs():
        message = request.args.get("message")
        songs = Song.query.all()
        return render_template('admin all songs.html', message=message, songs=songs)

@app.route('/admin/album/all')
@admin
def admin_all_albums():
        message = request.args.get("message")
        albums = Album.query.all()
        return render_template('admin all albums.html', message=message, albums=albums)

@app.route('/admin/user/all')
@admin
def admin_all_users():
        message = request.args.get("message")
        users = User.query.all()
        # users = db.session.query(User,db.func.count(Song.id).label('total_songs')).join(Song, User.id == Song.creator_id).group_by(User.id).all() 
        return render_template('admin all users.html', message=message, users=users)

@app.route('/admin/song/edit/<int:song_id>', methods=["GET", "POST"])
@admin
def admin_edit_song(song_id):
    song = Song.query.filter_by(id=song_id).first()
    user = User.query.filter_by(id=song.creator_id).first()
    if request.method == "POST":
        clicked_button  = request.form["button"]
        name = song.name
        if clicked_button == "flag":
            song.flagged = "True"
            db.session.commit()

            temp = Song.query.filter_by(id=song_id).first()
            return render_template('admin edit song.html', song=temp, message=f"{name} by {user.name} flagged successfully!!", user=user)
        elif clicked_button == "unflag":
            song.flagged = "False"
            db.session.commit()

            temp = Song.query.filter_by(id=song_id).first()
            return render_template('admin edit song.html', song=temp, message=f"{name} by {user.name} unflagged successfully!!", user=user)
        elif clicked_button == "delete":
            likes = Like.query.filter_by(song_id=song.id).all()
            for like in likes:
                db.session.delete(like)
            playlists = Playlist.query.filter_by(song_id=song.id).all()
            for playlist in playlists:
                db.session.delete(playlist)
            db.session.delete(song)
            os.remove(f"{app.config['UPLOAD_FOLDER']}/{song.id}.mp3")
            db.session.commit()
            return redirect(url_for('admin_all_songs', message=f"{name} by {user.name} deleted successfully!!"))
    return render_template('admin edit song.html', song=song, user=user)

@app.route('/admin/album/edit/<int:album_id>', methods=["GET", "POST"])
@admin
def admin_edit_album(album_id):
    album = Album.query.filter_by(id=album_id).first()
    songs = Song.query.filter_by(album=album.name).all()
    user = User.query.filter_by(id=album.creator_id).first()

    if request.method == "POST":
        clicked_button  = request.form["button"]
        if clicked_button == "flag":
            album.flagged = "True"
            for song in songs:
                song.flagged = "True"
            db.session.commit()

            updated_songs = Song.query.filter_by(album=album.name).all()
            updated_album = Album.query.filter_by(id=album_id).first()
            return render_template('admin edit album.html', songs=updated_songs, message=f"{album.name} by {user.name} flagged successfully!!", album=updated_album, user=user)
        elif clicked_button == "unflag":
            album.flagged = "False"
            for song in songs:
                song.flagged = "False"
            db.session.commit()

            updated_songs = Song.query.filter_by(album=album.name).all()
            updated_album = Album.query.filter_by(id=album_id).first()
            return render_template('admin edit album.html', songs=updated_songs, message=f"{album.name} by {user.name} unflagged successfully!!", album=updated_album, user=user)
        elif clicked_button == "delete_with_songs":
            for song in songs:
                likes = Like.query.filter_by(song_id=song.id).all()
                for like in likes:
                    db.session.delete(like)
                playlists = Playlist.query.filter_by(song_id=song.id).all()
                for playlist in playlists:
                    db.session.delete(playlist)
                os.remove(f"{app.config['UPLOAD_FOLDER']}/{song.id}.mp3")
                db.session.delete(song)
            db.session.delete(album)
            db.session.commit()
            return redirect(url_for('admin_all_albums', message=f"{album.name} by {user.name} deleted successfully with songs!!"))
        elif clicked_button == "delete_without_songs":
            for song in songs:
                song.album = default_album
            db.session.delete(album)
            db.session.commit()
            return redirect(url_for('admin_all_albums', message=f"{album.name} by {user.name} deleted successfully!!"))
        
    return render_template('admin edit album.html', songs=songs, album=album, user=user)

@app.route("/admin/user/edit/<int:user_id>", methods=["GET", "POST"])
@admin
def admin_edit_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    if request.method == "POST":
        clicked_button  = request.form["button"]
        name = user.name
        if clicked_button == "flag":
            user.flagged = "True"
            songs = Song.query.filter_by(creator_id=user.id).all()
            for song in songs:
                song.flagged = "True"
            db.session.commit()

            temp = User.query.filter_by(id=user_id).first()
            return render_template('admin edit user.html', message=f"User {name} flagged successfully!!", user=temp)
        
        elif clicked_button == "unflag":
            user.flagged = "False"
            songs = Song.query.filter_by(creator_id=user.id).all()
            for song in songs:
                song.flagged = "False"
            db.session.commit()

            temp = Song.query.filter_by(id=user_id).first()
            return render_template('admin edit user.html', message=f"User {name} unflagged successfully!!", user=user, song=temp)
        
        elif clicked_button == "delete":
            songs = Song.query.filter_by(creator_id=user.id).all()
            for song in songs:
                db.session.delete(song)
            likes = Like.query.filter_by(user_id=user.id).all()
            for like in likes:
                db.session.delete(like)
            albums = Album.query.filter_by(creator_id=user.id).all()
            for album in albums:
                db.session.delete(album)
            userplaylists = UserPlaylist.query.filter_by(id=user.id).all()
            for userplaylist in userplaylists:
                playlists = Playlist.query.filter_by(playlist_id=userplaylist.id).all()
                for playlist in playlists:
                    db.session.delete(playlist)
                db.session.delete(userplaylist)
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('admin_all_users', message=f"User {name} deleted successfully!!"))
    return render_template('admin edit user.html', user=user)

@app.route('/admin/logout')
@admin
def admin_logout():
    session.pop("admin", None)
    return redirect('/admin/login')

if __name__ == '__main__':
    create_admin()
    app.run(port=6000, debug=True)