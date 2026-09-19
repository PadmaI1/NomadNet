from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from models import Notification, db


notifications = Blueprint("notifications", __name__)


@notifications.route("/notifications")
@login_required
def notification_list():

    notifications = Notification.query.filter_by(
        recipient_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    unread_notifications = Notification.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).all()

    for notification in unread_notifications:
        notification.is_read = True

    db.session.commit()

    unread_count = 0

    return render_template(
        "notifications.html",
        notifications=notifications,
        unread_count=unread_count
    )