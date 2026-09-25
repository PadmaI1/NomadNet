from flask import Flask, render_template
from models import db, User, Notification
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from dotenv import load_dotenv

from routes.auth import auth
from routes.locations import locations
from routes.posts import posts
from routes.profiles import profiles
from routes.api import api
from routes.notifications import notifications
import os
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)


load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

database_url = os.getenv("DATABASE_URL", "sqlite:///nomadnet.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.root_path,
    "static",
    "uploads",
    "posts"
)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

csrf = CSRFProtect(app)

db.init_app(app)

migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


login_manager.login_view = "auth.login"


app.register_blueprint(auth)
app.register_blueprint(locations)
app.register_blueprint(posts)
app.register_blueprint(profiles)
app.register_blueprint(api)
app.register_blueprint(notifications)

@app.context_processor
def inject_unread_notification_count():

    unread_count = 0

    if current_user.is_authenticated:
        unread_count = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).count()

    return {
        "unread_count": unread_count
    }

@app.errorhandler(404)
def pagenotfound(error):

    return render_template("404.html"), 404


if __name__ == "__main__":

    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug_mode)