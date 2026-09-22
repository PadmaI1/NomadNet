from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from models import Comment, db, User, Post, Comment, Like, LocationFollow, Notification, Follow, Location
from forms import LoginForm, SignupForm, DeleteAccountForm, LogoutForm


auth = Blueprint("auth", __name__)


def _auth_showcase():
    """A handful of random hero location images, cycled behind the login/signup panels."""
    hero_locations = Location.query.filter(
        Location.hero_image_url.isnot(None)
    ).order_by(db.func.random()).limit(6).all()

    return {
        "hero_location": hero_locations[0] if hero_locations else None,
        "hero_locations": hero_locations,
    }


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    """
    User registration route.

    GET: Show signup form.
    POST: Validate form, then create user if validation passes.

    The SignupForm automatically:
    - Validates that username/email/password are not empty
    - Checks that username doesn't already exist
    - Checks that email doesn't already exist
    - Checks that passwords match
    - Checks password is at least 6 characters

    If any validation fails, form.validate_on_submit() returns False,
    and form.errors contains the error messages.
    """
    form = SignupForm()

    if form.validate_on_submit():
        # Validation passed. Data is clean and safe.
        hashed_password = generate_password_hash(form.password.data)

        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.")
        return redirect(url_for("auth.login"))

    # GET request OR POST with validation errors
    return render_template("auth/signup.html", form=form, **_auth_showcase())


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    User login route.

    GET: Show login form.
    POST: Validate form, then check password and log in if correct.

    The LoginForm validates that username and password are not empty.
    We still need to check the password is correct (that's not a form validator,
    that's application logic).
    """
    form = LoginForm()

    if form.validate_on_submit():
        # Form validation passed. Look up the user.
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not check_password_hash(user.password, form.password.data):
            flash("Invalid username or password")
            # Don't clear the form — user might just have wrong password
            return render_template("auth/login.html", form=form, **_auth_showcase())

        login_user(user)
        flash("Logged in successfully!")
        return redirect(url_for("locations.home"))

    # GET request OR POST with validation errors
    return render_template("auth/login.html", form=form, **_auth_showcase())


@auth.route("/logout", methods=["POST"])
def logout():
    """
    User logout route.

    We accept only POST (not GET) to prevent URL-based attacks.
    The LogoutForm holds the CSRF token, protecting this route.
    """
    form = LogoutForm()

    if form.validate_on_submit():
        logout_user()
        flash("Logged out successfully!")

    return redirect(url_for("locations.home"))


@auth.route("/account/settings")
@login_required
def account_settings():
    """Settings page for the logged-in user."""
    form = DeleteAccountForm()
    return render_template("auth/settings.html", delete_form=form)


@auth.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    """
    Delete the user's account and all associated data.

    This is a destructive operation, so:
    1. We require POST (not GET)
    2. We require CSRF token (form validation)
    3. We cascade-delete all user data
    """
    form = DeleteAccountForm()

    if not form.validate_on_submit():
        flash("Delete request failed. Please try again.")
        return redirect(url_for("auth.account_settings"))

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