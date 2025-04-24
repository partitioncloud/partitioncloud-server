#!/usr/bin/python3
"""
Groupe module
"""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, current_app, send_file, g, url_for)
from werkzeug.utils import secure_filename
from flask_babel import _

from .utils import User, Album, Groupe
from .auth import login_required
from .db import get_db

from . import permissions
from . import logging
from . import utils

bp = Blueprint("groupe", __name__, url_prefix="/groupe")


@bp.route("/")
def index():
    return redirect("/")


@bp.route("/<uuid>")
def get_groupe(uuid):
    """
    Groupe page
    """
    try:
        groupe = Groupe(uuid=uuid)
    except LookupError:
        #* Try to load from legacy group uuid,
        #TODO remove on v2
        groupe = Groupe(uuid=utils.format_uuid(uuid))
        return redirect(f"/groupe/{utils.format_uuid(uuid)}")

    groupe.users = [User(user_id=u_id) for u_id in groupe.get_users()]
    groupe.get_albums()
    user = User(user_id=session.get("user_id"))

    if user.id is None:
        # On ne propose pas aux gens non connectés de rejoindre l'album
        not_participant = False
    else:
        not_participant = not user.id in [i.id for i in groupe.users]

    return render_template(
        "groupe/index.html",
        groupe=groupe,
        not_participant=not_participant,
        user=user
    )


@bp.route("/<uuid>/qr")
def album_qr_code(uuid):
    return utils.get_qrcode(f"/groupe/{uuid}")


@bp.route("/create-groupe", methods=["POST"])
@login_required
def create_groupe():
    name = request.form["name"]
    user = User(user_id=session["user_id"])

    if not name or name.strip() == "":
        raise utils.InvalidRequest(_("Missing name."))

    db = get_db()
    while True:
        try:
            uuid = utils.new_uuid()

            db.execute(
                """
                INSERT INTO groupe (uuid, name)
                VALUES (?, ?)
                """,
                (uuid, name),
            )
            db.commit()
            groupe = Groupe(uuid=uuid)
            db.execute(
                """
                INSERT INTO groupe_contient_user (user_id, groupe_id, is_admin)
                VALUES (?, ?, 1)
                """,
                (session.get("user_id"), groupe.id),
            )
            db.commit()

            break
        except db.IntegrityError:
            pass

    logging.log([name, uuid, user.username], logging.LogEntry.NEW_GROUPE)

    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": uuid
        }
    return redirect(f"/groupe/{uuid}")


@bp.route("/<uuid>/join")
@login_required
def join_groupe(uuid):
    user = User(user_id=session.get("user_id"))
    user.join_groupe(uuid)

    flash(_("Group added to collection."))
    return redirect(f"/groupe/{uuid}")


@bp.route("/<uuid>/quit")
@login_required
def quit_groupe(uuid):
    user = User(user_id=session.get("user_id"))
    groupe = Groupe(uuid=uuid)
    users = groupe.get_users()
    if user.id not in users:
        raise utils.InvalidRequest(_("You are not a member of this group."))

    if len(users) == 1:
        flash(_("You are alone here, quitting means deleting this group."))
        return redirect(f"/groupe/{uuid}#delete")

    user.quit_groupe(groupe.uuid)

    if len(groupe.get_admins()) == 0: # On s'assure que le groupe contient toujours des administrateurs
        for user_id in groupe.get_users(force_reload=True):
            groupe.set_admin(user_id, True)

    flash(_("Group quitted."))
    return redirect("/albums")


@bp.route("/<uuid>/delete", methods=["POST"])
@login_required
def delete_groupe(uuid):
    groupe = Groupe(uuid=uuid)
    user = User(user_id=session.get("user_id"))

    permissions.can_delete_groupe(user, groupe)
    groupe.delete(current_app.instance_path)

    flash(_("Group deleted."))
    return redirect("/albums")


@bp.route("/<groupe_uuid>/create-album", methods=["POST"])
@login_required
def create_album_req(groupe_uuid):
    groupe = Groupe(uuid=groupe_uuid)
    user = User(user_id=session.get("user_id"))

    permissions.has_write_access_groupe(user, groupe)

    name = request.form["name"]
    if not name or name.strip() == "":
        raise utils.InvalidRequest(_("Missing name."))

    uuid = utils.create_album(name)
    album = Album(uuid=uuid)

    db = get_db()
    db.execute(
        """
        INSERT INTO groupe_contient_album (groupe_id, album_id)
        VALUES (?, ?)
        """,
        (groupe.id, album.id)
    )
    db.commit()

    logging.log([album.name, album.uuid, user.username], logging.LogEntry.NEW_ALBUM)

    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": uuid
        }
    return redirect(f"/groupe/{groupe.uuid}/{uuid}")



@bp.route("/<groupe_uuid>/<album_uuid>")
def get_album(groupe_uuid, album_uuid):
    """
    Album page
    """
    try:
        groupe = Groupe(uuid=groupe_uuid)
    except LookupError:
        try:
            groupe = Groupe(uuid=utils.format_uuid(groupe_uuid))
            return redirect(f"/groupe/{utils.format_uuid(groupe_uuid)}/{album_uuid}")
        except LookupError:
            return abort(404)

    album_list = [a for a in groupe.get_albums() if a.uuid == album_uuid]
    if len(album_list) == 0:
        album_uuid = utils.format_uuid(album_uuid)
        album_list = [a for a in groupe.get_albums() if a.uuid == album_uuid]
        if len(album_list) != 0:
            return redirect(f"/groupe/{groupe_uuid}/{album_uuid}")
        return abort(404)

    album = album_list[0]
    user = User(user_id=session.get("user_id"))

    # List of users without duplicate
    users_id = list(set(album.get_users()+groupe.get_users()))
    album.users = [User(user_id=id) for id in users_id]

    partitions = album.get_partitions()

    if user.id is None:
        # On ne propose pas aux gens non connectés de rejoindre l'album
        not_participant = False
    else:
        not_participant = not user.is_participant(album.uuid, exclude_groupe=True)

    return render_template(
        "albums/album.html",
        album=album,
        groupe=groupe,
        partitions=partitions,
        not_participant=not_participant,
        user=user
    )


@bp.route("/<groupe_uuid>/zip")
def zip_download(groupe_uuid):
    """
    Télécharger un groupe comme fichier zip
    """
    if g.user is None and current_app.config["ZIP_REQUIRE_LOGIN"]:
        raise utils.InvalidRequest(_("You need to login to access this resource."))
        return redirect(url_for("auth.login"))

    try:
        groupe = Groupe(uuid=groupe_uuid)
    except LookupError:
        groupe = Groupe(uuid=utils.format_uuid(groupe_uuid))
        return redirect(f"/groupe/{utils.format_uuid(groupe_uuid)}/zip")


    return send_file(
        groupe.to_zip(current_app.instance_path),
        download_name=secure_filename(f"{groupe.name}.zip")
    )


@bp.route("/<groupe_uuid>/<album_uuid>/qr")
def groupe_qr_code(groupe_uuid, album_uuid):
    return utils.get_qrcode(f"/groupe/{groupe_uuid}/{album_uuid}")
