from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from flask_login import login_required, current_user

from models import db, User, Post, Follow


profiles = Blueprint("profiles", __name__)


@profiles.route("/user/<username>")
def profile(username):

    user = User.query.filter_by(
        username=username
    ).first()

    if user is None:
        abort(404)

    posts = Post.query.filter_by(
        user_id=user.id
    ).order_by(
        Post.created_at.desc()
    ).all()

    is_following = False

    if current_user.is_authenticated:

        existing_follow = Follow.query.filter_by(
            follower_id=current_user.id,
            followed_id=user.id
        ).first()

        if existing_follow:
            is_following = True

    return render_template(
        "profile.html",
        user=user,
        posts=posts,
        is_following=is_following
    )


@profiles.route("/user/<username>/follow", methods=["POST"])
@login_required
def follow_user(username):

    user = User.query.filter_by(
        username=username
    ).first()

    if user is None:
        abort(404)

    if user.id == current_user.id:
        flash("You cannot follow yourself.")
        return redirect(
            url_for(
                "profiles.profile",
                username=user.username
            )
        )

    existing_follow = Follow.query.filter_by(
        follower_id=current_user.id,
        followed_id=user.id
    ).first()

    if existing_follow:

        db.session.delete(existing_follow)
        db.session.commit()

        flash(f"You unfollowed {user.username}.")

    else:

        follow = Follow(
            follower_id=current_user.id,
            followed_id=user.id
        )

        db.session.add(follow)
        db.session.commit()

        flash(f"You are now following {user.username}.")

    return redirect(
        url_for(
            "profiles.profile",
            username=user.username
        )
    )