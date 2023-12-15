import random
import string
import sqlite3


def run_sqlite_command(*args):
    """Run a command against the database"""
    con = sqlite3.connect("instance/partitioncloud.sqlite")
    cur = con.cursor()
    cur.execute(*args)
    con.commit()
    con.close()


def get_sqlite_data(*args):
    """Get data from the db"""
    con = sqlite3.connect("instance/partitioncloud.sqlite")
    cur = con.cursor()
    data = cur.execute(*args)
    new_data = list(data)
    con.close()
    return new_data


def new_uuid():
    return "".join(
        [random.choice(string.ascii_uppercase + string.digits) for _ in range(6)]
    )


def format_uuid(uuid):
    """Format old uuid4 format"""
    return uuid.upper()[:6]
