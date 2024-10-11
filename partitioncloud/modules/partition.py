#!/usr/bin/python3
"""
Partition module
"""
import os
import pypdf
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
        flash(_("You don't own this score."))
        return redirect(request.referrer)

    error = None # À mettre au propre
    if "file" not in request.files:
        error = _("Missing file")
    else:
        if "name" not in request.form or request.form["name"] == "":
            name = ".".join(request.files["file"].filename.split(".")[:-1])
        else:
            name = request.form["name"]

        if name == "":
            error = _("Missing filename.")
        else:
            filename = request.files["file"].filename
            ext = filename.split(".")[-1]
            if ext not in ["mid", "mp3"]:
                error = _("Unsupported file type.")

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
        flash(_("You are not allowed to edit this file."))
        return redirect("/albums")

    if request.method == "GET":
        return render_template("partition/edit.html", partition=partition, user=user)

    error = None

    if "name" not in request.form or request.form["name"].strip() == "":
        error = _("Missing title")
    elif "author" not in request.form:
        error = _("Missing author in request body (can be null).")
    elif "body" not in request.form:
        error = _("Missing lyrics (can be null).")

    if error is not None:
        flash(error)
        return redirect(f"/partition/{ uuid }/edit")

    if request.files.get('file', None):
        new_file = request.files["file"]
        try:
            pypdf.PdfReader(new_file)
            new_file.seek(0)
        except (pypdf.errors.PdfReadError, pypdf.errors.PdfStreamError):
            flash(_("Invalid PDF file"))
            return redirect(request.referrer)

        partition.update_file(new_file, current_app.instance_path)

    partition.update(
        name=request.form["name"],
        author=request.form["author"],
        body=request.form["body"]
    )

    flash(_("Successfully modified %(name)s", name=request.form['name']))
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
        error = _("Missing title")
    elif "author" not in request.form:
        error = _("Missing author in request body (can be null).")
    elif "body" not in request.form:
        error = _("Missing lyrics (can be null).")

    if error is not None:
        flash(error)
        return redirect(f"/partition/{ uuid }/details")

    partition.update(
        name=request.form["name"],
        author=request.form["author"],
        body=request.form["body"]
    )

    flash(_("Successfully modified %(name)s", name=request.form['name']))
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
        flash(_("You are not allowed to delete this score."))
        return redirect("/albums")

    if request.method == "GET":
        return render_template("partition/delete.html", partition=partition, user=user)

    partition.delete(current_app.instance_path)

    flash(_("Score deleted."))
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
