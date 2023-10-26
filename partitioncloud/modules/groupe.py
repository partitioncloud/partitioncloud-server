#!/usr/bin/python3
"""
Groupe module
"""
import os
from uuid import uuid4

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_file, session, current_app)

from .auth import login_required
from .db import get_db
from .utils import User, Album, get_all_partitions, Groupe
from . import search

bp = Blueprint("groupe", __name__, url_prefix="/groupe")


@bp.route("/")
def index():
    return redirect("/")


@bp.route("/<uuid>")
def groupe(uuid):
    """
    Groupe page
    """
    try:
        groupe = Groupe(uuid=uuid)
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

    except LookupError:
        return abort(404)



@bp.route("/create-groupe", methods=["POST"])
@login_required
def create_groupe():
    current_user = User(user_id=session.get("user_id"))

    name = request.form["name"]
    db = get_db()
    error = None

    if not name or name.strip() == "":
        error = "Un nom est requis. Le groupe n'a pas été créé"

    if error is None:
        while True:
            try:
                uuid = str(uuid4())

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

        if "response" in request.args and request.args["response"] == "json":
            return {
                "status": "ok",
                "uuid": uuid
            }
        else:
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
        flash("Ce groupe n'existe pas.")
        return redirect(f"/groupe/{uuid}")

    flash("Groupe ajouté à la collection.")
    return redirect(f"/groupe/{uuid}")


@bp.route("/<uuid>/quit")
@login_required
def quit_groupe(uuid):
    user = User(user_id=session.get("user_id"))
    groupe = Groupe(uuid=uuid)
    users = groupe.get_users()
    if user.id not in [u["id"] for u in users]:
        flash("Vous ne faites pas partie de ce groupe")
        return redirect(f"/groupe/{uuid}")

    if len(users) == 1:
        flash("Vous êtes seul dans ce groupe, le quitter entraînera sa suppression.")
        return redirect(f"/groupe/{uuid}#delete")

    user.quit_groupe(groupe.uuid)
    flash("Groupe quitté.")
    return redirect(f"/albums")


@bp.route("/<uuid>/delete", methods=["POST"])
@login_required
def delete_groupe(uuid):
    db = get_db()
    groupe = Groupe(uuid=uuid)
    user = User(user_id=session.get("user_id"))
    
    error = None
    users = groupe.get_users()
    if len(users) > 1:
        error = "Vous n'êtes pas seul dans ce groupe."
    
    if user.access_level == 1 or user.id not in groupe.get_admins():
        error = None

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    groupe.delete()

    flash("Groupe supprimé.")
    return redirect("/albums")


@bp.route("/<groupe_uuid>/create-album", methods=["POST"])
@login_required
def create_album(groupe_uuid):
    try:
        groupe = Groupe(uuid=groupe_uuid)
    except LookupError:
        abort(404)

    user = User(user_id=session.get("user_id"))

    name = request.form["name"]
    db = get_db()
    error = None

    if not name or name.strip() == "":
        error = "Un nom est requis. L'album n'a pas été créé"

    if user.id not in groupe.get_admins():
        error ="Vous n'êtes pas administrateur de ce groupe"

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
                    INSERT INTO groupe_contient_album (groupe_id, album_id)
                    VALUES (?, ?)
                    """,
                    (groupe.id, album.id)
                )
                db.commit()

                break
            except db.IntegrityError:
                pass

        if "response" in request.args and request.args["response"] == "json":
            return {
                "status": "ok",
                "uuid": uuid
            }
        else:
            return redirect(f"/groupe/{groupe.uuid}/{uuid}")

    flash(error)
    return redirect(request.referrer)



@bp.route("/<groupe_uuid>/<album_uuid>")
def album(groupe_uuid, album_uuid):
    """
    Album page
    """
    try:
        groupe = Groupe(uuid=groupe_uuid)
    except LookupError:
        abort(404)

    album_list = [a for a in groupe.get_albums() if a.uuid == album_uuid]
    if len(album_list) == 0:
        abort(404)

    album = album_list[0]
    user = User(user_id=session.get("user_id"))

    # List of users without duplicate
    users_id = list(set([i["id"] for i in album.get_users()+groupe.get_users()]))
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