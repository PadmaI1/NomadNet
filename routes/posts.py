from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user

from models import db, Post, Comment, Like, Location


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

@posts.route("/posts/create", methods=["POST"])
@login_required
def create_post():

    content = request.form["content"]
    location_id = request.form.get("location_id")

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

    post = Post(
        content=content,
        user_id=current_user.id,
        location_id=location.id
    )

    db.session.add(post)
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

    return render_template(
        "posts/post_details.html",
        post=post
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
        url_for("posts.post_detail", post_id=post.id)
    )