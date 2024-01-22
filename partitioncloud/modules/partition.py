#!/usr/bin/python3
"""
Partition module
"""
import os
from uuid import uuid4
from flask import (Blueprint, abort, send_file, render_template,
                    request, redirect, flash, session, current_app)
from flask_babel import _

from .db import get_db
from .auth import login_required, admin_required
from .utils import get_all_partitions, User, Partition, Attachment


bp = Blueprint("partition", __name__, url_prefix="/partition")

@bp.route("/<uuid>")
def get_partition(uuid):
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)


    return send_file(os.path.join(
            current_app.instance_path,
            "partitions",
            f"{uuid}.pdf"
        ), download_name = f"{partition.name}.pdf"
    )

@bp.route("/<uuid>/attachments")
def attachments(uuid):
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)

    partition.load_attachments()
    return render_template(
        "partition/attachments.html",
        partition=partition,
        user=User(user_id=session.get("user_id"))
    )


@bp.route("/<uuid>/add-attachment", methods=["POST"])
@login_required
def add_attachment(uuid):
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)
    user = User(user_id=session.get("user_id"))

    if user.id != partition.user_id and user.access_level != 1:
        flash(_("Cette partition ne vous appartient pas"))
        return redirect(request.referrer)

    error = None # À mettre au propre
    if "file" not in request.files:
        error = _("Aucun fichier n'a été fourni.")
    else:
        if "name" not in request.form or request.form["name"] == "":
            name = ".".join(request.files["file"].filename.split(".")[:-1])
        else:
            name = request.form["name"]

        if name == "":
            error = _("Pas de nom de fichier")
        else:
            filename = request.files["file"].filename
            ext = filename.split(".")[-1]
            if ext not in ["mid", "mp3"]:
                error = _("Extension de fichier non supportée")

    if error is not None:
        flash(error)
        return redirect(request.referrer)

    while True:
        try:
            attachment_uuid = str(uuid4())

            db = get_db()
            db.execute(
                """
                INSERT INTO attachments (uuid, name, filetype, partition_uuid, user_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (attachment_uuid, name, ext, partition.uuid, user.id),
            )
            db.commit()

            file = request.files["file"]
            file.save(os.path.join(
                current_app.instance_path,
                "attachments",
                f"{attachment_uuid}.{ext}"
            ))
            break

        except db.IntegrityError:
            pass


    if "response" in request.args and request.args["response"] == "json":
        return {
            "status": "ok",
            "uuid": attachment_uuid
        }
    return redirect(f"/partition/{partition.uuid}/attachments")


@bp.route("/attachment/<uuid>.<filetype>")
def get_attachment(uuid, filetype):
    try:
        attachment = Attachment(uuid=uuid)
    except LookupError:
        abort(404)

    assert filetype == attachment.filetype

    return send_file(os.path.join(
            current_app.instance_path,
            "attachments",
            f"{uuid}.{attachment.filetype}"
        ), download_name = f"{attachment.name}.{attachment.filetype}"
    )



@bp.route("/<uuid>/edit", methods=["GET", "POST"])
@login_required
def edit(uuid):
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)

    user = User(user_id=session.get("user_id"))
    if user.access_level != 1 and partition.user_id != user.id:
        flash(_("Vous n'êtes pas autorisé à modifier cette partition."))
        return redirect("/albums")

    if request.method == "GET":
        return render_template("partition/edit.html", partition=partition, user=user)

    error = None

    if "name" not in request.form or request.form["name"].strip() == "":
        error = _("Un titre est requis.")
    elif "author" not in request.form:
        error = _("Un nom d'auteur est requis (à minima nul)")
    elif "body" not in request.form:
        error = _("Des paroles sont requises (à minima nulles)")

    if error is not None:
        flash(error)
        return redirect(f"/partition/{ uuid }/edit")

    partition.update(
        name=request.form["name"],
        author=request.form["author"],
        body=request.form["body"]
    )

    flash(_("Partition %(name)s modifiée avec succès.", name=request.form['name']))
    return redirect("/albums")


@bp.route("/<uuid>/details", methods=["GET", "POST"])
@admin_required
def details(uuid):
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)

    user = User(user_id=session.get("user_id"))
    try:
        partition_user = partition.get_user()
    except LookupError:
        partition_user = None

    if request.method == "GET":
        return render_template(
            "partition/details.html",
            partition=partition,
            partition_user=partition_user,
            albums=partition.get_albums(),
            user=user
        )

    error = None

    if "name" not in request.form or request.form["name"].strip() == "":
        error = _("Un titre est requis.")
    elif "author" not in request.form:
        error = _("Un nom d'auteur est requis (à minima nul)")
    elif "body" not in request.form:
        error = _("Des paroles sont requises (à minima nulles)")

    if error is not None:
        flash(error)
        return redirect(f"/partition/{ uuid }/details")

    partition.update(
        name=request.form["name"],
        author=request.form["author"],
        body=request.form["body"]
    )

    flash(_("Partition %(name)s modifiée avec succès.", name=request.form['name']))
    return redirect("/albums")


@bp.route("/<uuid>/delete", methods=["GET", "POST"])
@login_required
def delete(uuid):
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)

    user = User(user_id=session.get("user_id"))

    if user.access_level != 1 and partition.user_id != user.id:
        flash(_("Vous n'êtes pas autorisé à supprimer cette partition."))
        return redirect("/albums")

    if request.method == "GET":
        return render_template("partition/delete.html", partition=partition, user=user)

    partition.delete(current_app.instance_path)

    flash(_("Partition supprimée."))
    return redirect("/albums")


@bp.route("/search/<uuid>")
@login_required
def partition_search(uuid):
    db = get_db()
    partition = db.execute(
        """
        SELECT uuid, url FROM search_results
        WHERE uuid = ?
        """,
        (uuid,)
    ).fetchone()

    if partition is None:
        abort(404)
    if request.args.get("redirect") == "true" and partition["url"] is not None:
        return redirect(partition["url"])

    return send_file(os.path.join(
            current_app.instance_path,
            "search-partitions",
            f"{uuid}.pdf"
        )
    )


@bp.route("/")
@admin_required
def index():
    partitions = get_all_partitions()
    user = User(user_id=session.get("user_id"))
    return render_template("admin/partitions.html", partitions=partitions, user=user)
