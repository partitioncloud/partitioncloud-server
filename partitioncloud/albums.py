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
from . import user

bp = Blueprint("albums", __name__, url_prefix="/albums")


@bp.route("/")
@login_required
def index():
    albums = user.get_albums(session.get("user_id"))

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

    if session.get("user_id") is None:
        # On ne propose pas aux gens non connectés de rejoindre l'album
        not_participant = False
    else:
        not_participant = not user.is_participant(session.get("user_id"), uuid)

    return render_template("albums/album.html", album=album, partitions=partitions, not_participant=not_participant)


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


@bp.route("/<uuid>/join")
def join_album(uuid):
    if session.get("user_id") is None:
        flash("Vous n'êtes pas connecté.")
        return redirect(f"/albums/{uuid}")
    
    db = get_db()
    album_id = db.execute(
        """
        SELECT id FROM album
        WHERE uuid = ?
        """,
        (uuid,)
    ).fetchone()["id"]

    if album_id is None:
        flash("Cet album n'existe pas.")
        return redirect(f"/albums/{uuid}")

    db.execute(
        """
        INSERT INTO contient_user (user_id, album_id)
        VALUES (?, ?)
        """,
        (session.get("user_id"), album_id)
    )
    db.commit()
    flash("Album ajouté à la collection.")
    return redirect(f"/albums/{uuid}")


@bp.route("/<uuid>/delete", methods=["GET", "POST"])
def delete_album(uuid):
    db = get_db()
    if session.get("user_id") is None:
        flash("Vous n'êtes pas connecté.")
        return redirect(f"/albums/{uuid}")

    if request.method == "GET":
        album =  db.execute(
            """
            SELECT * FROM album
            WHERE uuid = ?
            """,
            (uuid,)
        ).fetchone()
        return render_template("albums/delete-album.html", album=album)
    
    error = None
    users = user.get_users(uuid)
    if len(users) > 1:
        error = "Vous n'êtes pas seul dans cet album."
    elif len(users) == 1 and users[0]["id"] != session.get("user_id"):
        error = "Vous ne possédez pas cet album."
    
    if user.access_level(session.get("user-id")) == 1:
        error = None

    if error is not None:
        flash(error)
        return redirect(f"/albums/{uuid}")

    album_id = db.execute(
        """
        SELECT id FROM album
        WHERE uuid = ?
        """,
        (uuid,)
    ).fetchone()["id"]

    db.execute(
        """
        DELETE FROM album
        WHERE uuid = ?
        """,
        (uuid,)
    )
    db.execute(
        """
        DELETE FROM contient_user
        WHERE album_id = ?
        """,
        (album_id,)
    )
    db.execute(
        """
        DELETE FROM contient_partition
        WHERE album_id = ?
        """,
        (album_id,)
    )
    db.commit()
    # Delete orphan partitions
    partitions = db.execute(
        """
        SELECT partition.uuid FROM partition
        WHERE NOT EXISTS (
            SELECT NULL FROM contient_partition 
            WHERE partition.uuid = partition_uuid
        )
        """
    )
    for partition in partitions.fetchall():
        os.remove(f"partitioncloud/partitions/{partition['uuid']}.pdf")
    
    partitions = db.execute(
        """
        DELETE FROM partition
        WHERE uuid IN (
            SELECT partition.uuid FROM partition
            WHERE NOT EXISTS (
                SELECT NULL FROM contient_partition 
                WHERE partition.uuid = partition_uuid
            )
        )
        """
    )
    db.commit()
    flash("Album supprimé.")
    return redirect("/albums")