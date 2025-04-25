from typing import List
from flask import current_app
from werkzeug.security import generate_password_hash

from ..db import get_db
from .album import Album
from .groupe import Groupe
from .class_utils import FakeObject


# Variables defined in the CSS
colors = [
    "--color-rosewater",
    "--color-flamingo",
    "--color-pink",
    "--color-mauve",
    "--color-red",
    "--color-maroon",
    "--color-peach",
    "--color-yellow",
    "--color-green",
    "--color-teal",
    "--color-sky",
    "--color-sapphire",
    "--color-blue",
    "--color-lavender"
]


class User():
    def __init__(self, user_id=None, name=None):
        self.id = user_id
        self.username = name
        self.password = None
        self.albums = None
        self.accessible_albums = None
        self.groupes = None
        self.accessible_groupes = None
        self.partitions = None
        self.accessible_partitions = None
        self.max_queries = 0

        db = get_db()

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
        self.password = data["password"]
        self.access_level = data["access_level"]
        self.color = self.get_color()

        if self.is_admin:
            self.max_queries = 10
        else:
            self.max_queries = current_app.config["MAX_ONLINE_QUERIES"]

    @property
    def is_admin(self):
        return (self.access_level == 1)

    def is_participant(self, album_uuid, exclude_groupe=False) -> bool:
        db = get_db()

        return (len(db.execute( # Is participant directly in the album
                """
                SELECT album.id FROM album
                JOIN contient_user ON album_id = album.id
                JOIN user ON user_id = user.id
                WHERE user.id = ? AND album.uuid = ?
                """,
                (self.id, album_uuid)
            ).fetchall()) == 1 or
            # Is participant in a group that has this album
            ((not exclude_groupe) and (len(db.execute(
                """
                SELECT album.id FROM album
                JOIN groupe_contient_album
                JOIN groupe_contient_user
                JOIN user
                    ON user_id = user.id
                    AND groupe_contient_user.groupe_id = groupe_contient_album.groupe_id
                    AND album.id = album_id
                WHERE user.id = ? AND album.uuid = ?
                """,
                (self.id, album_uuid)
            ).fetchall()) >= 1))
            )


    def get_albums(self, force_reload=False):
        if self.albums is None or force_reload:
            db = get_db()
            if self.is_admin:
                # On récupère tous les albums qui ne sont pas dans un groupe
                self.albums = db.execute(
                    """
                    SELECT * FROM album
                    LEFT JOIN groupe_contient_album
                    ON album_id=album.id
                    WHERE album_id IS NULL
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

    
    def get_accessible_albums(self, force_reload=False):
        if self.accessible_albums is None or force_reload:
            db = get_db()
            if self.is_admin:
                # On récupère tous les albums qui ne sont pas dans un groupe
                self.accessible_albums = db.execute(
                    """
                    SELECT * FROM album
                    LEFT JOIN groupe_contient_album
                    ON album_id=album.id
                    WHERE album_id IS NULL
                    """
                ).fetchall()
            else:
                self.accessible_albums = db.execute(
                    """
                    SELECT album.* FROM album
                    LEFT JOIN groupe_contient_album AS gca ON gca.album_id=album.id
                    JOIN contient_user AS cu ON cu.album_id = album.id
                    JOIN user ON user_id = user.id
                    WHERE gca.album_id IS NULL
                    AND user.id = ?
                    """,
                    (self.id,),
                ).fetchall()
        return self.accessible_albums

    def get_groupes(self, force_reload=False):
        if self.groupes is None or force_reload:
            db = get_db()
            if self.is_admin:
                data = db.execute(
                    """
                    SELECT uuid FROM groupe
                    """
                ).fetchall()
            else:
                data = db.execute(
                    """
                    SELECT uuid FROM groupe
                    JOIN groupe_contient_user ON groupe.id = groupe_id
                    JOIN user ON user_id = user.id
                    WHERE user.id = ?
                    """,
                    (self.id,),
                ).fetchall()

            self.groupes = [Groupe(i["uuid"]) for i in data]

        return self.groupes

    
    def get_accessible_groupes(self, force_reload=False):
        """Returns groupes where user can add partitions"""
        if self.accessible_groupes is None or force_reload:
            db = get_db()
            if self.is_admin:
                data = db.execute(
                    """
                    SELECT groupe.* FROM groupe
                    """
                ).fetchall()
            else:
                data = db.execute(
                    """
                    SELECT groupe.* FROM groupe
                    JOIN groupe_contient_user ON groupe.id = groupe_id
                    JOIN user ON user_id = user.id
                    WHERE groupe_contient_user.is_admin = 1
                    AND user.id = ?
                    """,
                    (self.id,),
                ).fetchall()

            self.accessible_groupes = [Groupe(i["uuid"]) for i in data]

        return self.accessible_groupes


    def get_partitions(self, force_reload=False):
        if self.partitions is None or force_reload:
            db = get_db()
            if self.is_admin:
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

    def get_accessible_partitions(self, force_reload=False) -> List[FakeObject]:
        if self.accessible_partitions is None or force_reload:
            db = get_db()
            accessible_partitions = []
            if self.is_admin:
                accessible_partitions = db.execute(
                    """
                    SELECT * FROM partition
                    """
                ).fetchall()
            else:
                accessible_partitions = db.execute(
                    """
                    SELECT DISTINCT partition.uuid, partition.name,
                        partition.author, partition.body,
                        partition.user_id, partition.source
                    FROM partition
                        JOIN album
                        JOIN contient_partition
                        ON album.id=album_id
                        AND partition.uuid=partition_uuid
                    WHERE album.id IN (
                        SELECT album.id FROM album
                        JOIN contient_user
                        ON contient_user.user_id=?
                        AND album_id=album.id
                    UNION
                        SELECT DISTINCT album.id FROM album
                        JOIN groupe_contient_user
                        JOIN groupe_contient_album
                        ON groupe_contient_user.user_id=?
                        AND groupe_contient_album.album_id=album.id
                        AND groupe_contient_user.groupe_id=groupe_contient_album.groupe_id
                    )
                    """,
                    (self.id, self.id,),
                ).fetchall()
            self.accessible_partitions = [FakeObject(p) for p in accessible_partitions]
        return self.accessible_partitions

    def join_album(self, album_uuid=None, album_id=None) -> None:
        """
        Makes user join album. Provide preferably album_id
        """
        if album_id is None and album_uuid is None:
            raise ValueError("You should specify one of the parameters")

        db = get_db()
        if album_id is None:
            album = Album(uuid=album_uuid)
            album_id = album.id

        db.execute(
            """
            INSERT INTO contient_user (user_id, album_id)
            VALUES (?, ?)
            """,
            (self.id, album_id)
        )
        db.commit()

    def join_groupe(self, groupe_uuid=None, groupe_id=None):
        """
        Makes user join groupe. Provide preferably groupe_id
        """
        if groupe_id is None and groupe_uuid is None:
            raise ValueError("You should specify one of the parameters")

        db = get_db()
        if groupe_id is None:
            groupe = Groupe(uuid=groupe_uuid)
            groupe_id = groupe.id

        db.execute(
            """
            INSERT INTO groupe_contient_user (groupe_id, user_id)
            VALUES (?, ?)
            """,
            (groupe_id, self.id)
        )
        db.commit()

    def quit_album(self, album_uuid):
        db = get_db()

        db.execute(
            """
            DELETE FROM contient_user
            WHERE album_id IN (SELECT id FROM album WHERE uuid = ?)
            AND user_id = ?
            """,
            (album_uuid, self.id)
        )
        db.commit()

    def quit_groupe(self, groupe_uuid):
        db = get_db()
        groupe = Groupe(uuid=groupe_uuid)

        db.execute(
            """
            DELETE FROM groupe_contient_user
            WHERE user_id = ?
            AND groupe_id = ?
            """,
            (self.id, groupe.id)
        )
        db.commit()

    def update_password(self, new_password):
        db = get_db()

        db.execute(
            """
            UPDATE user SET password=?
            WHERE id=?
            """,
            (generate_password_hash(new_password), self.id)
        )

        db.commit()


    def delete(self):
        instance_path = current_app.config["INSTANCE_PATH"]
        for groupe in self.get_groupes():
            self.quit_groupe(groupe.uuid)

            if groupe.get_users() == []:
                groupe.delete(instance_path)


        for album_data in self.get_albums():
            uuid = album_data["uuid"]
            self.quit_album(uuid)

            album = Album(uuid=uuid)
            if album.get_users() == []:
                album.delete(instance_path)

        db = get_db()

        db.execute(
            """
            DELETE FROM user
            WHERE id=?
            """,
            (self.id,)
        )

        db.commit()


    def get_color(self):
        if len(colors) == 0:
            integer = hash(self.username) % 16777215
            return "#" + str(hex(integer))[2:]
        return f"var({colors[hash(self.username) %len(colors)]})"

    def __eq__(self, other):
        if isinstance(other, User): #TODO: take FakeObjects into account
            return self.id == other.id
        return NotImplemented

    def __repr__(self):
        return f"<User '{self.username}'>"