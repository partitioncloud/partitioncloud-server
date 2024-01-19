from datetime import datetime
from typing import Union
from enum import Enum

global log_file
global enabled


class LogEntry(Enum):
    LOGIN = 1
    NEW_GROUPE = 2
    NEW_ALBUM = 3
    NEW_PARTITION = 4
    NEW_USER = 5
    SERVER_RESTART = 6
    FAILED_LOGIN = 7

    def from_string(entry: str):
        mapping = {
            "LOGIN": LogEntry.LOGIN,
            "NEW_GROUPE": LogEntry.NEW_GROUPE,
            "NEW_ALBUM": LogEntry.NEW_ALBUM,
            "NEW_PARTITION": LogEntry.NEW_PARTITION,
            "NEW_USER": LogEntry.NEW_USER,
            "SERVER_RESTART": LogEntry.SERVER_RESTART,
            "FAILED_LOGIN": LogEntry.FAILED_LOGIN
        }
        # Will return KeyError if not available
        return mapping[entry]


def add_entry(entry: str) -> None:
    date = datetime.now().strftime("%y-%b-%Y %H:%M:%S")

    with open(log_file, 'a', encoding="utf8") as f:
        f.write(f"[{date}] {entry}\n")


def log(content: list[Union[str, bool, int]], log_type: LogEntry) -> None:
    description: str = ""

    if log_type not in enabled:
        return

    match log_type:
        case LogEntry.LOGIN: # content = (user.name)
            description = f"Successful login for {content[0]}"

        case LogEntry.NEW_GROUPE: # content = (groupe.name, groupe.id, user.name)
            description = f"{content[2]} added groupe '{content[0]}' ({content[1]})"

        case LogEntry.NEW_ALBUM: # content = (album.name, album.id, user.name)
            description = f"{content[2]} added album '{content[0]}' ({content[1]})"

        case LogEntry.NEW_PARTITION: # content = (partition.name, partition.uuid, user.name)
            description = f"{content[2]} added partition '{content[0]}' ({content[1]})"

        case LogEntry.NEW_USER: # content = (user.name, user.id, from_register_page, admin.name if relevant)
            if not content[2]:
                description = f"New user {content[0]}[{content[1]}]"
            else:
                description = f"New user {content[0]}[{content[1]}] added by {content[3]}"
                
        case LogEntry.SERVER_RESTART: # content = ()
            description = "Server just restarted"

        case LogEntry.FAILED_LOGIN: # content = (user.name)
            description = f"Failed login for {content[0]}"

    add_entry(description)


log_file = "logs.txt"
enabled = [i for i in LogEntry]