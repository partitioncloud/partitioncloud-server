import os
from hooks import utils

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