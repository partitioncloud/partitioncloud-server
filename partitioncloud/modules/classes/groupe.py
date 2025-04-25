"""
Classe Groupe
"""
import io
import os
import zipfile
from typing import List

from werkzeug.utils import secure_filename

from ..db import get_db
from .album import Album
from .class_utils import FakeObject, RealObject as Robj

class Groupe():
    def __init__(self, uuid):
        db=get_db()

        self.uuid = uuid
        data = db.execute(
            """
            SELECT * FROM groupe
            WHERE uuid = ?
            """,
            (self.uuid,)
        ).fetchone()
        if data is None:
            raise LookupError
        self.name = data["name"]
        self.id = data["id"]
        self.users = None
        self.albums = None
        self.admins = None

    def delete(self, instance_path) -> None:
        """
        Supprime le groupe, et les albums laissés orphelins (sans utilisateur)
        """
        db = get_db()
        db.execute(
            """
            DELETE FROM groupe
            WHERE id = ?
            """,
            (self.id,)
        )
        db.execute(
            """
            DELETE FROM groupe_contient_user
            WHERE groupe_id = ?
            """,
            (self.id,)
        )
        db.execute(
            """
            DELETE FROM groupe_contient_album
            WHERE groupe_id = ?
            """,
            (self.id,)
        )
        db.commit()

        # Supprime tous les albums laissés orphelins (maintenant ou plus tôt)
        data = db.execute(
            """
            SELECT id FROM album
            LEFT JOIN groupe_contient_album
                ON groupe_contient_album.album_id=album.id
            LEFT JOIN contient_user
                ON contient_user.album_id=album.id
            WHERE user_id IS NULL AND groupe_id IS NULL
            """
        ).fetchall()

        for i in data:
            album = Album(id=i["id"])
            album.delete(instance_path)


    def get_users(self, force_reload=False) -> List[FakeObject]:
        """
        Renvoie les utilisateurs liés au groupe
        """
        if self.users is None or force_reload:
            db = get_db()
            data = db.execute(
                """
                SELECT user.* FROM user
                JOIN groupe_contient_user ON user_id = user.id
                JOIN groupe ON groupe.id = groupe_id
                WHERE groupe.id = ?
                """,
                (self.id,)
            ).fetchall()
            self.users = [FakeObject(i, Robj.USER) for i in data]
        return self.users

    def get_albums(self, force_reload=False) -> List[Album]:
        """
        Renvoie les uuids des albums liés au groupe
        """
        if self.albums is None or force_reload:
            db = get_db()
            data = db.execute(
                """
                SELECT album.* FROM album
                JOIN groupe_contient_album ON album_id = album.id
                JOIN groupe ON groupe.id = groupe_id
                WHERE groupe.id = ?
                """,
                (self.id,)
            ).fetchall()
            self.albums = [FakeObject(i, Robj.ALBUM) for i in data]

        return self.albums

    def get_admins(self) -> List[FakeObject]:
        """
        Renvoie les utilisateurs administrateurs liés au groupe
        """
        db = get_db()
        data = db.execute(
            """
            SELECT user.* FROM user
            JOIN groupe_contient_user ON user_id = user.id
            JOIN groupe ON groupe.id = groupe_id
            WHERE is_admin=1 AND groupe.id = ?
            """,
            (self.id,)
        ).fetchall()
        return [FakeObject(i, Robj.USER) for i in data]

    def set_admin(self, user_id, value) -> None:
        """
        Rend un utilisateur administrateur du groupe
        """
        db = get_db()
        data = db.execute(
            """
            UPDATE groupe_contient_user
            SET is_admin=?
            WHERE user_id=? AND groupe_id=?
            """,
            (value, user_id, self.id)
        )
        db.commit()

    def to_zip(self, instance_path) -> io.BytesIO:
        data = io.BytesIO()
        with zipfile.ZipFile(data, mode="w") as z:
            for album in self.get_albums():
                for partition in album.get_partitions():
                    z.write(os.path.join(
                        instance_path,
                        "partitions",
                        f"{partition.uuid}.pdf"
                    ), arcname=secure_filename(album.name)+"/"
                        +secure_filename(partition.name+".pdf")
                    )

        # Spooling back to the beginning of the buffer
        data.seek(0)

        return data

    def __repr__(self):
        return f"<Groupe '{self.name}'>"