from flask import Flask, render_template
from models import db, User
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from routes.auth import auth
from routes.locations import locations
from routes.posts import posts
from routes.profiles import profiles
from routes.api import api

import os


app = Flask(__name__)

load_dotenv()

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nomadnet.db"


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


@app.errorhandler(404)
def pagenotfound(error):

    return render_template("404.html"), 404


if __name__ == "__main__":

    app.run(debug=True)