#!/usr/bin/python3
"""
Partition module
"""
import os
from flask import Blueprint, abort, send_file, render_template, request, redirect, flash, session

from .db import get_db
from .auth import login_required, admin_required
from .utils import get_all_partitions, User, Partition


bp = Blueprint("partition", __name__, url_prefix="/partition")

@bp.route("/<uuid>")
def partition(uuid):
    db = get_db()
    partition = db.execute(
        """
        SELECT * FROM partition
        WHERE uuid = ?
        """,
        (uuid,)
    ).fetchone()

    if partition is None:
        abort(404)
    return send_file(
        os.path.join("partitions", f"{uuid}.pdf"),
        download_name = f"{partition['name']}.pdf"
    )

@bp.route("/<uuid>/edit", methods=["GET", "POST"])
@login_required
def edit(uuid):
    db = get_db()
    try:
        partition = Partition(uuid=uuid)
    except LookupError:
        abort(404)

    user = User(user_id=session.get("user_id"))
    if user.access_level != 1 and partition.user_id != user.id:
        flash("Vous n'êtes pas autorisé à modifier cette partition.")
        return redirect("/albums")

    if request.method == "GET":
        return render_template("partition/edit.html", partition=partition, user=user)

    error = None

    if "name" not in request.form or request.form["name"].strip() == "":
        error = "Un titre est requis."
    elif "author" not in request.form:
        error = "Un nom d'auteur est requis (à minima nul)"
    elif "body" not in request.form:
        error = "Des paroles sont requises (à minima nulles)"

    if error is not None:
        flash(error)
        return redirect(f"/partition/{ uuid }/edit")
    
    partition.update(
        name=request.form["name"],
        author=request.form["author"],
        body=request.form["body"]
    )

    flash(f"Partition {request.form['name']} modifiée avec succès.")
    return redirect("/albums")


@bp.route("/<uuid>/details", methods=["GET", "POST"])
@admin_required
def details(uuid):
    db = get_db()
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
        error = "Un titre est requis."
    elif "author" not in request.form:
        error = "Un nom d'auteur est requis (à minima nul)"
    elif "body" not in request.form:
        error = "Des paroles sont requises (à minima nulles)"

    if error is not None:
        flash(error)
        return redirect(f"/partition/{ uuid }/details")
    
    partition.update(
        name=request.form["name"],
        author=request.form["author"],
        body=request.form["body"]
    )

    flash(f"Partition {request.form['name']} modifiée avec succès.")
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
        flash("Vous n'êtes pas autorisé à supprimer cette partition.")
        return redirect("/albums")

    if request.method == "GET":
        return render_template("partition/delete.html", partition=partition, user=user)

    partition.delete()

    flash("Partition supprimée.")
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
    return send_file(os.path.join("search-partitions", f"{uuid}.pdf"))


@bp.route("/")
@admin_required
def index():
    partitions = get_all_partitions()
    user = User(user_id=session.get("user_id"))
    return render_template("admin/partitions.html", partitions=partitions, user=user)