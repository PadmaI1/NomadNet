from flask import Flask, render_template, abort, request, session, flash, redirect, url_for, jsonify
from models import db, Country, User, Post, Comment, Like, Follow, Location
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
import requests
from math import radians, sin, cos, sqrt, atan2

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



@app.route("/location/<int:location_id>")
def location_page(location_id):

    location = Location.query.get(location_id)

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

'''
USER
  │
  │ types "Kyoto"
  ↓
JavaScript
  │
  │ input event
  ↓
Read "Kyoto"
  │
  │ fetch()
  ↓
Flask
  │
  ├── Search NomadNet DB
  │
  └── Search Nominatim
  │
  ↓
JSON
  │
  ↓
JavaScript
  │
  │ forEach()
  ↓
Create buttons
  │
  ↓
USER
  │
  │ clicks "Kyoto, Japan"
  ↓
JavaScript
  │
  ├── hidden location_id = 7
  ├── show "Selected: Kyoto"
  └── clear results
  │
  ↓
USER clicks "Post"
  │
  ↓
HTML form submits
  │
  ↓
Flask /posts/create
  │
  ↓
Post(location_id=7)
  │
  ↓
DATABASE
'''
@app.route("/posts/create", methods=["POST"])
@login_required
def create_post():

    content = request.form["content"]
    location_id = request.form.get("location_id")

    if not location_id:
        flash("Please select a location.")
        return redirect(url_for("home"))

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
        location_id = request.form["location_id"]

        if not content.strip():
            flash("Post cannot be empty.")
            return redirect(url_for("edit_post", post_id=post.id))

        location = Location.query.get(location_id)

        if location is None:
            flash("Invalid location selected.")
            return redirect(url_for("edit_post", post_id=post.id))

        post.content = content.strip()
        post.location_id = location.id

        db.session.commit()

        flash("Post updated successfully.")

        return redirect(url_for("home"))

    return render_template(
        "edit_post.html",
        post=post,
        locations=Location.query.all()
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

@app.route("/locations/search")
def search_locations():

    query = request.args.get("q", "").strip()

    if not query:
        return render_template(
            "search_locations.html",
            locations=[],
            api_locations=[],
            query=""
        )

    # 1. Search locations already known to NomadNet
    locations = Location.query.filter(
        Location.name.ilike(f"%{query}%")
    ).all()

    # 2. Nothing found locally → ask Nominatim
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query,
            "format": "json",
            "limit": 5,
            "addressdetails": 1,
            "accept-language": "en"
        },
        headers={
            "User-Agent": "NomadNet/1.0"
        },
        timeout=10
    )

    data = response.json()

    api_locations = []

    for result in data:

        city = (
            result["address"].get("city")
            or result["address"].get("town")
            or result["address"].get("village")
            or result["address"].get("municipality")
        )

        location_data = {
            "name": result.get("name"),
            "type": result.get("addresstype"),
            "country": result["address"].get("country"),
            "city": city,
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "place_id": result.get("place_id"),
            "provider": "openstreetmap",
            "provider_id": str(result["place_id"]),
            "display_name": result.get("display_name")
        }

        api_locations.append(location_data)

    return render_template(
        "search_locations.html",
        locations=locations,
        api_locations=api_locations,
        query=query
    )


@app.route("/locations/create", methods=["POST"])
@login_required
def create_location():
    name = request.form["name"]
    location_type = request.form["type"]
    country = request.form["country"]
    city = request.form["city"]
    latitude = float(request.form["latitude"])
    longitude = float(request.form["longitude"])
    provider = request.form["provider"]
    provider_id = request.form["provider_id"]

    # Check whether this exact external location
    # already exists in NomadNet
    location = Location.query.filter_by(
        provider=provider,
        provider_id=provider_id
    ).first()

    if location:
        return redirect(
            url_for("location_page", location_id=location.id)
        )

    # Location doesn't exist, so create it
    location = Location(
        name=name,
        type=location_type,
        country=country,
        city=city,
        latitude=latitude,
        longitude=longitude,
        provider=provider,
        provider_id=provider_id
    )

    db.session.add(location)
    db.session.commit()

    return redirect(
        url_for("location_page", location_id=location.id)
    )

@app.route("/api/locations/search")
@login_required
def api_search_locations():

    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify({
            "locations": [],
            "api_locations": []
        })

    locations = Location.query.filter(
        Location.name.ilike(f"%{query}%")
    ).all()

    local_locations = []

    for location in locations:
        local_locations.append({
            "id": location.id,
            "name": location.name,
            "type": location.type,
            "country": location.country,
            "city": location.city
        })

    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query,
            "format": "json",
            "limit": 5,
            "addressdetails": 1,
            "accept-language": "en"
        },
        headers={
            "User-Agent": "NomadNet/1.0"
        },
        timeout=10
    )

    data = response.json()

    api_locations = []

    for result in data:

        city = (
            result["address"].get("city")
            or result["address"].get("town")
            or result["address"].get("village")
            or result["address"].get("municipality")
        )

        provider_id = str(result["place_id"])

        existing_location = Location.query.filter_by(
            provider="openstreetmap",
            provider_id=provider_id
        ).first()

        api_locations.append({
            "name": result.get("name"),
            "type": result.get("addresstype"),
            "country": result["address"].get("country"),
            "city": city,
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "provider": "openstreetmap",
            "provider_id": provider_id,
            "display_name": result.get("display_name"),
            "existing_id": existing_location.id if existing_location else None
        })

    return jsonify({
        "locations": local_locations,
        "api_locations": api_locations
    })

@app.route("/api/locations/create", methods=["POST"])
@login_required
def api_create_location():

    location_data = request.get_json()

    name = location_data["name"]
    location_type = location_data["type"]
    country = location_data["country"]
    city = location_data["city"]
    latitude = location_data["latitude"]
    longitude = location_data["longitude"]
    provider = location_data["provider"]
    provider_id = location_data["provider_id"]

    location = Location.query.filter_by(
        provider=provider,
        provider_id=provider_id
    ).first()

    if location:
        return jsonify({
            "id": location.id,
            "name": location.name,
            "country": location.country,
            "city": location.city
        })

    location = Location(
        name=name,
        type=location_type,
        country=country,
        city=city,
        latitude=latitude,
        longitude=longitude,
        provider=provider,
        provider_id=provider_id
    )

    db.session.add(location)
    db.session.commit()

    return jsonify({
        "id": location.id,
        "name": location.name,
        "country": location.country,
        "city": location.city
    })

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371

    lat1 = radians(lat1)
    lon1 = radians(lon1)

    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = earth_radius * c

    return distance

@app.route("/api/locations/nearby")
@login_required
def nearby_locations():

    latitude = request.args.get("latitude", type=float)
    longitude = request.args.get("longitude", type=float)

    if latitude is None or longitude is None:
        return jsonify({
            "error": "Latitude and longitude are required."
        }), 400

    locations = Location.query.all()

    nearby = []

    for location in locations:

        distance = calculate_distance(
            latitude,
            longitude,
            location.latitude,
            location.longitude
        )

        if distance <= 50:

            nearby.append({
                "id": location.id,
                "name": location.name,
                "city": location.city,
                "country": location.country,
                "distance": round(distance, 2),
                "post_count": len(location.posts)
            })

    nearby.sort(key=lambda location: location["distance"])

    return jsonify({
        "locations": nearby
    })
 

@app.errorhandler(404)
def pagenotfound(error):
    return render_template("404.html"), 404



if __name__ == "__main__":

    app.run(debug=True)