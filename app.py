from flask import Flask, render_template, abort, request, session, flash, redirect, url_for
from models import db, Country, User, Post, Comment, Like, Follow, Location
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate
import os
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nomadnet.db'

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

login_manager.login_view = "login"

@app.route("/")
def home():

    countries = Country.query.all()
    locations = Location.query.all()

    if current_user.is_authenticated:

        following = Follow.query.filter_by(
            follower_id=current_user.id
        ).all()

        user_ids = [current_user.id]

        for follow in following:
            user_ids.append(follow.followed_id)

        posts = Post.query.filter(
            Post.user_id.in_(user_ids)
        ).order_by(
            Post.created_at.desc()
        ).all()

    else:

        posts = Post.query.order_by(
            Post.created_at.desc()
        ).all()

    return render_template(
        "home.html",
        countries=countries,
        locations=locations,
        posts=posts
    )


@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/country/<country_name>")
def country_page(country_name):

    country = Country.query.filter_by(
        name=country_name
    ).first()

    if country is None:
        abort(404)

    posts = Post.query.filter_by(
        country_id=country.id
    ).order_by(
        Post.created_at.desc()
    ).all()

    return render_template(
        "country.html",
        country=country,
        posts=posts
    )

@app.route("/location/<location_name>")
def location_page(location_name):

    location = Location.query.filter_by(
        name=location_name
    ).first()

    if location is None:
        abort(404)

    posts = Post.query.filter_by(
        location_id=location.id
    ).order_by(
        Post.created_at.desc()
    ).all()

    return render_template(
        "location.html",
        location=location,
        posts=posts
    )

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if not username or not email or not password:
            flash("Please fill in all fields.")
            return render_template("signup.html")

        existing_username = User.query.filter_by(username=username).first()

        if existing_username:
            flash("Username already exists. Please choose a different username.")
            return render_template("signup.html")

        existing_email = User.query.filter_by(email=email).first()  

        if existing_email:
            flash("Email already exists. Please choose a different email.")
            return render_template("signup.html")

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.")

        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user is None:
            flash("Invalid email or password")
            return render_template("login.html")

        if not check_password_hash(
            user.password,
            password):
            flash("Invalid email or password")
            return render_template("login.html")

        login_user(user)

        flash("Logged in successfully!")
        return redirect(url_for("home"))

    return render_template("login.html")

@app.route("/user/<username>")
def profile(username):

    user = User.query.filter_by(
        username=username
    ).first()

    if user is None:
        abort(404)

    posts = Post.query.filter_by(
        user_id=user.id
    ).order_by(
        Post.created_at.desc()
    ).all()

    is_following = False

    if current_user.is_authenticated:
        existing_follow = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user.id
        ).first()

        if existing_follow:
            is_following = True
            
    return render_template(
        "profile.html",
        user=user,
        posts=posts,
        is_following=is_following
    )

@app.route("/logout")
def logout():

    logout_user()

    flash("Logged out successfully!")
    return redirect(url_for("home"))

@app.route("/posts/create", methods=["POST"])
@login_required
def create_post():

    content = request.form["content"]
    location_id = request.form["location_id"]

    if not content.strip():
        flash("Post cannot be empty.")
        return redirect(url_for("home"))

    location = Location.query.get(location_id)

    if not location:
        flash("Invalid location.")
        return redirect(url_for("home"))

    post = Post(
        content=content,
        user_id=current_user.id,
        location_id=location.id
    )

    db.session.add(post)
    db.session.commit()

    flash("Post created successfully!")

    return redirect(url_for("home"))

@app.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    if post.user_id != current_user.id:
        abort(403)

    db.session.delete(post)
    db.session.commit()

    flash("Post deleted successfully.")

    return redirect(url_for("home"))

@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    if post.user_id != current_user.id:
        abort(403)

    if request.method == "POST":

        content = request.form["content"]
        country_id = request.form["country_id"]

        if not content.strip():
            flash("Post cannot be empty.")
            return redirect(url_for("edit_post", post_id=post.id))

        country = Country.query.get(country_id)

        if country is None:
            flash("Invalid country selected.")
            return redirect(url_for("edit_post", post_id=post.id))

        post.content = content.strip()
        post.country_id = country.id

        db.session.commit()

        flash("Post updated successfully.")

        return redirect(url_for("home"))

    return render_template(
        "edit_post.html",
        post=post,
        countries=Country.query.all()
    )

@app.route("/posts/<int:post_id>")
def post_detail(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    return render_template(
        "post_details.html",
        post=post
    )

@app.route("/posts/<int:post_id>/comments/create", methods=["POST"])
@login_required
def create_comment(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    content = request.form["content"]

    if not content.strip():
        flash("Comment cannot be empty.")
        return redirect(url_for("post_detail", post_id=post.id))

    comment = Comment(
        content=content.strip(),
        user_id=current_user.id,
        post_id=post.id
    )

    db.session.add(comment)
    db.session.commit()

    flash("Comment added successfully.")

    return redirect(url_for("post_detail", post_id=post.id))

@app.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):

    comment = Comment.query.get(comment_id)

    if comment is None:
        abort(404)

    if comment.user_id != current_user.id:
        abort(403)

    post_id = comment.post_id

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted successfully.")

    return redirect(url_for("post_detail", post_id=post_id))

@app.route("/posts/<int:post_id>/like", methods=["POST"])
@login_required
def like_post(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    existing_like = Like.query.filter_by(
        user_id=current_user.id,
        post_id=post.id
    ).first()

    if existing_like:

        db.session.delete(existing_like)
        db.session.commit()

        flash("Post unliked.")

    else:

        like = Like(
            user_id=current_user.id,
            post_id=post.id
        )

        db.session.add(like)
        db.session.commit()

        flash("Post liked.")

    return redirect(
        url_for("post_detail", post_id=post.id)
    )

@app.route("/user/<username>/follow", methods=["POST"])
@login_required
def follow_user(username):

    user = User.query.filter_by(username=username).first()

    if user is None:
        abort(404)

    if user.id == current_user.id:
        flash("You cannot follow yourself.")
        return redirect(
            url_for("profile", username=user.username)
        )

    existing_follow = Follow.query.filter_by(
        follower_id=current_user.id,
        followed_id=user.id
    ).first()

    if existing_follow:

        db.session.delete(existing_follow)
        db.session.commit()

        flash(f"You unfollowed {user.username}.")

    else:

        follow = Follow(
            follower_id=current_user.id,
            followed_id=user.id
        )

        db.session.add(follow)
        db.session.commit()

        flash(f"You are now following {user.username}.")

    return redirect(
        url_for("profile", username=user.username)
    )

@app.errorhandler(404)
def pagenotfound(error):
    return render_template("404.html"), 404



if __name__ == "__main__":

    app.run(debug=True)