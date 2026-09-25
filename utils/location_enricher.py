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


LOCATION_TYPE_FALLBACK_IMAGES = {
    "city": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1200&q=80",
    "mountain": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1200&q=80",
    "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80",
    "coast": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80",
    "island": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=1200&q=80",
    "forest": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&q=80",
    "nature": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&q=80",
    "park": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1200&q=80",
    "desert": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1200&q=80",
    "lake": "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1200&q=80",
    "village": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1200&q=80",
    "temple": "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&q=80",
    "museum": "https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=1200&q=80",
    "restaurant": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1200&q=80",
    "cafe": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=1200&q=80",
}

LOCATION_TYPE_FALLBACK_DEFAULT = "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?w=1200&q=80"


def get_fallback_image(location_type: str) -> str:
    """A representative photo for a location type, used when a place has
    no hero image or user-submitted photos yet (e.g. it isn't on
    NomadNet). Mirrors the same Unsplash-sourced convention already used
    for seeded locations' hero_image_url."""
    if not location_type:
        return LOCATION_TYPE_FALLBACK_DEFAULT

    return LOCATION_TYPE_FALLBACK_IMAGES.get(
        location_type.lower(),
        LOCATION_TYPE_FALLBACK_DEFAULT
    )


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
        "hero_image": get_hero_image(location) or get_fallback_image(location.type),
        "description": generate_location_description(location),
    }


def enrich_locations(locations, days=30) -> list:
    """Enrich multiple locations with computed fields.

    Runs a handful of batched, grouped-by-location queries instead of
    calling enrich_location() in a loop, which would run several queries
    PER location (an N+1 query pattern that gets slow fast as the number
    of locations and network latency grow)."""
    if not locations:
        return []

    location_ids = [location.id for location in locations]
    cutoff = datetime.utcnow() - timedelta(days=days)

    total_post_counts = dict(
        db.session.query(Post.location_id, db.func.count(Post.id))
        .filter(Post.location_id.in_(location_ids))
        .group_by(Post.location_id)
        .all()
    )

    recent_post_counts = dict(
        db.session.query(Post.location_id, db.func.count(Post.id))
        .filter(Post.location_id.in_(location_ids), Post.created_at >= cutoff)
        .group_by(Post.location_id)
        .all()
    )

    recent_like_counts = dict(
        db.session.query(Post.location_id, db.func.count(Like.id))
        .join(Like, Like.post_id == Post.id)
        .filter(Post.location_id.in_(location_ids), Post.created_at >= cutoff)
        .group_by(Post.location_id)
        .all()
    )

    recent_comment_counts = dict(
        db.session.query(Post.location_id, db.func.count(Comment.id))
        .join(Comment, Comment.post_id == Post.id)
        .filter(Post.location_id.in_(location_ids), Post.created_at >= cutoff)
        .group_by(Post.location_id)
        .all()
    )

    active_nomad_counts = dict(
        db.session.query(Post.location_id, db.func.count(db.distinct(Post.user_id)))
        .filter(Post.location_id.in_(location_ids), Post.created_at >= cutoff)
        .group_by(Post.location_id)
        .all()
    )

    enriched = []

    for location in locations:
        recent_posts = recent_post_counts.get(location.id, 0)

        if recent_posts:
            likes = recent_like_counts.get(location.id, 0)
            comments = recent_comment_counts.get(location.id, 0)
            engagement_score = (likes + comments * 2) / recent_posts
            rating = round(min(engagement_score / 2, 5.0), 2)
        else:
            rating = 0.0

        enriched.append({
            "location": location,
            "emoji": get_location_emoji(location.type),
            "rating": rating,
            "active_nomads": active_nomad_counts.get(location.id, 0),
            "post_count": total_post_counts.get(location.id, 0),
            "hero_image": get_hero_image(location) or get_fallback_image(location.type),
            "description": generate_location_description(location),
        })

    return enriched
