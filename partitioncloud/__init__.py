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

from .modules.utils import User, Album
from .modules import albums, auth, partition, admin, groupe, thumbnails, logging, settings
from .modules.auth import admin_required, login_required
from .modules.googlesearch import get_possible_queries
from .modules.db import get_db
from .modules import permissions
from .modules import utils

app = Flask(__name__)

def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

babel = Babel(app, locale_selector=get_locale)



def load_config(config_file='default_config.py'):
    assert(config_file.endswith(".py"))

    app.config.from_object(config_file[:-3])
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


if "FLASK_CONFIG_PATH" in os.environ:
    load_config(config_file=os.environ["FLASK_CONFIG_PATH"])
else:
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
    return render_template(
        "launch.html",
        user_count=utils.user_count(),
        partition_count=utils.partition_count()
    )


@app.route("/add-user", methods=["GET", "POST"])
@admin_required
def add_user():
    """
    Ajouter un utilisateur en tant qu'administrateur
    """

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        album_uuid = request.form["album_uuid"]

        auth.create_user(username, password)

        # Success, go to the login page.
        new_user = User(name=username)

        logging.log(
            [new_user.username, new_user.id, True, g.user.username],
            logging.LogEntry.NEW_USER
        )

        try:
            if album_uuid != "":
                new_user.join_album(album_uuid=album_uuid)
            flash(_("Created user %(username)s", username=username))
            return redirect(url_for("albums.index"))
        except LookupError:
            flash(_("This album does not exists, but user %(username)s has been created", username=username))
            return redirect(url_for("albums.index"))

    return render_template(
        "auth/register.html",
        albums=utils.get_all_albums(),
    )


@app.before_request
def before_request():
    """Set cookie max age to 31 days"""
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=int(app.config["MAX_AGE"]))


@app.context_processor
def inject_default_variables():
    """Inject variables in the template"""
    variables = {
        "lang": get_locale(),
        "version": __version__,
        "permissions": permissions,
        "max_queries": get_possible_queries(g.user.is_admin) if g.user else 0,
        "FakeObject": utils.FakeObject,
        "g_user": g.user
    }
    if __version__ == "unknown":
        variables["version"] = ""

    return variables


@app.after_request
def after_request(response):
    """Automatically close db after each request"""
    if ('db' in g) and (g.db is not None):
        g.db.close()
    
    #* see @app.errorhandler(utils.InvalidRequest)
    if response.status_code == 200 and "next_status" in session:
        status = session["next_status"]
        del session["next_status"]
        response.status_code = status

    return response


@app.errorhandler(LookupError)
def page_not_found(e):
    abort(404)

@app.errorhandler(utils.InvalidRequest)
def invalid_request(e):
    flash(e.reason)
    # We would want to respond with e.code HTTP status code
    # but we need to let 301 redirect. The workaround is to store the next_status
    # and apply it in after_request the next time
    session["next_status"] = e.code

    if e.redirect is not None:
        return redirect(e.redirect)
    if request.referrer:
        return redirect(request.referrer)
    return redirect("/albums")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
