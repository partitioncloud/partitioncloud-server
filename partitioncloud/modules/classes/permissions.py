import functools
from flask import current_app
from flask_babel import _

from ..db import get_db
from .user import User
from .album import Album
from .groupe import Groupe
from .partition import Partition
from .attachment import Attachment

class PermError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)

def admin_bypass(view):
    """Returns if user is admin"""
    @functools.wraps(view)
    def wrapped_view(user: User, *args, **kwargs) -> None:
        if user.is_admin:
            return
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
def can_delete_groupe(user: User, groupe: Groupe) -> None:
    if user.id in groupe.get_admins():
        return

    if len(groupe.get_users()) > 1:
        raise PermError(_("You are not alone in this group."))

@admin_bypass
def has_write_access_groupe(user: User, groupe: Groupe) -> None:
    if user.id in groupe.get_admins():
        return
    raise PermError(_("You are not admin of this group."))

@admin_bypass
def can_delete_album(user: User, album: Album) -> None:
    #TODO  We also need to check that this album is not in a groupe,
    #TODO  or if it is, if user has rights
    users = album.get_users()
    if len(users) > 1:
        raise PermError(_("You are not alone in this album."))
    elif user.id not in users:
        raise PermError(_("You don't own this album."))

@admin_bypass
def has_write_access_album(user: User, album: Album) -> None:
    #TODO  We also need to check that this album is not in a groupe,
    #TODO  or if it is, if user has rights
    if user.is_participant(album.uuid):
        return
    raise PermError(_("You are not a member of this album"))

@admin_bypass
def can_delete_partition(user: User, partition: Partition) -> None:
    if user.id == partition.user_id:
        return
    raise PermError(_("You are not allowed to delete this score."))

@admin_bypass
def has_write_access_partition(user: User, partition: Partition) -> None:
    if user.id == partition.user_id:
        return
    raise PermError(_("You don't own this score."))

@admin_bypass
def can_delete_attachment(user: User, attachment: Attachment) -> None:
    raise NotImplementedError

@admin_bypass
def can_delete_user(user: User, to_delete_user: User) -> None:
    if user.id != to_delete_user.id:
        raise PermError(_("Missing rights."))
    if current_app.config["DISABLE_ACCOUNT_DELETION"]:
        raise PermError(_("You are not allowed to delete your account."))
