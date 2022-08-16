#!/usr/bin/python3
import os
from .db import get_db

class User():
    def __init__(self, user_id):
        self.id = user_id

        db = get_db()
        if self.id is None:
            self.username = ""
            self.access_level = -1
        
        else:
            data = db.execute(
                """
                SELECT username, access_level FROM user
                WHERE id = ?
                """,
                (self.id,)
            ).fetchone()
            self.username = data["username"]
            self.access_level = data["access_level"]


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


    def get_albums(self):
        db = get_db()
        if self.access_level == 1:
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
                (self.id,),
            ).fetchall()

        
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
            SELECT partition.uuid, partition.name, partition.author FROM partition
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