#!/usr/bin/python3
import os

from .db import get_db

from .classes.user import User
from .classes.album import Album
from .classes.groupe import Groupe
from .classes.partition import Partition


def get_all_partitions():
    db = get_db()
    partitions = db.execute(
        """
        SELECT * FROM partition
        """
    )
    # Transform sql object to dictionary usable in any thread
    return [
        {
            "uuid": p["uuid"],
            "name": p["name"],
            "author": p["author"],
            "body": p["body"],
            "user_id": p["user_id"]
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