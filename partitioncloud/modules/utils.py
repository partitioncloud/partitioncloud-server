#!/usr/bin/python3
import os
from .db import get_db

from flask import current_app

class User():
    def __init__(self, user_id=None, name=None):
        self.id = user_id
        self.username = name
        self.albums = None
        self.partitions = None
        self.max_queries = 0

        db = get_db()
        if self.id is None and self.username is None:
            self.username = ""
            self.access_level = -1
        
        else:
            if self.id is not None:
                data = db.execute(
                    """
                    SELECT * FROM user
                    WHERE id = ?
                    """,
                    (self.id,)
                ).fetchone()
            elif self.username is not None:
                data = db.execute(
                    """
                    SELECT * FROM user
                    WHERE username = ?
                    """,
                    (self.username,)
                ).fetchone()
            
            self.id = data["id"]
            self.username = data["username"]
            self.access_level = data["access_level"]
            self.color = self.get_color()
            if self.access_level == 1:
                self.max_queries = 10
            else:
                self.max_queries = current_app.config["MAX_ONLINE_QUERIES"]


    def is_participant(self, album_uuid):
        db = get_db()
        
        return len(db.execute(
                """
                SELECT album.id FROM album
                JOIN contient_user ON album_id = album.id
                JOIN user ON user_id = user.id
                WHERE user.id = ? AND album.uuid = ?
                """,
                (self.id, album_uuid)
            ).fetchall()) == 1


    def get_albums(self, force_reload=False):
        if self.albums is None or force_reload:
            db = get_db()
            if self.access_level == 1:
                self.albums = db.execute(
                    """
                    SELECT * FROM album
                    """
                ).fetchall()
            else:
                self.albums = db.execute(
                    """
                    SELECT album.id, name, uuid FROM album
                    JOIN contient_user ON album_id = album.id
                    JOIN user ON user_id = user.id
                    WHERE user.id = ?
                    """,
                    (self.id,),
                ).fetchall()
        return self.albums


    def get_partitions(self, force_reload=False):
        if self.partitions is None or force_reload:
            db = get_db()
            if self.access_level == 1:
                self.partitions = db.execute(
                    """
                    SELECT * FROM partition
                    """
                ).fetchall()
            else:
                self.partitions = db.execute(
                    """
                    SELECT * FROM partition
                    JOIN user ON user_id = user.id
                    WHERE user.id = ?
                    """,
                    (self.id,),
                ).fetchall()
        return self.partitions
        
    def join_album(self, album_uuid):
        db = get_db()
        album = Album(uuid=album_uuid)

        db.execute(
            """
            INSERT INTO contient_user (user_id, album_id)
            VALUES (?, ?)
            """,
            (self.id, album.id)
        )
        db.commit()

    def quit_album(self, album_uuid):
        db = get_db()
        album = Album(uuid=album_uuid)

        db.execute(
            """
            DELETE FROM contient_user
            WHERE user_id = ?
            AND album_id = ?
            """,
            (self.id, album.id)
        )
        db.commit()


    def get_color(self):
        integer = hash(self.username) % 16777215
        return "#" + str(hex(integer))[2:]



class Album():
    def __init__(self, uuid=None, id=None):
        db = get_db()
        if uuid is not None:
            self.uuid = uuid
            data = db.execute(
                """
                SELECT id, name FROM album
                WHERE uuid = ?
                """,
                (self.uuid,)
            ).fetchone()
            if data is None:
                raise LookupError
            self.id = data["id"]
            self.name = data["name"]

        elif id is not None:
            self.id = id
            data = db.execute(
                """
                SELECT uuid, name FROM album
                WHERE id = ?
                """,
                (self.id,)
            ).fetchone()
            if data is None:
                raise LookupError
            self.uuid = data["uuid"]
            self.name = data["name"]

        else:
            raise LookupError
        
        self.users = None


    def get_users(self):
        """
        Renvoie les utilisateurs liés à l'album
        """
        db = get_db()
        return db.execute(
            """
            SELECT * FROM user
            JOIN contient_user ON user_id = user.id
            JOIN album ON album.id = album_id
            WHERE album.uuid = ?
            """,
            (self.uuid,)
        ).fetchall()

    def get_partitions(self):
        """
        Renvoie les partitions liées à l'album
        """
        db = get_db()
        return db.execute(
            """
            SELECT partition.uuid, partition.name, partition.author, partition.user_id FROM partition
            JOIN contient_partition ON partition_uuid = partition.uuid
            JOIN album ON album.id = album_id
            WHERE album.uuid = ?
            """,
            (self.uuid,),
        ).fetchall()


    def delete(self):
        """
        Supprimer l'album
        """
        db = get_db()
        db.execute(
            """
            DELETE FROM album
            WHERE uuid = ?
            """,
            (self.uuid,)
        )
        db.execute(
            """
            DELETE FROM contient_user
            WHERE album_id = ?
            """,
            (self.id,)
        )
        db.execute(
            """
            DELETE FROM contient_partition
            WHERE album_id = ?
            """,
            (self.id,)
        )
        db.commit()
        # Delete orphan partitions
        partitions = db.execute(
            """
            SELECT partition.uuid FROM partition
            WHERE NOT EXISTS (
                SELECT NULL FROM contient_partition 
                WHERE partition.uuid = partition_uuid
            )
            """
        )
        for partition in partitions.fetchall():
            os.remove(f"partitioncloud/partitions/{partition['uuid']}.pdf")
            if os.path.exists(f"partitioncloud/static/thumbnails/{partition['uuid']}.jpg"):
                os.remove(f"partitioncloud/static/thumbnails/{partition['uuid']}.jpg")
        
        partitions = db.execute(
            """
            DELETE FROM partition
            WHERE uuid IN (
                SELECT partition.uuid FROM partition
                WHERE NOT EXISTS (
                    SELECT NULL FROM contient_partition 
                    WHERE partition.uuid = partition_uuid
                )
            )
            """
        )
        db.commit()


    def add_partition(self, partition_uuid):
        """
        Ajoute une partition à l'album à partir de son uuid
        """
        db = get_db()
        db.execute(
            """
            INSERT INTO contient_partition (partition_uuid, album_id)
            VALUES (?, ?)
            """,
            (partition_uuid, self.id),
        )
        db.commit()


class Partition():
    def __init__(self, uuid=None):
        db = get_db()
        if uuid is not None:
            self.uuid = uuid
            data = db.execute(
                """
                SELECT * FROM partition
                WHERE uuid = ?
                """,
                (self.uuid,)
            ).fetchone()
            if data is None:
                raise LookupError
            self.name = data["name"]
            self.author = data["author"]
            self.body = data["body"]
            self.user_id = data["user_id"]
        else:
            raise LookupError

    def delete(self):
        db = get_db()
        db.execute(
            """
            DELETE FROM contient_partition
            WHERE partition_uuid = ?
            """,
            (self.uuid,)
        )
        db.commit()
        
        os.remove(f"partitioncloud/partitions/{self.uuid}.pdf")
        if os.path.exists(f"partitioncloud/static/thumbnails/{self.uuid}.jpg"):
            os.remove(f"partitioncloud/static/thumbnails/{self.uuid}.jpg")

        partitions = db.execute(
            """
            DELETE FROM partition
            WHERE uuid = ?
            """,
            (self.uuid,)
        )
        db.commit()

    def update(self, name=None, author="", body=""):
        if name is None:
            return Exception("name cannot be None")

        db = get_db()
        db.execute(
            """
            UPDATE partition
            SET name = ?,
                author = ?,
                body = ?
            WHERE uuid = ?
            """,
            (name, author, body, self.uuid)
        )
        db.commit()

    def get_user(self):
        db = get_db()
        user = db.execute(
            """
            SELECT * FROM user
            JOIN partition ON user_id = user.id
            WHERE partition.uuid = ?
            """,
            (self.uuid,),
        ).fetchone()

        if user is None:
            raise LookupError

        return User(user_id=user["id"])

    def get_albums(self):
        db = get_db()
        return db.execute(
            """
            SELECT * FROM album
            JOIN contient_partition ON album.id = album_id
            WHERE partition_uuid = ?
            """,
            (self.uuid,),
        ).fetchall()



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