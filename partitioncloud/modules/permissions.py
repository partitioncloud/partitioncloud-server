import functools
from typing import Union, Optional
from flask_babel import _
from flask import current_app

from .db import get_db
from .utils import FakeObject, InvalidRequest
from .classes.user import User
from .classes.album import Album
from .classes.groupe import Groupe
from .classes.partition import Partition
from .classes.attachment import Attachment

class PermError(InvalidRequest):
    def __init__(self, reason: str, redirect: Optional[str]=None):
        super().__init__(reason, redirect=redirect, code=401)
        self.redirect = redirect
        self.reason = reason
        self.code = 401

def admin_bypass(view):
    """Returns if user is admin"""
    @functools.wraps(view)
    def wrapped_view(user: User, *args, **kwargs) -> None:
        if user is not None and user.is_admin:
            return
        return view(user, *args, **kwargs)
    return wrapped_view

def requires_login(view):
    """Raises an error if no user is logged in"""
    @functools.wraps(view)
    def wrapped_view(user: User, *args, **kwargs) -> None:
        if user is None:
            raise PermError(
                _("You need to login to access this resource."),
            )
        return view(user, *args, **kwargs)
    return wrapped_view

def check(perm, *args, **kwargs):
    """
    Wrapper to check if user has the right to do something
    (in templates for instance)
    """
    try:
        perm(*args, **kwargs)
        return True
    except PermError:
        return False


@admin_bypass
@requires_login
def can_delete_groupe(user: User, groupe: Groupe) -> None:
    if user.id in groupe.get_admins():
        return

    if user.id not in groupe.get_users():
        raise PermError(_("You are not a member of this groupe"))

    if len(groupe.get_users()) > 1:
        raise PermError(_("You are not alone in this group."))

@admin_bypass
@requires_login
def has_write_access_groupe(user: User, groupe: Groupe) -> None:
    if user.id in groupe.get_admins():
        return
    raise PermError(_("You are not admin of this group."))

@admin_bypass
@requires_login
def can_delete_album(user: User, album: Album) -> None:
    # We check that this album is not in a groupe, or if it is, if user has rights
    groupe_uuid = album.get_groupe()
    if groupe_uuid is not None:
        return has_write_access_groupe(user, Groupe(uuid=groupe_uuid))

    users = album.get_users()
    if len(users) > 1:
        raise PermError(_("You are not alone in this album."))
    elif user not in users and user.id not in users: #! depending on the type of `album.get_users()`. This is a mess
        raise PermError(_("You don't own this album."))

@admin_bypass
@requires_login
def has_write_access_album(user: User, album: Album) -> None:
    # We check that this album is not in a groupe, or if it is, if user has rights
    groupe_uuid = album.get_groupe()
    if groupe_uuid is not None:
        return has_write_access_groupe(user, Groupe(uuid=groupe_uuid))

    if user.is_participant(album.uuid): #! There is some duplicated behavior here
        return
    raise PermError(_("You are not a member of this album"))

@admin_bypass
@requires_login
def can_delete_partition(user: User, partition: Union[Partition, FakeObject]) -> None:
    if user.id == partition.user_id:
        return
    raise PermError(_("You are not allowed to delete this score."))

@admin_bypass
@requires_login
def has_write_access_partition(user: User, partition: Union[Partition, FakeObject]) -> None:
    if user.id == partition.user_id:
        return
    raise PermError(_("You don't own this score."))

@admin_bypass
@requires_login
def can_delete_attachment(user: User, attachment: Attachment) -> None:
    raise NotImplementedError

@admin_bypass
@requires_login
def can_delete_user(user: User, to_delete_user: Union[User, FakeObject]) -> None:
    if user.id != to_delete_user.id:
        raise PermError(_("Missing rights."))
    if current_app.config["DISABLE_ACCOUNT_DELETION"]:
        raise PermError(_("You are not allowed to delete your account."))

def can_download_zip(user: Optional[User], inst: Union[Album, Groupe]) -> None:
    if not (current_app.config["ZIP_REQUIRE_LOGIN"] and user is None):
        return

    raise PermError(
        _("You need to login to access this resource."),
        redirect="/auth/login",
    )