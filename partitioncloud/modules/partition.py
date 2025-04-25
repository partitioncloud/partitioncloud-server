#!/usr/bin/python3
"""
Partition module
"""
import os
import pypdf
from uuid import uuid4
from flask import (Blueprint, abort, send_file, render_template, g,
                    request, redirect, flash, session, current_app)
from flask_babel import _

from .db import get_db
from .auth import login_required, admin_required
from .utils import User, Partition, Attachment
from . import permissions
from . import utils


bp = Blueprint("partition", __name__, url_prefix="/partition")

@bp.route("/<uuid>")
def get_partition(uuid):
    partition = Partition(uuid=uuid)

    return send_file(os.path.join(
            current_app.instance_path,
            "partitions",
            f"{uuid}.pdf"
        ), download_name = f"{partition.name}.pdf"
    )

@bp.route("/<uuid>/attachments")
def attachments(uuid):
    partition = Partition(uuid=uuid)

    return render_template(
        "partition/attachments.html",
        partition=partition,
        user=User(user_id=session.get("user_id"))
    )


@bp.route("/<uuid>/add-attachment", methods=["POST"])
@login_required
def add_attachment(uuid):
    partition = Partition(uuid=uuid)

    permissions.has_write_access_partition(g.user, partition)

    if "file" not in request.files:
        raise utils.InvalidRequest(_("Missing file"))

    if "name" not in request.form or request.form["name"] == "":
        name = ".".join(request.files["file"].filename.split(".")[:-1])
    else:
        name = request.form["name"]

    if name == "":
        raise utils.InvalidRequest(_("Missing filename."))

    filename = request.files["file"].filename
    ext = filename.split(".")[-1]
    if ext not in ["mid", "mp3"]:
        raise utils.InvalidRequest(_("Unsupported file type."))

    db = get_db()
    while True:
        attachment_uuid = str(uuid4())
        try:
            db.execute(
                """
                INSERT INTO attachments (uuid, name, filetype, partition_uuid, user_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (attachment_uuid, name, ext, partition.uuid, g.user.id),
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
    attachment = Attachment(uuid=uuid)

    if filetype != attachment.filetype:
        abort(404)

    return send_file(os.path.join(
            current_app.instance_path,
            "attachments",
            f"{uuid}.{attachment.filetype}"
        ), download_name = f"{attachment.name}.{attachment.filetype}"
    )


@bp.route("/<uuid>/details", methods=["GET", "POST"])
@login_required
def details(uuid):
    partition = Partition(uuid=uuid)

    permissions.has_write_access_partition(g.user, partition)

    try:
        partition_user = partition.get_user()
    except LookupError:
        partition_user = None

    if request.method == "GET":
        return render_template(
            "partition/details.html",
            partition=partition,
            partition_user=partition_user,
        )

    if "name" not in request.form or request.form["name"].strip() == "":
        raise utils.InvalidRequest(_("Missing title"))
    elif "author" not in request.form:
        raise utils.InvalidRequest(_("Missing author in request body (can be null)."))
    elif "body" not in request.form:
        raise utils.InvalidRequest(_("Missing lyrics (can be null)."))

    if request.files.get('file', None):
        new_file = request.files["file"]
        try:
            pypdf.PdfReader(new_file)
            new_file.seek(0)
        except (pypdf.errors.PdfReadError, pypdf.errors.PdfStreamError):
            raise utils.InvalidRequest(_("Invalid PDF file"), code=415)

        partition.update_file(new_file, current_app.instance_path)

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
    partition = Partition(uuid=uuid)

    permissions.can_delete_partition(g.user, partition)

    if request.method == "GET":
        return render_template("partition/delete.html", partition=partition)

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
        raise LookupError
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
    partitions = utils.get_all_partitions()
    return render_template(
        "admin/partitions.html",
        partitions=partitions
    )
