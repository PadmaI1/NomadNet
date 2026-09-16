from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
import requests
from models import db, Country, Follow, Post, Location, LocationFollow, Like, Comment
from datetime import datetime, timedelta


locations = Blueprint("locations", __name__)


@locations.route("/")
def home():

    countries = Country.query.all()
    locations = Location.query.all()

    cutoff = datetime.utcnow() - timedelta(days=7)

    recently_active_locations = (
        db.session.query(Location)
        .join(Post, Post.location_id == Location.id)
        .filter(Post.created_at >= cutoff)
        .group_by(Location.id)
        .order_by(db.func.max(Post.created_at).desc())
        .limit(10)
        .all()
    )

    trending_post_counts = (
    db.session.query(
        Post.location_id,
        db.func.count(Post.id)
    )
    .filter(Post.created_at >= cutoff)
    .group_by(Post.location_id)
    .all()
    )

    trending_like_counts = (
    db.session.query(
        Post.location_id,
        db.func.count(Like.id)
    )
    .join(Like, Like.post_id == Post.id)
    .filter(Post.created_at >= cutoff)
    .group_by(Post.location_id)
    .all()
    )

    trending_comment_counts = (
    db.session.query(
        Post.location_id,
        db.func.count(Comment.id)
    )
    .join(Comment, Comment.post_id == Post.id)
    .filter(Post.created_at >= cutoff)
    .group_by(Post.location_id)
    .all()
    )

    post_counts = dict(trending_post_counts)
    like_counts = dict(trending_like_counts)
    comment_counts = dict(trending_comment_counts)

    trending_scores = []

    for location_id, post_count in trending_post_counts:

        like_count = like_counts.get(location_id, 0)

        comment_count = comment_counts.get(location_id, 0)

        score = (
            post_count
            + (like_count * 2)
            + (comment_count * 3)
        )

        trending_scores.append(
            (location_id, score)
        )

    trending_scores.sort(
        key=lambda item: item[1],
        reverse=True
    )

    top_location_ids = [
        location_id
        for location_id, score in trending_scores[:10]
    ]

    trending_locations = Location.query.filter(
        Location.id.in_(top_location_ids)
    ).all()

    location_lookup = {
        location.id: location
        for location in trending_locations
    }

    trending_locations = [
        location_lookup[location_id]
        for location_id in top_location_ids
    ]


    if current_user.is_authenticated:

        followed_locations = LocationFollow.query.filter_by(
            user_id=current_user.id
        ).all()

        followed_location_ids = []

        for follow in followed_locations:
            followed_location_ids.append(
                follow.location_id
            )

        if followed_location_ids:
            posts = (
                Post.query
                .filter(
                    Post.location_id.in_(followed_location_ids)
                )
                .order_by(
                    Post.created_at.desc()
                )
                .all()
            )

        else:

            posts = Post.query.order_by(
                Post.created_at.desc()
            ).all()

    else:

        posts = Post.query.order_by(
            Post.created_at.desc()
        ).all()

    return render_template(
        "locations/home.html",
        countries=countries,
        locations=locations,
        posts=posts,
        recently_active_locations=recently_active_locations,
        trending_locations=trending_locations
    )


@locations.route("/location/<int:location_id>")
def location_page(location_id):

    location = Location.query.get(location_id)

    if location is None:
        abort(404)

    is_following = False

    if current_user.is_authenticated:

        existing_follow = LocationFollow.query.filter_by(
            user_id=current_user.id,
            location_id=location.id
        ).first()

        if existing_follow:
            is_following = True

    posts = Post.query.filter_by(
        location_id=location.id
    ).order_by(
        Post.created_at.desc()
    ).all()

    contributor_ids = set()

    for post in posts:
        contributor_ids.add(post.user_id)

    contributor_count = len(contributor_ids)

    return render_template(
        "locations/location.html",
        location=location,
        posts=posts,
        contributor_count=contributor_count,
        is_following=is_following
    )


@locations.route("/locations/search")
def search_locations():

    query = request.args.get("q", "").strip()

    if not query:
        return render_template(
            "search_locations.html",
            locations=[],
            api_locations=[],
            query=""
        )

    locations = Location.query.filter(
        Location.name.ilike(f"%{query}%")
    ).all()

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
        "locations/search_locations.html",
        locations=locations,
        api_locations=api_locations,
        query=query
    )


@locations.route("/locations/create", methods=["POST"])
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

    location = Location.query.filter_by(
        provider=provider,
        provider_id=provider_id
    ).first()

    if location:
        return redirect(
            url_for(
                "locations.location_page",
                location_id=location.id
            )
        )

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
        url_for(
            "locations.location_page",
            location_id=location.id
        )
    )

@locations.route(
    "/location/<int:location_id>/follow",
    methods=["POST"]
)
@login_required
def follow_location(location_id):

    location = Location.query.get(location_id)

    if location is None:
        abort(404)

    existing_follow = LocationFollow.query.filter_by(
        user_id=current_user.id,
        location_id=location.id
    ).first()

    if existing_follow:

        db.session.delete(existing_follow)
        db.session.commit()

        flash(f"You unfollowed {location.name}.")

    else:

        location_follow = LocationFollow(
            user_id=current_user.id,
            location_id=location.id
        )

        db.session.add(location_follow)
        db.session.commit()

        flash(f"You are now following {location.name}.")

    return redirect(
        url_for(
            "locations.location_page",
            location_id=location.id
        )
    )

