#!/usr/bin/python3
from typing import Optional, List
import random
import string
import qrcode
import io

from flask import current_app, send_file

from .classes.class_utils import FakeObject
from .db import get_db

class InvalidRequest(Exception):
    def __init__(self, reason: str, code :int=400, redirect: Optional[str]=None):
        self.redirect = redirect
        self.reason = reason
        self.code = code
        super().__init__(reason)


def new_uuid():
    return ''.join([random.choice(string.ascii_uppercase + string.digits) for _ in range(6)])

def format_uuid(uuid):
    """Format old uuid4 format"""
    return uuid.upper()[:6]

def get_qrcode(location):
    complete_url = current_app.config["BASE_URL"] + location
    img_io = io.BytesIO()

    qrcode.make(complete_url).save(img_io)
    img_io.seek(0)
    return send_file(img_io, mimetype="image/jpeg")


from .classes.user import User
from .classes.album import Album
from .classes.groupe import Groupe
from .classes.partition import Partition
from .classes.attachment import Attachment
from .classes.album import create as create_album


def get_all_partitions() -> List[FakeObject]:
    db = get_db()
    partitions = db.execute(
        """
        SELECT p.*,
            (CASE WHEN MAX(a.uuid) IS NOT NULL THEN 1 ELSE 0 END) AS has_attachment
        FROM partition AS p
            JOIN contient_partition ON contient_partition.partition_uuid = p.uuid
            JOIN album ON album.id = album_id
            LEFT JOIN attachments AS a ON p.uuid = a.partition_uuid
        GROUP BY p.uuid, p.name, p.author, p.user_id
        """
    )
    return [FakeObject(p) for p in partitions]

def get_all_albums() -> List[FakeObject]:
    db = get_db()
    albums = db.execute(
        """
        SELECT * FROM album
        """
    )
    return [FakeObject(a) for a in albums]

def get_all_users() -> List[User]:
    db = get_db()
    users_id = db.execute(
        """
        SELECT id FROM user
        """
    )
    return [User(user_id=user["id"]) for user in users_id]

def user_count() -> int:
    db = get_db()
    count = db.execute(
        """
        SELECT COUNT(*) as count FROM user
        """
    ).fetchone()

    return count[0]


def partition_count() -> int:
    db = get_db()
    count = db.execute(
        """
        SELECT COUNT(*) FROM partition
        """
    ).fetchone()

    return count[0]