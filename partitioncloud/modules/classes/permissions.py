import functools
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
    def wrapped_view(user, *args, **kwargs):
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
    raise NotImplementedError

@admin_bypass
def has_write_access_album(user: User, album: Album) -> None:
    raise NotImplementedError

@admin_bypass
def can_delete_partition(user: User, partition: Partition) -> None:
    raise NotImplementedError

@admin_bypass
def has_write_access_partition(user: User, partition: Partition) -> None:
    raise NotImplementedError

@admin_bypass
def can_delete_attachment(user: User, attachment: Attachment) -> None:
    raise NotImplementedError