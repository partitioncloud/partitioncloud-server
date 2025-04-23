#!/usr/bin/python3
"""
Main file
"""
import os
import sys
import datetime
import subprocess
import importlib.util

from flask import Flask, g, redirect, render_template, request, send_file, flash, session, abort, url_for
from werkzeug.security import generate_password_hash
from flask_babel import Babel, _

from .modules.utils import User, Album, get_all_albums, user_count, partition_count
from .modules import albums, auth, partition, admin, groupe, thumbnails, logging, settings
from .modules.auth import admin_required, login_required
from .modules.classes import permissions
from .modules.db import get_db

app = Flask(__name__)

def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

babel = Babel(app, locale_selector=get_locale)



def load_config():
    app.config.from_object('default_config')
    app.instance_path = os.path.abspath(app.config["INSTANCE_PATH"])

    if not os.path.exists(app.instance_path):
        print("[ERROR] Instance path does not exist. Make sure to use an existing directory.")
        sys.exit(1)

    if os.path.exists(f"{app.instance_path}/config.py"):
        # Load module from instance_path/config.py in user_config object
        spec = importlib.util.spec_from_file_location(
            ".",
            os.path.join(app.instance_path, "config.py")
        )

        if spec is None:
            print("[ERROR] Failed to load $INSTANCE_PATH/config.py")
            sys.exit(1)

        user_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_config)

        app.config.from_object(user_config)

        if os.path.abspath(app.config["INSTANCE_PATH"]) != app.instance_path:
            print(("[ERROR] Using two different instance path.\n"
                    "Please modify INSTANCE_PATH only in default_config.py ",
                    "and remove it from $INSTANCE_PATH/config.py"))
            sys.exit(1)
    else:
        print("[WARNING] Using default config")

    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, f"{__name__}.sqlite"),
    )


def setup_logging():
    logging.log_file = os.path.join(app.instance_path, "logs.txt")
    enabled = []
    for event in app.config["ENABLED_LOGS"]:
        try:
            enabled.append(logging.LogEntry.from_string(event))
        except KeyError:
            print(f"[ERROR] There is an error in your config: Unknown event {event}")

    logging.enabled = enabled


def get_version():
    try:
        result = subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE, check=True)
        return result.stdout.decode('utf8')
    except (FileNotFoundError, subprocess.CalledProcessError):
        # In case git not found or any platform specific weird error
        return "unknown"


load_config()
setup_logging()

app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(groupe.bp)
app.register_blueprint(albums.bp)
app.register_blueprint(settings.bp)
app.register_blueprint(partition.bp)
app.register_blueprint(thumbnails.bp)

__version__ = get_version()

logging.log([], logging.LogEntry.SERVER_RESTART)


@app.route("/")
def home():
    """Show launch page if enabled"""
    if g.user is None:
        if app.config["LAUNCH_PAGE"]:
            return redirect(url_for("launch_page"))
        return redirect(url_for("auth.login"))
    return redirect(url_for("albums.index"))


@app.route("/launch")
def launch_page():
    """Show launch page if enabled"""
    if not app.config["LAUNCH_PAGE"]:
        return home()
    return render_template("launch.html", user_count=user_count(), partition_count=partition_count())


@app.route("/add-user", methods=["GET", "POST"])
@admin_required
def add_user():
    """
    Ajouter un utilisateur en tant qu'administrateur
    """
    current_user = User(user_id=session.get("user_id"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        album_uuid = request.form["album_uuid"]

        error = auth.create_user(username, password)

        if error is None:
            # Success, go to the login page.
            user = User(name=username)

            logging.log(
                [user.username, user.id, True, current_user.username],
                logging.LogEntry.NEW_USER
            )

            try:
                if album_uuid != "":
                    user.join_album(album_uuid)
                flash(_("Created user %(username)s", username=username))
                return redirect(url_for("albums.index"))
            except LookupError:
                flash(_("This album does not exists, but user %(username)s has been created", username=username))
                return redirect(url_for("albums.index"))

        flash(error)
    return render_template("auth/register.html", albums=get_all_albums(), user=current_user)


@app.before_request
def before_request():
    """Set cookie max age to 31 days"""
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=int(app.config["MAX_AGE"]))
    
    if g.user is not None:
        g.user = User(user_id=g.user["id"])

@app.context_processor
def inject_default_variables():
    """Inject variables in the template"""
    variables = {
        "lang": get_locale(),
        "version": __version__,
        "permissions": permissions
    }
    if __version__ == "unknown":
        variables["version"] = ""

    return variables


@app.after_request
def after_request(response):
    """Automatically close db after each request"""
    if ('db' in g) and (g.db is not None):
        g.db.close()
    return response


@app.errorhandler(LookupError)
def page_not_found(e):
    abort(404)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
