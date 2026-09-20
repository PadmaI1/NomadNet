from flask import Blueprint, render_template, abort, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from requests import post

from models import PostMedia, db, Post, Comment, Like, Location, Notification
import os
import uuid

posts = Blueprint("posts", __name__)

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

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}


@posts.route("/posts/create", methods=["POST"])
@login_required
def create_post():
    content = request.form.get("content")
    location_id = request.form.get("location_id")
    media_files = request.files.getlist("media")

    if not location_id:
        flash("Please select a location.")
        return redirect(url_for("locations.home"))

    if not content.strip():
        flash("Post cannot be empty.")
        return redirect(url_for("locations.home"))

    location = Location.query.get(location_id)

    if not location:
        flash("Invalid location.")
        return redirect(url_for("locations.home"))

    media_type = None
    extension = None

    validated_media = []

    for media_file in media_files:

        if not media_file.filename:
            continue

        extension = media_file.filename.rsplit(".", 1)[1].lower()

        if extension in ALLOWED_IMAGE_EXTENSIONS:
            media_type = "image"

        elif extension in ALLOWED_VIDEO_EXTENSIONS:
            media_type = "video"

        else:
            flash("Invalid image or video format.")
            return redirect(url_for("locations.home"))

        validated_media.append(
            (media_file, extension, media_type)
        )

    post = Post(
        content=content.strip(),
        user_id=current_user.id,
        location_id=location.id
    )

    db.session.add(post)
    db.session.flush()

    for index, (media_file, extension, media_type) in enumerate(validated_media):

        filename = f"{uuid.uuid4().hex}.{extension}"

        filepath = os.path.join(
            current_app.config["UPLOAD_FOLDER"],
            filename
        )

        media_file.save(filepath)

        media = PostMedia(
            post_id=post.id,
            filename=filename,
            media_type=media_type,
            display_order=index
        )

        db.session.add(media)

    db.session.commit()

    flash("Post created successfully!")
    return redirect(url_for("locations.home"))


@posts.route("/posts/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    if post.user_id != current_user.id:
        abort(403)

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
    db.session.commit()

    flash("Post deleted successfully.")

    return redirect(url_for("locations.home"))

@posts.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
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

        delete_media_ids = request.form.getlist("delete_media")

        if not content.strip():
            flash("Post cannot be empty.")
            return redirect(
                url_for("posts.edit_post", post_id=post.id)
            )

        location = Location.query.get(location_id)

        if location is None:
            flash("Invalid location selected.")
            return redirect(
                url_for("posts.edit_post", post_id=post.id)
            )

        post.content = content.strip()
        post.location_id = location.id

        for media_id in delete_media_ids:

            media = PostMedia.query.filter_by(
                id=media_id,
                post_id=post.id
            ).first()

            if media is None:
                continue

            filepath = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                media.filename
            )

            if os.path.exists(filepath):
                os.remove(filepath)

            db.session.delete(media)

        db.session.commit()

        flash("Post updated successfully.")

        return redirect(url_for("locations.home"))

    return render_template(
        "posts/edit_post.html",
        post=post,
        locations=Location.query.all()
    )


@posts.route("/posts/<int:post_id>")
def post_detail(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    is_liked = False

    if current_user.is_authenticated:

        existing_like = Like.query.filter_by(
            user_id=current_user.id,
            post_id=post.id
        ).first()

        if existing_like:
            is_liked = True

    return render_template(
        "posts/post_details.html",
        post=post,
        is_liked=is_liked
    )


@posts.route("/posts/<int:post_id>/comments/create", methods=["POST"])
@login_required
def create_comment(post_id):

    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    content = request.form["content"]

    if not content.strip():
        flash("Comment cannot be empty.")
        return redirect(
            url_for("posts.post_detail", post_id=post.id)
        )

    comment = Comment(
        content=content.strip(),
        user_id=current_user.id,
        post_id=post.id
    )

    db.session.add(comment)
    db.session.flush()

    if post.user_id != current_user.id:
        notification = Notification(
            recipient_id=post.user_id,
            actor_id=current_user.id,
            notification_type="comment",
            post_id=post.id,
            comment_id=comment.id
        )

        db.session.add(notification)

    db.session.commit()

    flash("Comment added successfully.")

    return redirect(
        url_for("posts.post_detail", post_id=post.id)
    )


@posts.route("/comments/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):

    comment = Comment.query.get(comment_id)

    if comment is None:
        abort(404)

    if comment.user_id != current_user.id:
        abort(403)

    post_id = comment.post_id

    Notification.query.filter_by(
        comment_id=comment.id
    ).delete()

    db.session.delete(comment)
    db.session.commit()

    flash("Comment deleted successfully.")

    return redirect(
        url_for("posts.post_detail", post_id=post_id)
    )


@posts.route("/posts/<int:post_id>/like", methods=["POST"])
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
        liked = False

    else:

        like = Like(
            user_id=current_user.id,
            post_id=post.id
        )

        db.session.add(like)
        liked = True

        if post.user_id != current_user.id:
            notification = Notification(
                recipient_id=post.user_id,
                actor_id=current_user.id,
                notification_type="like",
                post_id=post.id
            )

            db.session.add(notification)

    db.session.commit()

    like_count = Like.query.filter_by(
        post_id=post.id
    ).count()

    return jsonify({
        "liked": liked,
        "like_count": like_count
    })