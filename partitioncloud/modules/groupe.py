#!/usr/bin/python3
"""
Groupe module
"""
from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, current_app)
from flask_babel import _

from .auth import login_required
from .db import get_db
from .utils import User, Album, Groupe
from . import utils
from . import logging

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
        try:
            groupe = Groupe(uuid=utils.format_uuid(uuid))
            return redirect(f"/groupe/{utils.format_uuid(uuid)}")
        except LookupError:
            return abort(404)

    groupe.users = [User(user_id=i["id"]) for i in groupe.get_users()]
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
    db = get_db()
    error = None

    user = User(user_id=session["user_id"])

    if not name or name.strip() == "":
        error = _("Un nom est requis. Le groupe n'a pas été créé")

    if error is None:
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

    flash(error)
    return redirect(request.referrer)


@bp.route("/<uuid>/join")
@login_required
def join_groupe(uuid):
    user = User(user_id=session.get("user_id"))
    try:
        user.join_groupe(uuid)
    except LookupError:
        flash(_("Ce groupe n'existe pas."))
        return redirect(f"/groupe/{uuid}")

    flash(_("Groupe ajouté à la collection."))
    return redirect(f"/groupe/{uuid}")


@bp.route("/<uuid>/quit")
@login_required
def quit_groupe(uuid):
    user = User(user_id=session.get("user_id"))
    groupe = Groupe(uuid=uuid)
    users = groupe.get_users()
    if user.id not in [u["id"] for u in users]:
        flash(_("Vous ne faites pas partie de ce groupe"))
        return redirect(f"/groupe/{uuid}")

    if len(users) == 1:
        flash(_("Vous êtes seul dans ce groupe, le quitter entraînera sa suppression."))
        return redirect(f"/groupe/{uuid}#delete")

    user.quit_groupe(groupe.uuid)
    flash(_("Groupe quitté."))
    return redirect("/albums")


@bp.route("/<uuid>/delete", methods=["POST"])
@login_required
def delete_groupe(uuid):
    groupe = Groupe(uuid=uuid)
    user = User(user_id=session.get("user_id"))

    error = None
    users = groupe.get_users()
    if len(users) > 1:
        error = _("Vous n'êtes pas seul dans ce groupe.")

    if user.access_level == 1 or user.id not in groupe.get_admins():
        error = None

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    groupe.delete(current_app.instance_path)

    flash(_("Groupe supprimé."))
    return redirect("/albums")


@bp.route("/<groupe_uuid>/create-album", methods=["POST"])
@login_required
def create_album_req(groupe_uuid):
    try:
        groupe = Groupe(uuid=groupe_uuid)
    except LookupError:
        abort(404)

    user = User(user_id=session.get("user_id"))

    name = request.form["name"]
    db = get_db()
    error = None

    if not name or name.strip() == "":
        error = _("Un nom est requis. L'album n'a pas été créé")

    if user.id not in groupe.get_admins():
        error = _("Vous n'êtes pas administrateur de ce groupe")

    if error is None:
        uuid = utils.create_album(name)
        album = Album(uuid=uuid)

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

    flash(error)
    return redirect(request.referrer)



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
    users_id = list({i["id"] for i in album.get_users()+groupe.get_users()})
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


@bp.route("/<groupe_uuid>/<album_uuid>/qr")
def groupe_qr_code(groupe_uuid, album_uuid):
    return utils.get_qrcode(f"/groupe/{groupe_uuid}/{album_uuid}")
