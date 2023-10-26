#!/usr/bin/python3
import os

from .db import get_db

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