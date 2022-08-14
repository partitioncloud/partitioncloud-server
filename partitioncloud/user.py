#!/usr/bin/python3
from .db import get_db


def access_level(user_id):
    db = get_db()
    if user_id is None:
        return -1
    return db.execute(
        """
        SELECT access_level FROM user
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()["access_level"]


def is_participant(user_id, uuid):
    db = get_db()
    return len(db.execute(
            """
            SELECT album.id FROM album
            JOIN contient_user ON album_id = album.id
            JOIN user ON user_id = user.id
            WHERE user.id = ? AND album.uuid = ?
            """,
            (user_id, uuid)
        ).fetchall()) == 1


def get_albums(user_id):
    db = get_db()
    if access_level(user_id) == 1:
        return db.execute(
            """
            SELECT * FROM album
            """
        ).fetchall()
    return db.execute(
            """
            SELECT album.id, name, uuid FROM album
            JOIN contient_user ON album_id = album.id
            JOIN user ON user_id = user.id
            WHERE user.id = ?
            """,
            (user_id,),
        ).fetchall()


def get_users(album_uuid):
    db = get_db()
    return db.execute(
        """
        SELECT * FROM user
        JOIN contient_user ON user_id = user.id
        JOIN album ON album.id = album_id
        WHERE album.uuid = ?
        """,
        (album_uuid,)
    ).fetchall()