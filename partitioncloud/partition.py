#!/usr/bin/python3
"""
Partition module
"""
import os
from flask import Blueprint, abort, send_file, render_template

from .db import get_db
from .auth import login_required, admin_required
from .utils import get_all_partitions


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


@bp.route("/search/<uuid>")
@login_required
def partition_search(uuid):
    db = get_db()
    partition = db.execute(
        """
        SELECT * FROM search_results
        WHERE uuid = ?
        """,
        (uuid,)
    ).fetchone()

    if partition is None:
        abort(404)
    return send_file(os.path.join("search-partitions", f"{uuid}.pdf"))


@bp.route("/")
@admin_required
def index():
    partitions = get_all_partitions().fetchall()
    return render_template("partitions/view-all.html", partitions=partitions)