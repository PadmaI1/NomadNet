from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User


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


@auth.route("/logout")
def logout():

    logout_user()

    flash("Logged out successfully!")

    return redirect(url_for("locations.home"))