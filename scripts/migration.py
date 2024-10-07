#!/usr/bin/python3
import os
import sys
import shutil
import argparse
from functools import cmp_to_key

from colorama import Fore, Style
from hooks import v1 as v1_hooks, config


def get_version(v: str) -> (int, int, int):
    """Returns a tuple (major, minor, patch from the string v{major}.{minor}.{patch})"""
    assert v[0] == "v"  # Check if the version is correctly formatted
    return tuple(map(int, v[1:].split(".")))


def is_newer(v1: str, v2: str) -> bool:
    """Returns True if v1 > v2"""
    return get_version(v1) > get_version(v2)


hooks = [
    ("v1.3.0", [("add SOURCE column", v1_hooks.add_source)]),
    ("v1.2.0", [("create groupe structure", v1_hooks.add_groupes)]),
    ("v1.3.0", [("create attachment table", v1_hooks.add_attachments)]),
    ("v1.3.3", [("Install colorama", v1_hooks.install_colorama)]),
    (
        "v1.4.0",
        [
            ("Change all albums & groupes uuids", v1_hooks.mass_rename),
            ("Warn new parameter", v1_hooks.base_url_parameter_added),
        ],
    ),
    ("v1.4.1", [("Install qrcode", v1_hooks.install_qrcode)]),
    ("v1.5.0", [("Move to instance directory", v1_hooks.move_instance)]),
    ("v1.5.1", [("Move thumbnails", v1_hooks.move_thumbnails)]),
    ("v1.7.0", [("Install babel", v1_hooks.install_babel)]),
    ("v1.8.2", [("Install pypdf", v1_hooks.install_pypdf)]),
    ("v1.10.3", [("Install unidecode", v1_hooks.install_unidecode)]),
]


def get_hooks(current, target):
    """Returns a list of hooks needed to migrate"""

    def compare(v1: str, v2: str):
        if is_newer(v2[0], v1[0]):
            return -1
        if is_newer(v1[0], v2[0]):
            return 1
        return 0

    applied_hooks = []
    for hook in hooks:
        if is_newer(hook[0], current) and (
            target == hook[0] or is_newer(target, hook[0])
        ):
            applied_hooks.append(hook)

    return sorted(applied_hooks, key=cmp_to_key(compare))


def backup_instance(version, verbose=True):
    """Backs up current instance in backups/{version}"""

    def print_verbose(*f_args):
        if verbose:
            print(*f_args)

    print_verbose("\nBacking up current instance")
    dest = os.path.join("backups", version)

    if os.path.exists(dest):
        print(f"{Fore.RED}Backup directory already exists{Style.RESET_ALL}")
        sys.exit(1)

    os.makedirs(dest)
    paths = [
        (config.instance, os.path.join(dest, "instance")),
        (
            os.path.join("partitioncloud", "partitions"),
            os.path.join(dest, "partitions"),
        ),
        (
            os.path.join("partitioncloud", "attachments"),
            os.path.join(dest, "attachments"),
        ),
        (
            os.path.join("partitioncloud", "search-partitions"),
            os.path.join(dest, "search-partitions"),
        ),
    ]
    for src, dst in paths: # Only the first one exists after v1.5.0
        if os.path.exists(src):
            print_verbose(f"\tBacking up {src}")
            shutil.copytree(src, dst)


def print_hooks(hooks_list):
    for hook in hooks_list:
        print(f"- {Fore.BLUE}{hook[0]}{Style.RESET_ALL}:")
        for sub_hook in hook[1]:
            print("\t", sub_hook[0])


def apply_hooks(hooks_list):
    for hook in hooks_list:
        print(f"Migrating to {Fore.BLUE}{hook[0]}{Style.RESET_ALL}:")
        for sub_hook in hook[1]:
            print(f"\tApplying '{sub_hook[0]}'")
            sub_hook[1]()


def migrate(current, target, skip_backup=False, prog_name="scripts/migration.py"):
    """Migrate from one version to another"""
    print(f"Trying to migrate from {current} to {target}")

    assert is_newer(target, current)

    applied_hooks = get_hooks(current, target)
    if len(applied_hooks) == 0:
        print(f"{Fore.GREEN}No hook to apply{Style.RESET_ALL}")
        sys.exit(0)

    print("The following hooks will be applied:")
    print_hooks(applied_hooks)

    if input("Apply these hooks ? [y/N] ") != "y":
        print(f"{Fore.RED}Aborting !{Style.RESET_ALL}")
        sys.exit(1)

    if not skip_backup:
        backup_instance(current)
        print(
            f"Instance backed up in {Style.BRIGHT}backups/{current}{Style.RESET_ALL}\n"
        )
        print(
            f"If something goes wrong, recover with {Style.BRIGHT}{Fore.BLUE}{prog_name}\
 --restore {current}{Style.RESET_ALL}"
        )
    else:
        print("Skipping automatic backup")

    apply_hooks(applied_hooks)
    print("Done !")


def restore(version):
    if (
        input(
            "Do you really want to restore from backup ? Your current data will be deleted [y/N] "
        )
        != "y"
    ):
        print(f"{Fore.RED}Aborting !{Style.RESET_ALL}")
        sys.exit(1)

    dest = os.path.join("backups", version)
    print(f"Restoring from {dest}")
    paths = [
        (config.instance, os.path.join(dest, "instance")),
        (
            os.path.join("partitioncloud", "partitions"),
            os.path.join(dest, "partitions"),
        ),
        (
            os.path.join("partitioncloud", "attachments"),
            os.path.join(dest, "attachments"),
        ),
        (
            os.path.join("partitioncloud", "search-partitions"),
            os.path.join(dest, "search-partitions"),
        ),
    ]
    for src, dst in paths: # Only the first one exists after v1.5.0
        if os.path.exists(src):
            shutil.rmtree(src)

        if os.path.exists(dst):
            print(f"\tRestoring {src}")
            shutil.copytree(dst, src)
        else:
            print(
                f"\t{Fore.RED}No available backup for {src}, \
                deleting current content to avoid any conflict{Style.RESET_ALL}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="PartitionCloud Migration tool",
        description="Helps you migrate from one version to another",
    )

    parser.add_argument("-c", "--current", help="current version (vx.y.z)")
    parser.add_argument("-t", "--target", help="target version (vx.y.z)")
    parser.add_argument("-i", "--instance", help="instance folder", default="instance")
    parser.add_argument("-s", "--skip-backup", action="store_true")
    parser.add_argument(
        "-r",
        "--restore",
        help="restore from specific version backup, will not apply any hook (vx.y.z)",
    )
    parser.add_argument(
        "-b",
        "--backup",
        help="backup current version, without running any hooks",
    )

    args = parser.parse_args()
    config.instance = os.path.abspath(args.instance)

    if args.restore is not None:
        restore(args.restore)
    elif args.backup is not None:
        backup_instance(args.backup, verbose=True)
    else:
        migrate(args.current, args.target, skip_backup=args.skip_backup)
