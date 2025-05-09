#!/usr/bin/python3
"""
Authentification module
"""
import functools
from typing import Optional

from flask import (Blueprint, flash, g, redirect, render_template,
                request, session, url_for, current_app)
from flask_babel import _

from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .permissions import PermError
from .utils import User
from . import logging
from . import utils

bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            raise PermError(
                _("You need to login to access this resource."),
                redirect=url_for("auth.login")
            )

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
            raise PermError(
                _("You need to login to access this resource."),
                redirect=url_for("auth.login")
            )

        if not g.user.is_admin:
            raise PermError(
                _("You need to login to access this resource."),
                redirect="/albums"
            )

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")

    g.user = None
    if user_id is not None:
        g.user = User(user_id=user_id)


def create_user(username: str, password: str) -> Optional[str]:
    """Adds a new user to the database"""

    if not username:
        raise utils.InvalidRequest(_("Missing username."))
    elif not password:
        raise utils.InvalidRequest(_("Missing password."))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO user (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        db.commit()
    except db.IntegrityError:
        # The username was already taken, which caused the
        # commit to fail. Show a validation error.
        raise utils.InvalidRequest(_("Username %(username)s is not available.", username=username))


@bp.route("/register", methods=("GET", "POST"))
@anon_required
def register():
    """Register a new user.
    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if current_app.config["DISABLE_REGISTER"]:
        raise utils.InvalidRequest(
            _("New users registration is disabled by owner."),
            redirect=url_for("auth.login")
        )

    if request.method == "GET":
        return render_template("auth/register.html")

    new_username = request.form["username"]
    password = request.form["password"]

    create_user(new_username, password)

    new_user = User(name=new_username)
    flash(_("Successfully created new user. You can log in."))

    logging.log(
        [new_user.username, new_user.id, False],
        logging.LogEntry.NEW_USER
    )
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=("GET", "POST"))
@anon_required
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form["username"]
    password = request.form["password"]

    db = get_db()
    user = db.execute(# TODO can't that be a function of `class User` ?
        "SELECT * FROM user WHERE username = ?", (username,)
    ).fetchone()

    if (user is None) or not check_password_hash(user["password"], password):
        logging.log([username], logging.LogEntry.FAILED_LOGIN)
        raise utils.InvalidRequest(_("Incorrect username or password"))

    # store the user id in a new session and return to the index
    session.clear()
    session["user_id"] = user["id"]

    logging.log([username], logging.LogEntry.LOGIN)

    return redirect(url_for("albums.index"))



@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect("/")
