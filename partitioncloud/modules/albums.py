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
                   request, session, current_app, send_file, g, url_for)
from werkzeug.utils import secure_filename
from flask_babel import _

from .auth import login_required
from .db import get_db
from .utils import User, Album, Partition
from . import search, utils, logging
from . import permissions


bp = Blueprint("albums", __name__, url_prefix="/albums")


@bp.route("/")
@login_required
def index():
    """
    Albums home page
    """
    return render_template("albums/index.html")


@bp.route("/search", methods=["POST"])
@login_required
def search_page():
    """
    Résultats de recherche
    """
    if "query" not in request.form or request.form["query"] == "":
        raise utils.InvalidRequest(_("Missing search query"))

    query = request.form["query"]
    nb_queries = abs(int(request.form["nb-queries"]))
    search.flush_cache(current_app.instance_path)

    partitions_list = None
    if current_app.config["PRIVATE_SEARCH"]:
        partitions_list = utils.get_all_partitions()
    else:
        partitions_list = g.user.get_accessible_partitions()
    partitions_local = search.local_search(query, partitions_list)

    if nb_queries > 0:
        nb_queries = min(g.user.max_queries, nb_queries)
        google_results = search.online_search(query, nb_queries, current_app.instance_path)
    else:
        google_results = []

    return render_template(
        "albums/search.html",
        partitions=partitions_local,
        google_results=google_results,
        query=query
    )

@bp.route("/<uuid>")
def get_album(uuid):
    """
    Album page
    """
    try:
        album = Album(uuid=uuid)
    except LookupError:
        try: #TODO remove in v2
            album = Album(uuid=utils.format_uuid(uuid))
            return redirect(f"/albums/{utils.format_uuid(uuid)}")
        except LookupError:
            return abort(404)

    partitions = album.get_partitions()
    return render_template(
        "albums/album.html",
        album=album,
        partitions=partitions,
    )


@bp.route("/<uuid>/qr")
def qr_code(uuid):
    """
    Renvoie le QR Code d'un album
    """
    return utils.get_qrcode(f"/albums/{uuid}")


@bp.route("/<uuid>/zip")
def zip_download(uuid):
    """
    Télécharger un album comme fichier zip
    """
    album = Album(uuid=uuid)
    permissions.can_download_zip(g.user, album)

    return send_file(
        album.to_zip(current_app.instance_path),
        download_name=secure_filename(f"{album.name}.zip")
    )


@bp.route("/create-album", methods=["POST"])
@login_required
def create_album_req():
    """
    Création d'un album
    """
    name = request.form["name"]

    if not name or name.strip() == "":
        raise utils.InvalidRequest(_("Missing name."))

    uuid = utils.create_album(name)

    db = get_db()
    album = Album(uuid=uuid)
    g.user.join_album(album_id=album.id)

    logging.log([album.name, album.uuid, g.user.username], logging.LogEntry.NEW_ALBUM)

    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": uuid
        }
    return redirect(f"/albums/{uuid}")


@bp.route("/<uuid>/join")
@login_required
def join_album(uuid):
    """
    Rejoindre un album
    """
    g.user.join_album(album_uuid=uuid)

    flash(_("Album added to collection."))
    return redirect(request.referrer)


@bp.route("/<uuid>/quit")
@login_required
def quit_album(uuid):
    """
    Quitter un album
    """
    album = Album(uuid=uuid)

    users = album.get_users()
    if g.user not in users:
        raise utils.InvalidRequest(_("You are not a member of this album"))

    if len(users) == 1 and album.get_groupe() is None:
        flash(_("You are alone here, quitting means deleting this album."))
        return redirect(f"/albums/{uuid}#delete")

    g.user.quit_album(album)
    flash(_("Album quitted."))
    return redirect("/albums")


@bp.route("/<uuid>/delete", methods=["GET", "POST"])
@login_required
def delete_album(uuid):
    """
    Supprimer un album
    """
    album = Album(uuid=uuid)

    if request.method == "GET":
        return render_template("albums/delete-album.html", album=album)

    permissions.can_delete_album(g.user, album)
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
    album = Album(uuid=album_uuid)
    source = "upload" # source type: upload, unknown or url

    permissions.has_write_access_album(g.user, album)

    if "name" not in request.form:
        raise utils.InvalidRequest(_("Missing title"))
    elif "file" not in request.files and "partition-uuid" not in request.form:
        raise utils.InvalidRequest(_("Missing file"))
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
            raise utils.InvalidRequest(_("Search results expired"))
        source = data["url"]
    else:
        partition_type = "file"

        try:
            pypdf.PdfReader(request.files["file"])
            request.files["file"].seek(0)
        except (pypdf.errors.PdfReadError, pypdf.errors.PdfStreamError):
            raise utils.InvalidRequest(_("Invalid PDF file"), code=415)

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
                (partition_uuid, request.form["name"], author, body, g.user.id, source),
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
        [request.form["name"], partition_uuid, g.user.username],
        logging.LogEntry.NEW_PARTITION
    )

    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": partition_uuid
        }
    flash(_("Score %(partition_name)s added", partition_name=request.form["name"]))
    return redirect(f"/albums/{album.uuid}")


@bp.route("/add-partition", methods=["POST"])
@login_required
def add_partition_from_search():
    """
    Ajout d'une partition (depuis la recherche locale)
    """
    album = Album(uuid=request.form["album-uuid"])

    if "album-uuid" not in request.form:
        raise utils.InvalidRequest(_("Selecting an album is mandatory."))
    elif "partition-uuid" not in request.form:
        raise utils.InvalidRequest(_("Selecting a score is mandatory."))
    elif "partition-type" not in request.form:
        raise utils.InvalidRequest(_("Please specify a score type."))

    permissions.has_write_access_album(g.user, album)

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

        if data is not None:
            raise utils.InvalidRequest(
                _("Score is already in the album."),
                redirect=f"/albums/{album.uuid}"
            )

        album.add_partition(request.form["partition-uuid"])
        flash(_("Score added"))
        return redirect(f"/albums/{album.uuid}")

    if request.form["partition-type"] == "online_search":
        return render_template(
            "albums/add-partition.html",
            album=album,
            partition_uuid=request.form["partition-uuid"],
        )

    raise utils.InvalidRequest(
        _("Unknown score type."),
        redirect="/albums"
    )
