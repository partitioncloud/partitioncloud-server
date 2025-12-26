import os
import sys
import random
import string
import sqlite3
from colorama import Fore, Style

from . import config


def run_sqlite_command(*args):
    """Run a command against the database"""
    con = sqlite3.connect(os.path.join(
        config.instance,
        "partitioncloud.sqlite"
    ))
    cur = con.cursor()
    cur.execute(*args)
    con.commit()
    con.close()


def get_sqlite_data(*args):
    """Get data from the db"""
    con = sqlite3.connect(os.path.join(
        config.instance,
        "partitioncloud.sqlite"
    ))
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


def install_package(package):
    print(f"\nThe following python package needs to be installed: {Style.BRIGHT}{Fore.YELLOW}{package}{Style.RESET_ALL}")
    print(f"1. Install with {Style.BRIGHT}pip{Style.RESET_ALL} (automatic)")
    print(f"2. Install manually (other package manager)")
    option = input("Select an option: ")
    try:
        choice = int(option)

        if choice == 1:
            return_value = os.system(f"pip install {package} -qq")
            if return_value == 0:
                return
            print(f"{Fore.RED}Installation with pip failed{Style.RESET_ALL}")
            sys.exit(return_value)

        elif choice == 2:
            input("Install via you preferred option, and hit [Enter] when done")
            return

    except ValueError:
        pass

    print(f"{Fore.RED}Please enter a valid option{Style.RESET_ALL}")
    return install_package(package)


def uninstall_package(package):
    print(f"\nThe following python package can be uninstalled: {Style.BRIGHT}{Fore.YELLOW}{package}{Style.RESET_ALL}")
    print(f"1. Uninstall with {Style.BRIGHT}pip{Style.RESET_ALL} (automatic)")
    print(f"2. Do nothing, I will do it later")
    option = input("Select an option: ")
    try:
        choice = int(option)

        if choice == 1:
            return_value = os.system(f"pip uninstall {package} -qqy")
            if return_value == 0:
                return
            print(f"{Fore.RED}Uninstallation with pip failed{Style.RESET_ALL}")
            sys.exit(return_value)

        elif choice == 2:
            return

    except ValueError:
        pass

    print(f"{Fore.RED}Please enter a valid option{Style.RESET_ALL}")
    return uninstall_package(package)