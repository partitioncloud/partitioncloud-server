import os

from ..db import get_db
from .user import User
from .attachment import Attachment



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
            self.source = data["source"]
            self.attachments = None
        else:
            raise LookupError

    def delete(self, instance_path):
        db = get_db()
        db.execute(
            """
            DELETE FROM contient_partition
            WHERE partition_uuid = ?
            """,
            (self.uuid,)
        )
        db.commit()

        os.remove(f"{instance_path}/partitions/{self.uuid}.pdf")
        if os.path.exists(f"{instance_path}/cache/thumbnails/{self.uuid}.jpg"):
            os.remove(f"{instance_path}/cache/thumbnails/{self.uuid}.jpg")

        db.execute(
            """
            DELETE FROM partition
            WHERE uuid = ?
            """,
            (self.uuid,)
        )
        db.commit()

        for attachment in self.get_attachments():
            attachment.delete(instance_path)

    def update(self, name=None, author="", body=""):
        if name is None:
            raise ValueError("name cannot be None")

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

    def update_file(self, file, instance_path):
        partition_path = os.path.join(
            instance_path,
            "partitions",
            f"{self.uuid}.pdf"
        )
        file.save(partition_path)
        if os.path.exists(f"{instance_path}/cache/thumbnails/{self.uuid}.jpg"):
            os.remove(f"{instance_path}/cache/thumbnails/{self.uuid}.jpg")

        db = get_db()
        db.execute(
            """
            UPDATE partition
            SET source = 'upload'
            WHERE uuid = ?
            """,
            (self.uuid,)
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

    def get_attachments(self):
        db = get_db()
        if self.attachments is None:
            data = db.execute(
                """
                SELECT * FROM attachments
                WHERE partition_uuid = ?
                """,
                (self.uuid,)
            )
            self.attachments = [Attachment(data=i) for i in data]

        return self.attachments
