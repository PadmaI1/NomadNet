from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user
import requests

from models import db, Country, Follow, Post, Location


locations = Blueprint("locations", __name__)


@locations.route("/")
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
        "locations/home.html",
        countries=countries,
        locations=locations,
        posts=posts
    )


@locations.route("/location/<int:location_id>")
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
        "locations/location.html",
        location=location,
        posts=posts
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