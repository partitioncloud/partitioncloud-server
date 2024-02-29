#!/usr/bin/python3
"""
Albums module
"""
import os
import pypdf
import shutil

from uuid import uuid4
from typing import TypeVar

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, current_app)
from flask_babel import _

from .auth import login_required
from .db import get_db
from .utils import User, Album
from . import search, utils, logging


bp = Blueprint("albums", __name__, url_prefix="/albums")


@bp.route("/")
@login_required
def index():
    """
    Albums home page
    """
    user = User(user_id=session.get("user_id"))

    return render_template("albums/index.html", user=user)


@bp.route("/search", methods=["POST"])
@login_required
def search_page():
    """
    Résultats de recherche
    """
    if "query" not in request.form or request.form["query"] == "":
        flash(_("Missing search query"))
        return redirect("/albums")

    user = User(user_id=session.get("user_id"))

    query = request.form["query"]
    nb_queries = abs(int(request.form["nb-queries"]))
    search.flush_cache(current_app.instance_path)
    
    partitions_list = None
    if current_app.config["PRIVATE_SEARCH"]:
        partitions_list = utils.get_all_partitions()
    else:
        partitions_list = user.get_accessible_partitions()
    partitions_local = search.local_search(query, partitions_list)

    if nb_queries > 0:
        if user.access_level != 1:
            nb_queries = min(current_app.config["MAX_ONLINE_QUERIES"], nb_queries)
        else:
            nb_queries = min(10, nb_queries) # Query limit is 10 for an admin
        google_results = search.online_search(query, nb_queries, current_app.instance_path)
    else:
        google_results = []

    user.get_albums()

    return render_template(
        "albums/search.html",
        partitions=partitions_local,
        google_results=google_results,
        query=query,
        user=user
    )

@bp.route("/<uuid>")
def get_album(uuid):
    """
    Album page
    """
    try:
        album = Album(uuid=uuid)
    except LookupError:
        try:
            album = Album(uuid=utils.format_uuid(uuid))
            return redirect(f"/albums/{utils.format_uuid(uuid)}")
        except LookupError:
            return abort(404)

    album.users = [User(user_id=i["id"]) for i in album.get_users()]
    user = User(user_id=session.get("user_id"))
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
        not_participant=not_participant,
        user=user
    )


@bp.route("/<uuid>/qr")
def qr_code(uuid):
    """
    Renvoie le QR Code d'un album
    """
    return utils.get_qrcode(f"/albums/{uuid}")


@bp.route("/create-album", methods=["POST"])
@login_required
def create_album_req():
    """
    Création d'un album
    """
    name = request.form["name"]
    db = get_db()
    error = None

    user = User(user_id=session["user_id"])

    if not name or name.strip() == "":
        error = _("Missing name.")

    if error is None:
        uuid = utils.create_album(name)
        album = Album(uuid=uuid)
        db.execute(
            """
            INSERT INTO contient_user (user_id, album_id)
            VALUES (?, ?)
            """,
            (session.get("user_id"), album.id),
        )
        db.commit()

        logging.log([album.name, album.uuid, user.username], logging.LogEntry.NEW_ALBUM)

        if "response" in request.args and request.args["response"] == "json":
            return {
                "status": "ok",
                "uuid": uuid
            }
        return redirect(f"/albums/{uuid}")

    flash(error)
    return redirect(request.referrer)


@bp.route("/<uuid>/join")
@login_required
def join_album(uuid):
    """
    Rejoindre un album
    """
    user = User(user_id=session.get("user_id"))
    try:
        user.join_album(uuid)
    except LookupError:
        flash(_("This album does not exist."))
        return redirect(request.referrer)

    flash(_("Album added to collection."))
    return redirect(request.referrer)


@bp.route("/<uuid>/quit")
@login_required
def quit_album(uuid):
    """
    Quitter un album
    """
    user = User(user_id=session.get("user_id"))
    album = Album(uuid=uuid)
    users = album.get_users()
    if user.id not in [u["id"] for u in users]:
        flash(_("You are not a member of this album"))
        return redirect(request.referrer)

    if len(users) == 1:
        flash(_("You are alone here, quitting means deleting this album."))
        return redirect(f"/albums/{uuid}#delete")

    user.quit_album(uuid)
    flash(_("Album quitted."))
    return redirect("/albums")


@bp.route("/<uuid>/delete", methods=["GET", "POST"])
@login_required
def delete_album(uuid):
    """
    Supprimer un album
    """
    album = Album(uuid=uuid)
    user = User(user_id=session.get("user_id"))

    if request.method == "GET":
        return render_template("albums/delete-album.html", album=album, user=user)

    error = None
    users = album.get_users()
    if len(users) > 1:
        error = _("You are not alone in this album.")
    elif len(users) == 1 and users[0]["id"] != user.id:
        error = _("You don't own this album.")

    if user.access_level == 1:
        error = None

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    album.delete(current_app.instance_path)

    flash(_("Album deleted."))
    return redirect("/albums")


@bp.route("/<album_uuid>/add-partition", methods=["POST"])
@login_required
def add_partition(album_uuid):
    """
    Ajouter une partition à un album (nouveau fichier)
    """
    T = TypeVar("T")
    def get_opt_string(dictionary: dict[T, str], key: T):
        """Renvoie '' si la clé n'existe pas dans le dictionnaire"""
        if key in dictionary:
            return dictionary[key]
        return ""

    db = get_db()
    user = User(user_id=session.get("user_id"))
    album = Album(uuid=album_uuid)
    source = "upload" # source type: upload, unknown or url

    if (not user.is_participant(album.uuid)) and (user.access_level != 1):
        flash(_("You are not a member of this album"))
        return redirect(request.referrer)

    error = None

    if "name" not in request.form:
        error = _("Missing title")
    elif "file" not in request.files and "partition-uuid" not in request.form:
        error = _("Missing file")
    elif "file" not in request.files:
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
            error = _("Search results expired")
        else:
            source = data["url"]
    else:
        partition_type = "file"

        try:
            pypdf.PdfReader(request.files["file"])
            request.files["file"].seek(0)
        except (pypdf.errors.PdfReadError, pypdf.errors.PdfStreamError):
            error = _("Invalid PDF file")

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    author = get_opt_string(request.form, "author")
    body = get_opt_string(request.form, "body")

    partition_uuid: str
    while True:
        try:
            partition_uuid = str(uuid4())

            db.execute(
                """
                INSERT INTO partition (uuid, name, author, body, user_id, source)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (partition_uuid, request.form["name"], author, body, user.id, source),
            )
            db.commit()

            partition_path = os.path.join(
                current_app.instance_path,
                "partitions",
                f"{partition_uuid}.pdf"
            )

            if partition_type == "file":
                file = request.files["file"]
                file.save(partition_path)
            else:
                search_partition_path = os.path.join(
                    current_app.instance_path,
                    "search-partitions",
                    f"{search_uuid}.pdf"
                )

                shutil.copyfile(
                    search_partition_path,
                    partition_path
                )

            db.commit()

            album.add_partition(partition_uuid)

            break
        except db.IntegrityError:
            pass

    logging.log(
        [request.form["name"], partition_uuid, user.username],
        logging.LogEntry.NEW_PARTITION
    )

    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": partition_uuid
        }
    flash(_("Score %(partition_name)s added", partition_name=request.form['name']))
    return redirect(f"/albums/{album.uuid}")


@bp.route("/add-partition", methods=["POST"])
@login_required
def add_partition_from_search():
    """
    Ajout d'une partition (depuis la recherche locale)
    """
    user = User(user_id=session.get("user_id"))
    error = None

    if "album-uuid" not in request.form:
        error = _("Selecting an album is mandatory.")
    elif "partition-uuid" not in request.form:
        error = _("Selecting a score is mandatory.")
    elif "partition-type" not in request.form:
        error = _("Please specify a score type.")
    elif (not user.is_participant(request.form["album-uuid"])) and (user.access_level != 1):
        error = _("You are not a member of this album")

    if error is not None:
        flash(error)
        return redirect("/albums")

    album = Album(request.form["album-uuid"])
    if request.form["partition-type"] == "local_file":
        db = get_db()
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
            flash(_("Score added"))
        else:
            flash(_("Score is already in the album."))

        return redirect(f"/albums/{album.uuid}")

    if request.form["partition-type"] == "online_search":
        return render_template(
            "albums/add-partition.html",
            album=album,
            partition_uuid=request.form["partition-uuid"],
            user=user
        )

    flash(_("Unknown score type."))
    return redirect("/albums")
