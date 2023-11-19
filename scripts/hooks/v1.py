import os
import sqlite3
from hooks import utils
from colorama import Fore, Style

"""
 v1.3.*
"""
def add_source():
    utils.run_sqlite_command(
        "ALTER TABLE partition ADD source TEXT DEFAULT 'unknown'"
    )

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
    os.system("pip install colorama -qq")


"""
 v1.4.*
"""
def mass_rename():
    """Rename all albums & groupes to use a shorter uuid"""
    albums = utils.get_sqlite_data("SELECT * FROM album")
    groupes = utils.get_sqlite_data("SELECT * FROM groupe")

    utils.run_sqlite_command(
        "ALTER TABLE groupe RENAME TO _groupe_old"
    )
    utils.run_sqlite_command(
        "ALTER TABLE album RENAME TO _album_old"
    )

    utils.run_sqlite_command( # Add UNIQUE constraint & change uuid length
        """CREATE TABLE groupe (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            uuid TEXT(6) UNIQUE NOT NULL
        );"""
    )

    utils.run_sqlite_command( # Change uuid length
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
                (album[0], album[1], utils.format_uuid(album[2]))
            )
        except sqlite3.IntegrityError:
            uuid = new_uuid()
            print(f"{Fore.RED}Collision on {album[1]}{Style.RESET_ALL} ({album[2][:10]} renaming to {uuid})")
            utils.run_sqlite_command(
                """
                INSERT INTO album (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (album[0], album[1], uuid)
            )
    
    for groupe in groupes:
        try:
            utils.run_sqlite_command(
                """
                INSERT INTO groupe (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (groupe[0], groupe[1], utils.format_uuid(groupe[2]))
            )
        except sqlite3.IntegrityError:
            uuid = new_uuid()
            print(f"{Fore.RED}Collision on {groupe[1]}{Style.RESET_ALL} ({groupe[2][:10]} renaming to {uuid})")
            utils.run_sqlite_command(
                """
                INSERT INTO groupe (id, name, uuid)
                VALUES (?, ?, ?)
                """,
                (groupe[0], groupe[1], uuid)
            )

    utils.run_sqlite_command(
        "DROP TABLE _groupe_old"
    )
    utils.run_sqlite_command(
        "DROP TABLE _album_old"
    )

def base_url_parameter_added():
    print(f"{Style.BRIGHT}{Fore.YELLOW}The parameter BASE_URL has been added, reference your front url in it{Style.RESET_ALL}")