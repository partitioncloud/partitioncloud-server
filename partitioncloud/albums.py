#!/usr/bin/python3
"""
Albums module
"""
import os
import shutil
from uuid import uuid4

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_file, session)

from .auth import login_required
from .db import get_db
from .utils import User, Album, get_all_partitions
from . import search

bp = Blueprint("albums", __name__, url_prefix="/albums")


@bp.route("/")
@login_required
def index():
    user = User(session.get("user_id"))
    albums = user.get_albums()

    return render_template("albums/index.html", albums=albums)


@bp.route("/search", methods=["POST"])
@login_required
def search_page():
    if "query" not in request.form or request.form["query"] == "":
        flash("Aucun terme de recherche spécifié.")
        return redirect("/albums")

    query = request.form["query"]
    search.flush_cache()
    partitions_local = search.local_search(query, get_all_partitions())
    if "online-search" in request.form:
        google_results = search.online_search(query)
    else:
        google_results = []
    user = User(session.get("user_id"))

    return render_template(
        "albums/search.html",
        partitions=partitions_local,
        google_results=google_results,
        query=query,
        albums=user.get_albums()
    )

@bp.route("/<uuid>")
def album(uuid):
    """
    Album page
    """
    try:
        album = Album(uuid=uuid)
        user = User(session.get("user_id"))
        partitions = album.get_partitions()
        if user.id is None:
            # On ne propose pas aux gens non connectés de rejoindre l'album
            not_participant = False
        else:
            not_participant = not user.is_participant(album.uuid)

        return render_template(
            "albums/album.html",
            album=album,
            partitions=partitions,
            not_participant=not_participant
        )

    except LookupError:
        return abort(404)


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

        if not name or name.strip() == "":
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
                    album = Album(uuid=uuid)
                    db.execute(
                        """
                        INSERT INTO contient_user (user_id, album_id)
                        VALUES (?, ?)
                        """,
                        (session.get("user_id"), album.id),
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
@login_required
def join_album(uuid):
    user = User(session.get("user_id"))
    try:
        user.join_album(uuid)
    except LookupError:
        flash("Cet album n'existe pas.")
        return redirect(f"/albums/{uuid}")

    flash("Album ajouté à la collection.")
    return redirect(f"/albums/{uuid}")


@bp.route("/<uuid>/delete", methods=["GET", "POST"])
@login_required
def delete_album(uuid):
    db = get_db()
    album = Album(uuid=uuid)

    if request.method == "GET":
        return render_template("albums/delete-album.html", album=album)
    
    error = None
    users = album.get_users()
    user = User(session.get("user_id"))
    if len(users) > 1:
        error = "Vous n'êtes pas seul dans cet album."
    elif len(users) == 1 and users[0]["id"] != user.id:
        error = "Vous ne possédez pas cet album."
    
    if user.access_level == 1:
        error = None

    if error is not None:
        flash(error)
        return redirect(f"/albums/{uuid}")

    album.delete()

    flash("Album supprimé.")
    return redirect("/albums")


@bp.route("/<album_uuid>/add-partition", methods=["GET", "POST"])
@login_required
def add_partition(album_uuid):
    db = get_db()
    user = User(session.get("user_id"))
    album = Album(uuid=album_uuid)

    if (not user.is_participant(album.uuid)) and (user.access_level != 1):
        flash("Vous ne participez pas à cet album.")
        return redirect(f"/albums/{album.uuid}")

    if request.method == "GET":
        return render_template("albums/add-partition.html", album=album)

    error = None

    if "name" not in request.form:
        error = "Un titre est requis."
    elif "file" not in request.files:
        if "partition-uuid" not in request.form:
            error = "Aucun fichier n'a été fourni."
        else:
            partition_type = "uuid"
            search_uuid = request.form["partition-uuid"]
            data = db.execute(
                """
                SELECT * FROM search_results
                WHERE uuid = ?
                """,
                (search_uuid,)
            ).fetchone()
            if data is None:
                error = "Les résultats de la recherche ont expiré."
    else:
        partition_type = "file"

    if error is not None:
        flash(error)
        return redirect(f"/albums/{album.uuid}")

    if "author" in request.form:
        author = request.form["author"]
    else:
        author = ""
    if "body" in request.form:
        body = request.form["body"]
    else:
        body = ""

    while True:
        try:
            partition_uuid = str(uuid4())

            db.execute(
                """
                INSERT INTO partition (uuid, name, author, body)
                VALUES (?, ?, ?, ?)
                """,
                (partition_uuid, request.form["name"], author, body),
            )
            db.commit()

            if partition_type == "file":
                file = request.files["file"]
                file.save(f"partitioncloud/partitions/{partition_uuid}.pdf")
            else:
                shutil.copyfile(f"partitioncloud/search-partitions/{search_uuid}.pdf", f"partitioncloud/partitions/{partition_uuid}.pdf")

            os.system(
                f'/usr/bin/convert -thumbnail\
                "178^>" -background white -alpha \
                remove -crop 178x178+0+0 \
                partitioncloud/partitions/{partition_uuid}.pdf[0] \
                partitioncloud/static/thumbnails/{partition_uuid}.jpg'
            )

            album_id = db.execute(
                """
                SELECT id FROM album
                WHERE uuid = ?
                """,
                (album.uuid,)
            ).fetchone()["id"]
            db.commit()

            album.add_partition(partition_uuid)

            break
        except db.IntegrityError:
            pass

    flash(f"Partition {request.form['name']} ajoutée")
    return redirect(f"/albums/{album.uuid}")


@bp.route("/add-partition", methods=["POST"])
@login_required
def add_partition_from_search():
    user = User(session.get("user_id"))
    error = None
    db = get_db()

    if "album-uuid" not in request.form:
        error = "Il est nécessaire de sélectionner un album."
    elif "partition-uuid" not in request.form:
        error = "Il est nécessaire de sélectionner une partition."
    elif "partition-type" not in request.form:
        error = "Il est nécessaire de spécifier un type de partition."
    elif not user.is_participant(request.form["album-uuid"]):
        error = "Vous ne participez pas à cet album."
    
    if error is not None:
        flash(error)
        return redirect("/albums")

    album = Album(request.form["album-uuid"])
    if request.form["partition-type"] == "local_file":
        data = db.execute(
            """
            SELECT * FROM contient_partition
            WHERE album_id = ?
            AND partition_uuid = ?
            """,
            (album.id, request.form["partition-uuid"])
        ).fetchone()

        if data is None:
            album.add_partition(request.form["partition-uuid"])
            flash("Partition ajoutée.")
        else:
            flash("Partition déjà dans l'album.")

        return redirect(f"/albums/{album.uuid}")

    elif request.form["partition-type"] == "online_search":
        return render_template(
            "albums/add-partition.html",
            album=album,
            partition_uuid=request.form["partition-uuid"]
        )

    else:
        flash("Type de partition inconnu.")
        return redirect("/albums")