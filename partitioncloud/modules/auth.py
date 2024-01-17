#!/usr/bin/python3
"""
Authentification module
"""
import functools
from typing import Optional

from flask import (Blueprint, flash, g, redirect, render_template,
                request, session, url_for, current_app)

from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .utils import User
from . import logging

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Vous devez être connecté pour accéder à cette page.")
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


def anon_required(view):
    """View decorator that redirects authenticated users to the index."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is not None:
            return redirect(url_for("albums.index"))

        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Vous devez être connecté pour accéder à cette page.")
            return redirect(url_for("auth.login"))

        user = User(user_id=session.get("user_id"))
        if user.access_level != 1:
            flash("Droits insuffisants.")
            return redirect("/albums")

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
    else:
        g.user = (
            get_db().execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        )


def create_user(username: str, password: str) -> Optional[str]:
    """Adds a new user to the database"""
    error = None
    if not username:
        error = "Un nom d'utilisateur est requis."
    elif not password:
        error = "Un mot de passe est requis."

    try:
        db = get_db()

        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
    except db.IntegrityError:
        # The username was already taken, which caused the
        # commit to fail. Show a validation error.
        error = f"Le nom d'utilisateur {username} est déjà pris."

    return error # may be None


@bp.route("/register", methods=("GET", "POST"))
@anon_required
def register():
    """Register a new user.
    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if current_app.config["DISABLE_REGISTER"]:
        flash("L'enregistrement de nouveaux utilisateurs a été désactivé par l'administrateur.")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        error = create_user(username, password)

        if error is not None:
            flash(error)
        else:
            user = User(name=username)

            flash("Utilisateur créé avec succès. Vous pouvez vous connecter.")

            logging.log(
                [user.username, user.id, False],
                logging.LogEntry.NEW_USER
            )

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
@anon_required
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if (user is None) or not check_password_hash(user["password"], password):
            logging.log([username], logging.LogEntry.FAILED_LOGIN)
            error = "Nom d'utilisateur ou mot de passe incorrect."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user["id"]

            logging.log([username], logging.LogEntry.LOGIN)

            return redirect(url_for("albums.index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("auth.login"))
