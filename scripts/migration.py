#!/usr/bin/python3
import os
import shutil
import argparse
from functools import cmp_to_key
from distutils.dir_util import copy_tree

from colorama import Fore, Style
from hooks import v1


def get_version(v: str) -> (int, int, int):
    """Returns a tuple (major, minor, patch from the string v{major}.{minor}.{patch})"""
    assert (v[0] == 'v') # Check if the version is correctly formatted
    return tuple(map(int, v[1:].split('.')))


def is_newer(v1: str, v2: str) -> bool:
    """Returns True if v1 > v2"""
    return get_version(v1) > get_version(v2)


hooks = [
    ("v1.3.0", [
        ("add SOURCE column", v1.add_source)
    ]),
    ("v1.2.0", [
        ("create groupe structure", v1.add_groupes)
    ]),
    ("v1.3.0", [
        ("create attachment table", v1.add_attachments)
    ]),
    ("v1.3.3", [
        ("Install colorama", v1.install_colorama)
    ]),
    ("v1.4.0", [
        ("Change all albums & groupes uuids", v1.mass_rename),
        ("Warn new parameter", v1.base_url_parameter_added)
    ])
]


def get_hooks(current, target):
    """Returns a list of hooks needed to migrate"""
    def compare(v1: str, v2: str):
        if is_newer(v2[0], v1[0]):
            return -1
        elif is_newer(v1[0], v2[0]):
            return 1
        else:
            return 0

    applied_hooks = []
    for hook in hooks:
        if is_newer(hook[0], current) and (target == hook[0] or is_newer(target, hook[0])):
            applied_hooks.append(hook)

    return sorted(applied_hooks, key=cmp_to_key(compare))


def backup_instance(version, verbose=True):
    """Backs up current instance in backups/{version}"""
    def print_verbose(*args):
        if verbose:
            print(*args)

    print_verbose("\nBacking up current instance")
    dest = os.path.join("backups", version)

    if os.path.exists(dest):
        print(f"{Fore.RED}Backup directory already exists{Style.RESET_ALL}")
        exit(1)

    os.makedirs(dest)
    paths = [
        ("instance", os.path.join(dest, "instance")),
        (os.path.join("partitioncloud", "partitions"), os.path.join(dest, "partitions")),
        (os.path.join("partitioncloud", "attachments"), os.path.join(dest, "attachments")),
        (os.path.join("partitioncloud", "search-partitions"), os.path.join(dest, "search-partitions"))
    ]
    for src, dst in paths:
        if os.path.exists(src):
            print_verbose(f"\tBacking up {src}")
            copy_tree(src, dst)


def print_hooks(hooks):
    for hook in hooks:
        print(f"- {Fore.BLUE}{hook[0]}{Style.RESET_ALL}:")
        for subhook in hook[1]:
            print("\t", subhook[0])


def apply_hooks(hooks):
    for hook in hooks:
        print(f"Migrating to {Fore.BLUE}{hook[0]}{Style.RESET_ALL}:")
        for subhook in hook[1]:
            print(f"\tApplying '{subhook[0]}'")
            subhook[1]()


def migrate(current, target, skip_backup=False, prog_name="scripts/migration.py"):
    """"""
    print(f"Trying to migrate from {args.current} to {args.target}")

    assert is_newer(args.target, args.current)

    applied_hooks = get_hooks(args.current, args.target)
    if (len(applied_hooks) == 0):
        print(f"{Fore.GREEN}No hook to apply{Style.RESET_ALL}")
        exit(0)

    print("The following hooks will be applied:")
    print_hooks(applied_hooks)

    if input("Apply these hooks ? [y/N] ") != "y":
        print(f"{Fore.RED}Aborting !{Style.RESET_ALL}")
        exit(1)

    if not skip_backup:
        backup_instance(current)
        print(f"Instance backed up in {Style.BRIGHT}backups/{current}{Style.RESET_ALL}\n")
        print(f"If something goes wrong, recover with {Style.BRIGHT}{Fore.BLUE}{prog_name} --restore {current}{Style.RESET_ALL}")
    else:
        print("Skipping automatic backup")

    apply_hooks(applied_hooks)
    print("Done !")


def restore(version):
    if input("Do you really want to restore from backup ? Your current data will be deleted [y/N] ") != "y":
        print(f"{Fore.RED}Aborting !{Style.RESET_ALL}")
        exit(1)

    dest = os.path.join("backups", version)
    print(f"Restoring from {dest}")
    paths = [
        ("instance", os.path.join(dest, "instance")),
        (os.path.join("partitioncloud", "partitions"), os.path.join(dest, "partitions")),
        (os.path.join("partitioncloud", "attachments"), os.path.join(dest, "attachments")),
        (os.path.join("partitioncloud", "search-partitions"), os.path.join(dest, "search-partitions"))
    ]
    for src, dst in paths:
        if os.path.exists(src):
            shutil.rmtree(src)

        if os.path.exists(dst):
            print(f"\tRestoring {src}")
            copy_tree(dst, src)
        else:
            print(f"\t{Fore.RED}No available backup for {src}, deleting current content to avoid any conflict{Style.RESET_ALL}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                        prog='PartitionCloud Migration tool',
                        description='Helps you migrate from one version to another')

    parser.add_argument('-c', '--current', help="current version (vx.y.z)")
    parser.add_argument('-t', '--target', help="target version (vx.y.z)")
    parser.add_argument('-s', '--skip-backup', action='store_true')
    parser.add_argument('-r', '--restore', help='restore from specific version backup, will not apply any hook (vx.y.z)')

    args = parser.parse_args()
    
    if args.restore is None:
        migrate(args.current, args.target, skip_backup=args.skip_backup)
    else:
        restore(args.restore)