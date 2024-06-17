import os
import shutil
import sqlite3
from colorama import Fore, Style

from . import utils
from . import config

"""
 v1.3.*
"""


def add_source():
    utils.run_sqlite_command("ALTER TABLE partition ADD source TEXT DEFAULT 'unknown'")


def add_groupes():
    utils.run_sqlite_command(
        """CREATE TABLE groupe (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            uuid TEXT(36) NOT NULL
        );"""
    )
    utils.run_sqlite_command(
        """CREATE TABLE groupe_contient_user (
            groupe_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (groupe_id, user_id)
        );"""
    )
    utils.run_sqlite_command(
        """CREATE TABLE groupe_contient_album (
            groupe_id INTEGER NOT NULL,
            album_id INTEGER NOT NULL,
            PRIMARY KEY (groupe_id, album_id)
        );"""
    )


def add_attachments():
    os.makedirs("partitioncloud/attachments", exist_ok=True)
    utils.run_sqlite_command(
        """CREATE TABLE attachments (
                uuid TEXT(36) PRIMARY KEY,
                name TEXT NOT NULL,
                filetype TEXT NOT NULL DEFAULT 'mp3',
                partition_uuid INTEGER NOT NULL,
                user_id INTEGER NOT NULL
            );"""
    )


def install_colorama():
    utils.install_package("colorama")


"""
 v1.4.*
"""


def mass_rename():
    """Rename all albums & groupes to use a shorter uuid"""
    albums = utils.get_sqlite_data("SELECT * FROM album")
    groupes = utils.get_sqlite_data("SELECT * FROM groupe")

    utils.run_sqlite_command("ALTER TABLE groupe RENAME TO _groupe_old")
    utils.run_sqlite_command("ALTER TABLE album RENAME TO _album_old")

    utils.run_sqlite_command(  # Add UNIQUE constraint & change uuid length
        """CREATE TABLE groupe (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            uuid TEXT(6) UNIQUE NOT NULL
        );"""
    )

    utils.run_sqlite_command(  # Change uuid length
        """CREATE TABLE album (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            uuid TEXT(6) UNIQUE NOT NULL
        );"""
    )

    for album in albums:
        try:
            utils.run_sqlite_command(
                """
                INSERT INTO album (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (album[0], album[1], utils.format_uuid(album[2])),
            )
        except sqlite3.IntegrityError:
            uuid = utils.new_uuid()
            print(
                f"{Fore.RED}Collision on {album[1]}{Style.RESET_ALL} \
                    ({album[2][:10]} renaming to {uuid})"
            )
            utils.run_sqlite_command(
                """
                INSERT INTO album (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (album[0], album[1], uuid),
            )

    for groupe in groupes:
        try:
            utils.run_sqlite_command(
                """
                INSERT INTO groupe (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (groupe[0], groupe[1], utils.format_uuid(groupe[2])),
            )
        except sqlite3.IntegrityError:
            uuid = utils.new_uuid()
            print(
                f"{Fore.RED}Collision on {groupe[1]}{Style.RESET_ALL} \
                    ({groupe[2][:10]} renaming to {uuid})"
            )
            utils.run_sqlite_command(
                """
                INSERT INTO groupe (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (groupe[0], groupe[1], uuid),
            )

    utils.run_sqlite_command("DROP TABLE _groupe_old")
    utils.run_sqlite_command("DROP TABLE _album_old")


def base_url_parameter_added():
    print(
        f"{Style.BRIGHT}{Fore.YELLOW}The parameter BASE_URL has been added, \
            reference your front url in it{Style.RESET_ALL}"
    )


def install_qrcode():
    utils.install_package("qrcode")


"""
 v1.5.*
"""


def move_instance():
    paths = [
        "attachments",
        "partitions",
        "search-partitions"
    ]
    for path in paths:
        shutil.move(
            os.path.join("partitioncloud", path),
            os.path.join(config.instance, path)
        )


def move_thumbnails():
    shutil.rmtree("partitioncloud/static/thumbnails", ignore_errors=True)
    shutil.rmtree("partitioncloud/static/search-thumbnails", ignore_errors=True)

    os.makedirs(os.path.join(config.instance, "cache", "thumbnails"), exist_ok=True)
    os.makedirs(os.path.join(config.instance, "cache", "search-thumbnails"), exist_ok=True)


"""
 v1.7.*
"""


def install_babel():
    utils.install_package("flask-babel")


"""
 v1.8.*
"""

def install_pypdf():
    utils.install_package("pypdf")

"""
 v1.10.*
"""

def install_unidecode():
    utils.install_package("unidecode")