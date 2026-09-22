from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
import requests
from models import db, Country, Follow, Post, Location, LocationFollow, Like, Comment, User
from forms import CreatePostForm
from datetime import datetime, timedelta
from utils.location_enricher import (
    enrich_locations,
    enrich_location,
    get_location_emoji,
    get_fallback_image
)
from routes.api import calculate_distance


locations = Blueprint("locations", __name__)


def _build_discovery_context():
    """Shared trending/recently-active/pinned computation used by both the
    Explore and For You pages."""

    countries = Country.query.all()
    all_locations = Location.query.all()

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

    enriched_trending = enrich_locations(trending_locations)
    enriched_recently_active = enrich_locations(recently_active_locations)

    pinned_locations = []

    if current_user.is_authenticated:

        followed_location_ids = [
            follow.location_id
            for follow in LocationFollow.query.filter_by(
                user_id=current_user.id
            ).limit(3).all()
        ]

        pinned_locations = enrich_locations(
            Location.query.filter(
                Location.id.in_(followed_location_ids)
            ).all()
        )

    return {
        "countries": countries,
        "locations": all_locations,
        "recently_active_locations": enriched_recently_active,
        "trending_locations": enriched_trending,
        "pinned_locations": pinned_locations,
        "now": datetime.utcnow(),
    }


@locations.route("/")
def home():

    posts = Post.query.order_by(
        Post.created_at.desc()
    ).limit(60).all()

    form = CreatePostForm()

    return render_template(
        "locations/home.html",
        posts=posts,
        form=form,
        active_tab="explore",
        is_for_you=False,
        **_build_discovery_context()
    )


@locations.route("/for-you")
@login_required
def for_you():

    followed_location_ids = [
        follow.location_id
        for follow in LocationFollow.query.filter_by(
            user_id=current_user.id
        ).all()
    ]

    followed_user_ids = [
        follow.followed_id
        for follow in Follow.query.filter_by(
            follower_id=current_user.id
        ).all()
    ]

    if followed_location_ids or followed_user_ids:

        posts = (
            Post.query
            .filter(
                db.or_(
                    Post.location_id.in_(followed_location_ids),
                    Post.user_id.in_(followed_user_ids)
                )
            )
            .order_by(Post.created_at.desc())
            .all()
        )

    else:

        posts = []

    form = CreatePostForm()

    return render_template(
        "locations/home.html",
        posts=posts,
        form=form,
        active_tab="foryou",
        is_for_you=True,
        **_build_discovery_context()
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

    media_count = sum(len(post.media) for post in posts)

    follower_count = LocationFollow.query.filter_by(
        location_id=location.id
    ).count()

    recent_contributors = []
    seen_contributor_ids = set()

    for post in posts:
        if post.user_id not in seen_contributor_ids:
            seen_contributor_ids.add(post.user_id)
            recent_contributors.append(post.author)
        if len(recent_contributors) >= 5:
            break

    other_locations = Location.query.filter(
        Location.id != location.id
    ).all()

    nearby_locations = sorted(
        (
            {
                "location": other,
                "distance": calculate_distance(
                    location.latitude,
                    location.longitude,
                    other.latitude,
                    other.longitude
                )
            }
            for other in other_locations
        ),
        key=lambda item: item["distance"]
    )[:4]

    return render_template(
        "locations/location.html",
        location=location,
        posts=posts,
        contributor_count=contributor_count,
        is_following=is_following,
        media_count=media_count,
        follower_count=follower_count,
        recent_contributors=recent_contributors,
        nearby_locations=nearby_locations,
        now=datetime.utcnow(),
        **enrich_location(location)
    )


@locations.route("/locations/search")
def search_locations():

    query = request.args.get("q", "").strip()

    if not query:
        return render_template(
            "locations/search_locations.html",
            locations=[],
            api_locations=[],
            all_matches=[],
            top_location=None,
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

        location_type = result.get("addresstype") or "location"

        location_data = {
            "name": result.get("name"),
            "type": location_type,
            "country": result["address"].get("country"),
            "city": city,
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
            "place_id": result.get("place_id"),
            "provider": "openstreetmap",
            "provider_id": str(result["place_id"]),
            "display_name": result.get("display_name"),
            "emoji": get_location_emoji(location_type)
        }

        api_locations.append(location_data)

    all_matches = [
        {
            "kind": "saved",
            "id": location.id,
            "name": location.name,
            "type": location.type,
            "country": location.country,
            "city": location.city,
            "on_nomadnet": True,
            **enrich_location(location)
        }
        for location in locations
    ] + [
        {
            **item,
            "on_nomadnet": False,
            "rating": None,
            "active_nomads": 0,
            "post_count": 0,
            "hero_image": get_fallback_image(item["type"]),
            "description": (
                item["display_name"]
                if item["display_name"] and item["display_name"] != item["name"]
                else ", ".join(
                    part for part in [item["city"], item["country"]] if part
                )
            )
        }
        for item in api_locations
    ]

    top_location = all_matches[0] if all_matches else None

    return render_template(
        "locations/search_locations.html",
        locations=locations,
        api_locations=api_locations,
        all_matches=all_matches,
        top_location=top_location,
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

