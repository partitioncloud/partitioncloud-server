#!/usr/bin/python3
"""
Admin Panel
"""
from flask import Blueprint, render_template, session

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
    current_user.get_albums() # We need to do that before we close the db
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
