from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    posts = db.relationship("Post", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)
    likes = db.relationship("Like",backref="user",lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.id"),
        nullable=True
    )

    comments = db.relationship("Comment", backref="post", lazy=True)
    likes = db.relationship("Like",backref="post",lazy=True)
    location = db.relationship("Location",backref="posts",lazy=True)
    media = db.relationship(
    "PostMedia",
    backref="post",
    lazy=True,
    cascade="all, delete-orphan",
    order_by="PostMedia.display_order"
)

class PostMedia(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id"),
        nullable=False
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    media_type = db.Column(
        db.String(20),
        nullable=False
    )

    display_order = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False)


class Location(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    type = db.Column(
        db.String(50),
        nullable=False
    )

    country = db.Column(
        db.String(100),
        nullable=False
    )

    city = db.Column(
        db.String(100),
        nullable=True
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    provider = db.Column(db.String(50), nullable=True)
    provider_id = db.Column(db.String(100), nullable=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    content = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id"),
        nullable=False
    )

class Like(db.Model):

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "post_id",
            name="unique_user_post_like"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

class Follow(db.Model):
    __table_args__ = (
        db.UniqueConstraint(
            "follower_id",
            "followed_id",
            name="unique_follower_followed"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    follower_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    followed_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    follower = db.relationship(
        "User",
        foreign_keys=[follower_id],
        backref="following"
    )

    followed = db.relationship(
        "User",
        foreign_keys=[followed_id],
        backref="followers"
    )

class LocationFollow(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "location_id",
            name="unique_user_location_follow"
        ),
    )

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    recipient_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False
    )

    post_id = db.Column(
        db.Integer,
        db.ForeignKey("post.id"),
        nullable=True
    )

    comment_id = db.Column(
        db.Integer,
        db.ForeignKey("comment.id"),
        nullable=True
    )

    location_id = db.Column(
        db.Integer,
        db.ForeignKey("location.id"),
        nullable=True
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    recipient = db.relationship(
        "User",
        foreign_keys=[recipient_id],
        backref="notifications_received"
    )

    actor = db.relationship(
        "User",
        foreign_keys=[actor_id]
    )
