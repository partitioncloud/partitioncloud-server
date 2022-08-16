#!/usr/bin/python3
"""
Partition module
"""
import os
from flask import Blueprint, abort, send_file

from .db import get_db
from .auth import login_required


bp = Blueprint("partition", __name__, url_prefix="/partition")

@bp.route("/<uuid>")
@login_required
def partition(uuid):
    db = get_db()
    partition = db.execute(
        """
        SELECT * FROM partition
        WHERE uuid = ?
        """,
        (uuid,)
    ).fetchone()

    if partition is None:
        abort(404)
    return send_file(os.path.join("partitions", f"{uuid}.pdf"))