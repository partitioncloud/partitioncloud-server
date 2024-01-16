#!/usr/bin/python3
"""
Main file
"""
import os
import sys
import datetime
import subprocess
import importlib.util

from flask import Flask, g, redirect, render_template, request, send_file, flash, session, abort
from werkzeug.security import generate_password_hash

from .modules.utils import User, Album, get_all_albums
from .modules import albums, auth, partition, admin, groupe, thumbnails
from .modules.auth import admin_required, login_required
from .modules.db import get_db

app = Flask(__name__)


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
        user_config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_config)

        app.config.from_object(user_config)

        if os.path.abspath(app.config["INSTANCE_PATH"]) != app.instance_path:
            print("[ERROR] Using two different instance path. \
            \nPlease modify INSTANCE_PATH only in default_config.py and remove it from $INSTANCE_PATH/config.py")
            sys.exit(1)
    else:
        print("[WARNING] Using default config")

    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, f"{__name__}.sqlite"),
    )


def get_version():
    try:
        result = subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE, check=True)
        return result.stdout.decode('utf8')
    except (FileNotFoundError, subprocess.CalledProcessError):
        # In case git not found or any platform specific weird error
        return "unknown"


load_config()

app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(groupe.bp)
app.register_blueprint(albums.bp)
app.register_blueprint(partition.bp)
app.register_blueprint(thumbnails.bp)

__version__ = get_version()


@app.route("/")
def home():
    """Redirect to home"""
    return redirect("/albums/")


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
            try:
                if album_uuid != "":
                    user.join_album(album_uuid)
                flash(f"Utilisateur {username} créé")
                return redirect("/albums")
            except LookupError:
                flash(f"Cet album n'existe pas. L'utilisateur {username} a été créé")
                return redirect("/albums")

        flash(error)
    return render_template("auth/register.html", albums=get_all_albums(), user=current_user)


@app.before_request
def before_request():
    """Set cookie max age to 31 days"""
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=int(app.config["MAX_AGE"]))

@app.context_processor
def inject_default_variables():
    """Inject the version number in the template variables"""
    if __version__ == "unknown":
        return {"version": ''}
    return {"version": __version__}


@app.after_request
def after_request(response):
    """Automatically close db after each request"""
    if ('db' in g) and (g.db is not None):
        g.db.close()
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0")
