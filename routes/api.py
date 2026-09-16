from flask import Blueprint, request, jsonify
from flask_login import login_required
import requests
from math import radians, sin, cos, sqrt, atan2

from models import db, Location


api = Blueprint("api", __name__)


@api.route("/api/locations/search")
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
            "existing_id": (
                existing_location.id
                if existing_location
                else None
            )
        })

    return jsonify({
        "locations": local_locations,
        "api_locations": api_locations
    })


@api.route("/api/locations/create", methods=["POST"])
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

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    distance = earth_radius * c

    return distance


@api.route("/api/locations/nearby")
@login_required
def nearby_locations():

    latitude = request.args.get(
        "latitude",
        type=float
    )

    longitude = request.args.get(
        "longitude",
        type=float
    )

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

    nearby.sort(
        key=lambda location: location["distance"]
    )

    return jsonify({
        "locations": nearby
    })