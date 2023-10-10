import os

from ..db import get_db



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
