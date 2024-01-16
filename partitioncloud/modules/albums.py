#!/usr/bin/python3
"""
Albums module
"""
import os
import shutil
from uuid import uuid4
from typing import TypeVar

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, current_app)

from .auth import login_required
from .db import get_db
from .utils import User, Album
from . import search, utils


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
        flash("Aucun terme de recherche spécifié.")
        return redirect("/albums")

    query = request.form["query"]
    nb_queries = abs(int(request.form["nb-queries"]))
    search.flush_cache(current_app.instance_path)
    partitions_local = search.local_search(query, utils.get_all_partitions())

    user = User(user_id=session.get("user_id"))

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

    if not name or name.strip() == "":
        error = "Un nom est requis. L'album n'a pas été créé"

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
        flash("Cet album n'existe pas.")
        return redirect(request.referrer)

    flash("Album ajouté à la collection.")
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
        flash("Vous ne faites pas partie de cet album")
        return redirect(request.referrer)

    if len(users) == 1:
        flash("Vous êtes seul dans cet album, le quitter entraînera sa suppression.")
        return redirect(f"/albums/{uuid}#delete")

    user.quit_album(uuid)
    flash("Album quitté.")
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
        error = "Vous n'êtes pas seul dans cet album."
    elif len(users) == 1 and users[0]["id"] != user.id:
        error = "Vous ne possédez pas cet album."

    if user.access_level == 1:
        error = None

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    album.delete(current_app.instance_path)

    flash("Album supprimé.")
    return redirect("/albums")


@bp.route("/<album_uuid>/add-partition", methods=["POST"])
@login_required
def add_partition(album_uuid):
    """
    Ajouter une partition à un album (par upload)
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
        flash("Vous ne participez pas à cet album.")
        return redirect(request.referrer)

    error = None

    if "name" not in request.form:
        error = "Un titre est requis."
    elif "file" not in request.files and "partition-uuid" not in request.form:
        error = "Aucun fichier n'a été fourni."
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
            error = "Les résultats de la recherche ont expiré."
        else:
            source = data["url"]
    else:
        partition_type = "file"

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    author = get_opt_string(request.form, "author")
    body = get_opt_string(request.form, "body")

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

            os.system(
                f'/usr/bin/convert -thumbnail\
                "178^>" -background white -alpha \
                remove -crop 178x178+0+0 \
                {partition_path}[0] \
                partitioncloud/static/thumbnails/{partition_uuid}.jpg'
            )
            db.commit()

            album.add_partition(partition_uuid)

            break
        except db.IntegrityError:
            pass

    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": partition_uuid
        }
    flash(f"Partition {request.form['name']} ajoutée")
    return redirect(f"/albums/{album.uuid}")


@bp.route("/add-partition", methods=["POST"])
@login_required
def add_partition_from_search():
    """
    Ajout d'une partition (depuis la recherche)
    """
    user = User(user_id=session.get("user_id"))
    error = None

    if "album-uuid" not in request.form:
        error = "Il est nécessaire de sélectionner un album."
    elif "partition-uuid" not in request.form:
        error = "Il est nécessaire de sélectionner une partition."
    elif "partition-type" not in request.form:
        error = "Il est nécessaire de spécifier un type de partition."
    elif (not user.is_participant(request.form["album-uuid"])) and (user.access_level != 1):
        error = "Vous ne participez pas à cet album."

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
            flash("Partition ajoutée.")
        else:
            flash("Partition déjà dans l'album.")

        return redirect(f"/albums/{album.uuid}")

    if request.form["partition-type"] == "online_search":
        return render_template(
            "albums/add-partition.html",
            album=album,
            partition_uuid=request.form["partition-uuid"],
            user=user
        )

    flash("Type de partition inconnu.")
    return redirect("/albums")
