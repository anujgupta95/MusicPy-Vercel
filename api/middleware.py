import functools
from flask import session,redirect,url_for, request

#middleware auth
def auth(func):
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return decorated

#middleware guest
def guest(func):
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        if "email" in session:
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return decorated

#middleware creator
def creator(func):
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        if "role" not in session:
            return redirect('/')
        return func(*args, **kwargs)
    return decorated

#middleware admin
def admin(func):
    @functools.wraps(func)
    def decorated(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return decorated

if __name__=="__main__":
    auth()
    guest()
    creator()
    admin()