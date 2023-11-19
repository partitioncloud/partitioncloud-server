import sqlite3

def run_sqlite_command(cmd):
    """Run a command against the database"""
    con = sqlite3.connect("instance/partitioncloud.sqlite")
    cur = con.cursor()
    cur.execute(cmd)
    con.commit()
    con.close()