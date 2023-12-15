#!/usr/bin/python3
import io
import random
import string
import qrcode

from flask import current_app, send_file
from .db import get_db


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


def get_all_partitions():
    db = get_db()
    partitions = db.execute(
        """
        SELECT p.uuid, p.name, p.author, p.body, p.user_id,
            CASE WHEN MAX(a.uuid) IS NOT NULL THEN 1 ELSE 0 END AS has_attachment
        FROM partition AS p
            JOIN contient_partition ON contient_partition.partition_uuid = p.uuid
            JOIN album ON album.id = album_id
            LEFT JOIN attachments AS a ON p.uuid = a.partition_uuid
        GROUP BY p.uuid, p.name, p.author, p.user_id
        """
    )
    # Transform sql object to dictionary usable in any thread
    return [
        {
            "uuid": p["uuid"],
            "name": p["name"],
            "author": p["author"],
            "body": p["body"],
            "user_id": p["user_id"],
            "has_attachment": p["has_attachment"]
        } for p in partitions
    ]

def get_all_albums():
    db = get_db()
    albums = db.execute(
        """
        SELECT * FROM album
        """
    )
    # Transform sql object to dictionary usable in any thread
    return [
        {
            "id": a["id"],
            "name": a["name"],
            "uuid": a["uuid"]
        } for a in albums
    ]
