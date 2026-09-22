from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import Comment, db, User, Post, Comment, Like, LocationFollow, Notification, Follow


auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if not username or not email or not password:
            flash("Please fill in all fields.")
            return render_template("auth/signup.html")

        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            flash("Username already exists. Please choose a different username.")
            return render_template("auth/signup.html")

        existing_email = User.query.filter_by(email=email).first()

        if existing_email:
            flash("Email already exists. Please choose a different email.")
            return render_template("auth/signup.html")

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.")

        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username
        ).first()

        if user is None:
            flash("Invalid username or password")
            return render_template("auth/login.html")

        if not check_password_hash(
            user.password,
            password
        ):
            flash("Invalid username or password")
            return render_template("auth/login.html")

        login_user(user)

        flash("Logged in successfully!")

        return redirect(url_for("locations.home"))

    return render_template("auth/login.html")


@auth.route("/logout", methods=["POST"])
def logout():

    logout_user()

    flash("Logged out successfully!")

    return redirect(url_for("locations.home"))

@auth.route("/account/settings")
@login_required
def account_settings():

    return render_template("auth/settings.html")


@auth.route("/account/delete", methods=["POST"])
@login_required
def delete_account():

    user = current_user

    posts = Post.query.filter_by(
        user_id=user.id
    ).all()

    for post in posts:

        Notification.query.filter_by(
            post_id=post.id
        ).delete()

        for media in post.media:

            filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                media.filename
            )

            if os.path.exists(filepath):
                os.remove(filepath)

        db.session.delete(post)

    comments = Comment.query.filter_by(
        user_id=user.id
    ).all()

    for comment in comments:

        Notification.query.filter_by(
            comment_id=comment.id
        ).delete()

        db.session.delete(comment)

    Like.query.filter_by(
        user_id=user.id
    ).delete()

    Follow.query.filter(
        (Follow.follower_id == user.id) |
        (Follow.followed_id == user.id)
    ).delete(
        synchronize_session=False
    )

    LocationFollow.query.filter_by(
        user_id=user.id
    ).delete()

    Notification.query.filter(
        (Notification.recipient_id == user.id) |
        (Notification.actor_id == user.id)
    ).delete(
        synchronize_session=False
    )

    db.session.delete(user)

    db.session.commit()

    logout_user()

    flash("Your account has been deleted.")

    return redirect(
        url_for("auth.login")
    )