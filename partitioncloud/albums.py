#!/usr/bin/python3
"""
Albums module
"""
import os
from uuid import uuid4

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_file, session)

from .auth import login_required
from .db import get_db

bp = Blueprint("albums", __name__, url_prefix="/albums")


@bp.route("/")
@login_required
def index():
    db = get_db()
    albums = db.execute(
        """
        SELECT album.id, name, uuid FROM album
        JOIN contient_user ON album_id = album.id
        JOIN user ON user_id = user.id
        WHERE user.id = ?
        """,
        (session.get("user_id"),),
    ).fetchall()

    return render_template("albums/index.html", albums=albums)


@bp.route("/<uuid>")
def album(uuid):
    """
    Album page
    """
    db = get_db()
    album = db.execute(
        """
        SELECT id, name, uuid FROM album
        WHERE uuid = ?
        """,
        (uuid,),
    ).fetchone()

    if album is None:
        return abort(404)

    partitions = db.execute(
        """
        SELECT partition.uuid, partition.name, partition.author FROM partition
        JOIN contient_partition ON partition_uuid = partition.uuid
        JOIN album ON album.id = album_id
        WHERE album.uuid = ?
        """,
        (uuid,),
    ).fetchall()

    return render_template("albums/album.html", album=album, partitions=partitions)


@bp.route("/<album_uuid>/<partition_uuid>")
def partition(album_uuid, partition_uuid):
    """
    Returns a partition in a given album
    """
    db = get_db()
    partition = db.execute(
        """
        SELECT * FROM partition
        JOIN contient_partition ON partition_uuid = partition.uuid
        JOIN album ON album.id = album_id
        WHERE album.uuid = ?
        AND partition.uuid = ?
        """,
        (album_uuid, partition_uuid),
    ).fetchone()

    if partition is None:
        return abort(404)

    return send_file(os.path.join("partitions", f"{partition_uuid}.pdf"))


@bp.route("/create-album", methods=["GET", "POST"])
@login_required
def create_album():
    if request.method == "POST":
        name = request.form["name"]
        db = get_db()
        error = None

        if not name:
            error = "Un nom est requis."

        if error is None:
            while True:
                try:
                    uuid = str(uuid4())

                    db.execute(
                        """
                        INSERT INTO album (uuid, name)
                        VALUES (?, ?)
                        """,
                        (uuid, name),
                    )
                    db.commit()

                    album_id = db.execute(
                        """
                        SELECT id FROM album
                        WHERE uuid = ?
                        """,
                        (uuid,),
                    ).fetchone()["id"]

                    db.execute(
                        """
                        INSERT INTO contient_user (user_id, album_id)
                        VALUES (?, ?)
                        """,
                        (session.get("user_id"), album_id),
                    )
                    db.commit()

                    break
                except db.IntegrityError:
                    pass

            return redirect(f"/albums/{uuid}")

        flash(error)
        return render_template("albums/create-album.html")

    return render_template("albums/create-album.html")
