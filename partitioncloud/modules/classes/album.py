"""
Classe Album
"""
import os

from ..db import get_db
from ..utils import new_uuid

from .attachment import Attachment

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


    def get_users(self, force_reload=False):
        """
        Renvoie les utilisateurs liés à l'album
        """
        if self.users is None or force_reload:
            db = get_db()
            self.users = db.execute(
                """
                SELECT * FROM user
                JOIN contient_user ON user_id = user.id
                JOIN album ON album.id = album_id
                WHERE album.uuid = ?
                """,
                (self.uuid,)
            ).fetchall()
        return self.users

    def get_partitions(self):
        """
        Renvoie les partitions liées à l'album
        """
        db = get_db()
        return db.execute(
            """
            SELECT p.uuid, p.name, p.author, p.user_id,
                CASE WHEN MAX(a.uuid) IS NOT NULL THEN 1 ELSE 0 END AS has_attachment
            FROM partition AS p
                JOIN contient_partition ON contient_partition.partition_uuid = p.uuid
                JOIN album ON album.id = album_id
                LEFT JOIN attachments AS a ON p.uuid = a.partition_uuid
            WHERE album.uuid = ?
            GROUP BY p.uuid, p.name, p.author, p.user_id
            """,
            (self.uuid,),
        ).fetchall()


    def delete(self, instance_path):
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
            data = db.execute(
                """
                SELECT * FROM attachments
                WHERE partition_uuid = ?
                """,
                (partition["uuid"],)
            )
            attachments = [Attachment(data=i) for i in data]

            for attachment in attachments:
                attachment.delete(instance_path)

            os.remove(f"{instance_path}/partitions/{partition['uuid']}.pdf")
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


def create(name: str) -> str:
    """Créer un nouvel album"""
    db = get_db()
    while True:
        try:
            uuid = new_uuid()

            db.execute(
                """
                INSERT INTO album (uuid, name)
                VALUES (?, ?)
                """,
                (uuid, name),
            )
            db.commit()

            break
        except db.IntegrityError:
            pass

    return uuid
