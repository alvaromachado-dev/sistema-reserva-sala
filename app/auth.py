from flask import Blueprint, render_template, request, redirect
from .models import User
from . import db, login_manager
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/")

    return render_template("login.html")

@auth.route("/register", methods=["POST"])
def register():
    user = User(
        username=request.form["username"],
        password=generate_password_hash(request.form["password"])
    )
    db.session.add(user)
    db.session.commit()
    return redirect("/login")

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")