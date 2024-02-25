#!/usr/bin/python3
"""
Admin Panel
"""
import os
from flask import Blueprint, render_template, session, current_app, send_file

from .db import get_db
from .auth import admin_required
from .utils import User


bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@admin_required
def index():
    """
    Admin panel home page
    """
    current_user = User(user_id=session.get("user_id"))
    db = get_db()
    users_id = db.execute(
        """
        SELECT id FROM user
        """
    )
    users = [User(user_id=user["id"]) for user in users_id]
    for user in users:
        user.get_albums()
        user.get_partitions()

    return render_template(
        "admin/index.html",
        users=users,
        user=current_user
    )

@bp.route("/user/<user_id>")
@admin_required
def user_inspect(user_id):
    """
    Inspect user
    """
    current_user = User(user_id=session.get("user_id"))
    db = get_db()
    inspected_user = User(user_id=user_id)

    return render_template(
        "settings/index.html",
        skip_old_password=True,
        inspected_user=inspected_user,
        user=current_user
    )


@bp.route("/logs")
@admin_required
def logs():
    """
    Admin panel logs page
    """
    user = User(user_id=session.get("user_id"))

    return render_template(
        "admin/logs.html",
        user=user
    )


@bp.route("/logs.txt")
@admin_required
def logs_txt():
    """
    Admin panel logs page
    """
    return send_file(
        os.path.join(current_app.instance_path, "logs.txt")
    )
