#!/usr/bin/python3
"""
Admin Panel
"""
import os
from flask import Blueprint, render_template, session, current_app, send_file

from . import utils
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
    users = utils.get_all_users()
    for user in users:
        user.get_albums()
        user.get_partitions()

    return render_template(
        "admin/index.html",
        users=users
    )

@bp.route("/user/<user_id>")
@admin_required
def user_inspect(user_id):
    """
    Inspect user
    """
    db = get_db()
    inspected_user = User(user_id=user_id)

    return render_template(
        "settings/index.html",
        skip_old_password=True,
        inspected_user=inspected_user,
        deletion_allowed=True
    )


@bp.route("/logs")
@admin_required
def logs():
    """
    Admin panel logs page
    """
    return render_template(
        "admin/logs.html"
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
