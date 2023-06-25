#!/usr/bin/python3
"""
Main file
"""
import os

from flask import Flask, g, redirect, render_template, request, send_file, flash, session
from werkzeug.security import generate_password_hash

from .modules.utils import User, Album, get_all_albums
from .modules import albums, auth, partition, admin
from .modules.auth import admin_required
from .modules.db import get_db

app = Flask(__name__)

app.config.from_mapping(
    DATABASE=os.path.join(app.instance_path, f"{__name__}.sqlite"),
)
app.config.from_object('default_config')
if os.path.exists("instance/config.py"):
    app.config.from_object('instance.config')
else:
    print("[WARNING] Using default config")

app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(albums.bp)
app.register_blueprint(partition.bp)


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
        db = get_db()
        error = None

        if not username:
            error = "Un nom d'utilisateur est requis."
        elif not password:
            error = "Un mot de passe est requis."

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                error = f"Le nom d'utilisateur {username} est déjà pris."
            else:
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


@app.after_request
def after_request(response):
    """Automatically close db after each request"""
    if ('db' in g) and (g.db is not None):
        g.db.close()
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0")
