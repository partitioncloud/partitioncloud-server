#!/usr/bin/python3
"""
Admin Panel
"""
import os
from flask import Blueprint, abort, send_file, render_template

from .db import get_db
from .auth import admin_required
from .utils import User


bp = Blueprint("admin", __name__, url_prefix="/admin")

@bp.route("/")
@admin_required
def index():
    current_user = User(user_id=session.get("user_id"))
    db = get_db()
    users_id = db.execute(
        """
        SELECT id FROM user
        """
    )
    users = [User(user_id=u["id"]) for u in users_id]
    for u in users:
        u.albums = u.get_albums()
        u.partitions = u.get_partitions()
    db.close()

    return render_template(
        "admin/index.html",
        users=users,
        user=current_user
    )