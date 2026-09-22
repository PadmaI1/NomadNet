"""Helper functions to enrich location data with computed fields for Stitch design."""

from flask import url_for
from models import db, Post, Like, Comment, LocationFollow
from datetime import datetime, timedelta

LOCATION_TYPE_EMOJIS = {
    "island": "🏝️",
    "city": "🏙️",
    "mountain": "⛰️",
    "beach": "🏖️",
    "temple": "🏛️",
    "village": "🏘️",
    "forest": "🌲",
    "desert": "🏜️",
    "lake": "🌊",
    "coast": "🏖️",
    "nature": "🌿",
    "park": "🌳",
    "museum": "🏛️",
    "restaurant": "🍽️",
    "cafe": "☕",
}


def get_location_emoji(location_type: str) -> str:
    """Get emoji for location type."""
    return LOCATION_TYPE_EMOJIS.get(location_type.lower(), "📍")


def calculate_location_rating(location, days=30) -> float:
    """
    Calculate location rating from engagement metrics.
    Formula: (total_likes + total_comments * 2) / post_count
    Returns rating between 0.0 and 5.0
    """
    cutoff = datetime.utcnow() - timedelta(days=days)

    posts = Post.query.filter(
        Post.location_id == location.id,
        Post.created_at >= cutoff
    ).all()

    if not posts:
        return 0.0

    total_likes = Like.query.join(Post).filter(
        Post.location_id == location.id,
        Post.created_at >= cutoff
    ).count()

    total_comments = Comment.query.join(Post).filter(
        Post.location_id == location.id,
        Post.created_at >= cutoff
    ).count()

    post_count = len(posts)

    engagement_score = (total_likes + total_comments * 2) / post_count

    rating = min(engagement_score / 2, 5.0)

    return round(rating, 2)


def get_active_nomads_count(location, days=30) -> int:
    """Get count of distinct users who posted about this location in last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    unique_posters = db.session.query(
        db.func.count(db.distinct(Post.user_id))
    ).filter(
        Post.location_id == location.id,
        Post.created_at >= cutoff
    ).scalar()

    return unique_posters or 0


def _media_url(filename: str) -> str:
    """Resolve a media filename to a usable URL, whether it's an
    externally hosted seed image or a locally uploaded file."""
    if filename.startswith("http://") or filename.startswith("https://"):
        return filename

    return url_for("static", filename="uploads/posts/" + filename)


def get_hero_image(location) -> str:
    """Get the location's hero image: its own hero_image_url if set,
    otherwise the most recent post's first image."""
    if location.hero_image_url:
        return location.hero_image_url

    if not location.posts:
        return None

    for post in sorted(location.posts, key=lambda p: p.created_at, reverse=True):
        for media in post.media:
            if media.media_type == "image":
                return _media_url(media.filename)

    return None


def generate_location_description(location) -> str:
    """Generate a smart description from location name and type."""
    if location.description:
        return location.description

    type_label = location.type.title() if location.type else "Destination"

    if location.city:
        return f"{location.name} - {location.city}, {location.country}"

    return f"{location.name} - {location.country}"


def enrich_location(location) -> dict:
    """
    Enrich a location object with computed fields for template rendering.
    Returns a dict with additional computed fields.
    """
    return {
        "emoji": get_location_emoji(location.type),
        "rating": calculate_location_rating(location),
        "active_nomads": get_active_nomads_count(location),
        "post_count": len(location.posts),
        "hero_image": get_hero_image(location),
        "description": generate_location_description(location),
    }


def enrich_locations(locations) -> list:
    """Enrich multiple locations with computed fields."""
    enriched = []
    for location in locations:
        enriched_data = {
            "location": location,
            **enrich_location(location)
        }
        enriched.append(enriched_data)

    return enriched
