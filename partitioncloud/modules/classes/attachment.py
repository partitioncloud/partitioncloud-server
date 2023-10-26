import os

from flask import current_app

from ..db import get_db


class Attachment():
    def __init__(self, uuid=None, data=None):
        db = get_db()
        if uuid is not None:
            self.uuid = uuid
            data = db.execute(
                """
                SELECT * FROM attachments
                WHERE uuid = ?
                """,
                (self.uuid,)
            ).fetchone()
            if data is None:
                raise LookupError

        elif data is not None:
            self.uuid = data["uuid"]

        else:
            raise LookupError

        self.name = data["name"]
        self.user_id = data["user_id"]
        self.filetype = data["filetype"]
        self.partition_uuid = data["partition_uuid"]

    def delete(self):
        db = get_db()
        db.execute(
            """
            DELETE FROM attachments
            WHERE uuid = ?
            """,
            (self.uuid,)
        )
        db.commit()
        
        os.remove(f"partitioncloud/attachments/{self.uuid}.{self.filetype}")

    def __repr__(self):
        return f"{self.name}.{self.filetype}"