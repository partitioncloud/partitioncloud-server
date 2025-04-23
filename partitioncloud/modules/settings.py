#!/usr/bin/python3
"""
User Settings
"""
import os
from flask import Blueprint, render_template, session, current_app, send_file, request, flash, redirect
from werkzeug.security import check_password_hash

from flask_babel import _

from .db import get_db
from .auth import login_required
from .utils import User
from . import logging


bp = Blueprint("settings", __name__, url_prefix="/settings")

@bp.route("/")
@login_required
def index():
    """
    Settings page
    """
    user = User(user_id=session.get("user_id"))

    return render_template(
        "settings/index.html",
        inspected_user=user,
        user=user,
        deletion_allowed=not current_app.config["DISABLE_ACCOUNT_DELETION"]
    )


@bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    log_data = None
    if "user_id" not in request.form:
        flash(_("Missing user id."))
        return redirect(request.referrer)

    cur_user = User(user_id=session.get("user_id"))
    user_id = request.form["user_id"]
    mod_user = User(user_id=user_id)

    if not cur_user.is_admin:
        log_data = [mod_user.username, mod_user.id]
        if cur_user.id != mod_user.id:
            flash(_("Missing rights."))
            return redirect(request.referrer)

        if current_app.config["DISABLE_ACCOUNT_DELETION"]:
            flash(_("You are not allowed to delete your account."))
            return redirect(request.referrer)
    else:
        log_data = [mod_user.username, mod_user.id, cur_user.username]

    mod_user.delete()
    flash(_("User successfully deleted."))
    logging.log(log_data, logging.LogEntry.DELETE_ACCOUNT)
    if cur_user.id == mod_user.id:
        return redirect("/")
    return redirect("/admin")


@bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    log_data = None
    if "user_id" not in request.form:
        flash(_("Missing user id."))
        return redirect(request.referrer)

    cur_user = User(user_id=session.get("user_id"))
    user_id = request.form["user_id"]
    mod_user = User(user_id=user_id)

    if cur_user.access_level != 1:
        log_data = [mod_user.username, mod_user.id]
        if cur_user.id != mod_user.id:
            flash(_("Missing rights."))
            return redirect(request.referrer)

        if "old_password" not in request.form:
            flash(_("Missing old password."))
            return redirect(request.referrer)

        if not check_password_hash(mod_user.password, request.form["old_password"]):
            flash(_("Incorrect password."))
            return redirect(request.referrer)
    else:
        log_data = [mod_user.username, mod_user.id, cur_user.username]

    if "new_password" not in request.form or "confirm_new_password" not in request.form:
        flash(_("Missing password."))
        return redirect(request.referrer)

    if request.form["new_password"] != request.form["confirm_new_password"]:
        flash(_("Password and its confirmation differ."))
        return redirect(request.referrer)

    mod_user.update_password(request.form["new_password"])
    flash(_("Successfully updated password."))
    logging.log(log_data, logging.LogEntry.PASSWORD_CHANGE)
    return redirect(request.referrer)
