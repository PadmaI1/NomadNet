from flask import Blueprint, render_template, abort, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from requests import post

from sqlalchemy.orm import selectinload, joinedload

from models import PostMedia, db, Post, Comment, Like, Location, LocationFollow, Follow, Notification
from forms import CreatePostForm, EditPostForm, CreateCommentForm
from utils.location_enricher import enrich_location
from datetime import datetime
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
    """
    Create a new post.

    The CreatePostForm validates:
    - content is not empty and is < 5000 chars
    - location_id is provided and is not empty
    - media files (if provided) are valid image/video extensions

    Request flow:
    1. Form validates all inputs
    2. If validation fails, form.validate_on_submit() returns False
    3. If validation passes, we process the form data
    4. Check that location exists in database
    5. Save media files to disk
    6. Create Post and PostMedia database records
    7. Commit and redirect
    """
    form = CreatePostForm()

    if form.validate_on_submit():
        # Form validated. Get the location and verify it exists.
        location = Location.query.get(int(form.location_id.data))

        if not location:
            flash("Invalid location.")
            return redirect(url_for("locations.home"))

        # Create the post with validated data
        post = Post(
            content=form.content.data.strip(),
            user_id=current_user.id,
            location_id=location.id
        )

        db.session.add(post)
        db.session.flush()  # Flush to get post.id before adding media

        # Process media files
        media_files = request.files.getlist("media")

        for index, media_file in enumerate(media_files):

            if not media_file.filename:
                continue

            extension = media_file.filename.rsplit(".", 1)[1].lower()

            # Determine media type based on extension
            if extension in ALLOWED_IMAGE_EXTENSIONS:
                media_type = "image"
            elif extension in ALLOWED_VIDEO_EXTENSIONS:
                media_type = "video"
            else:
                # This should not happen because form validation already checked
                continue

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

    # If GET or form validation failed, redirect home
    # (forms are usually submitted via home page)
    flash("Failed to create post. Please try again.")
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
    """
    Edit an existing post.

    Security checks:
    - @login_required ensures user is logged in
    - Check that post exists (404 if not)
    - Check that current_user owns the post (403 if not)

    Form validation:
    - content must not be empty
    - location_id must be provided and valid
    - media files (if provided) must be valid formats

    Additional logic:
    - Handle deletion of existing media (user checks boxes to delete)
    - Handle addition of new media (user uploads new files)
    """
    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    if post.user_id != current_user.id:
        abort(403)

    form = EditPostForm()

    if form.validate_on_submit():

        location = Location.query.get(int(form.location_id.data))

        if location is None:
            flash("Invalid location selected.")
            return redirect(url_for("posts.edit_post", post_id=post.id))

        # Update post content and location
        post.content = form.content.data.strip()
        post.location_id = location.id

        # Delete media that user checked for deletion
        delete_media_ids = request.form.getlist("delete_media")

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

        # Handle new media uploads
        media_files = request.files.getlist("media")
        existing_media_count = len(post.media)

        for index, media_file in enumerate(media_files):

            if not media_file.filename:
                continue

            extension = media_file.filename.rsplit(".", 1)[1].lower()

            if extension in ALLOWED_IMAGE_EXTENSIONS:
                media_type = "image"
            elif extension in ALLOWED_VIDEO_EXTENSIONS:
                media_type = "video"
            else:
                continue

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
                display_order=existing_media_count + index
            )

            db.session.add(media)

        db.session.commit()

        flash("Post updated successfully.")
        return redirect(url_for("locations.home"))

    # GET request: populate form with current post data
    if request.method == "GET":
        form.content.data = post.content
        form.location_id.data = str(post.location_id)

    return render_template(
        "posts/edit_post.html",
        form=form,
        post=post,
        locations=Location.query.all()
    )


@posts.route("/posts/<int:post_id>")
def post_detail(post_id):
    """
    Display a single post with all comments, plus context about the
    post's location (stats, other contributors, other posts there)
    and the author's follow status.

    This route instantiates CreateCommentForm so the template
    can render the comment form with proper CSRF protection.
    """
    post = Post.query.options(
        selectinload(Post.comments).joinedload(Comment.author)
    ).get(post_id)

    if post is None:
        abort(404)

    is_liked = False
    is_following_author = False

    if current_user.is_authenticated:

        existing_like = Like.query.filter_by(
            user_id=current_user.id,
            post_id=post.id
        ).first()

        if existing_like:
            is_liked = True

        if post.user_id != current_user.id:

            existing_follow = Follow.query.filter_by(
                follower_id=current_user.id,
                followed_id=post.user_id
            ).first()

            if existing_follow:
                is_following_author = True

    location = post.location
    location_context = {}
    recent_contributors = []
    more_posts = []
    is_following_location = False

    if location:

        location_posts = Post.query.filter_by(
            location_id=location.id
        ).order_by(
            Post.created_at.desc()
        ).all()

        contributor_ids = {p.user_id for p in location_posts}

        seen_contributor_ids = set()

        for p in location_posts:

            if p.user_id == post.user_id or p.user_id in seen_contributor_ids:
                continue

            seen_contributor_ids.add(p.user_id)
            recent_contributors.append(p.author)

            if len(recent_contributors) >= 4:
                break

        more_posts = [p for p in location_posts if p.id != post.id][:4]

        if current_user.is_authenticated:

            existing_location_follow = LocationFollow.query.filter_by(
                user_id=current_user.id,
                location_id=location.id
            ).first()

            if existing_location_follow:
                is_following_location = True

        location_context = {
            "contributor_count": len(contributor_ids),
            "location_follower_count": LocationFollow.query.filter_by(
                location_id=location.id
            ).count(),
            **enrich_location(location)
        }

    form = CreateCommentForm()

    return render_template(
        "posts/post_details.html",
        post=post,
        is_liked=is_liked,
        is_following_author=is_following_author,
        is_following_location=is_following_location,
        recent_contributors=recent_contributors,
        more_posts=more_posts,
        now=datetime.utcnow(),
        form=form,
        **location_context
    )


@posts.route("/posts/<int:post_id>/comments/create", methods=["POST"])
@login_required
def create_comment(post_id):
    """
    Create a comment on a post.

    Form validation:
    - content must not be empty and must be < 1000 chars

    Database logic:
    - Create Comment record
    - Create Notification if the post owner is not the commenter
    """
    post = Post.query.get(post_id)

    if post is None:
        abort(404)

    form = CreateCommentForm()

    if form.validate_on_submit():

        comment = Comment(
            content=form.content.data.strip(),
            user_id=current_user.id,
            post_id=post.id
        )

        db.session.add(comment)
        db.session.flush()

        # Notify the post owner (unless they're commenting on their own post)
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

    else:
        if form.errors:
            flash(form.errors['content'][0])

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