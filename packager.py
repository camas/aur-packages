#!/usr/bin/env python3

import argparse
import sys
from typing import Iterable
import os
import shutil

from clicolor.cli import CLI

from scripts.packages import PackageManager, BUILD_PATH, DIST_PATH

LINE_WIDTH = 66  # Newspaper optimal
CLEAN_SAFE = ['.gitignore', 'README']


def main() -> None:
    # Print header
    tag = [
        f"Camas' AUR Packager",
        "Builds, tests and deploys pacman packages",
        "https://github.com/camas/aur-packages/",
    ]
    print()
    for i, line in enumerate(tag):
        if i == 0:
            print(f"{CLI.BOLD}{line.center(LINE_WIDTH, ' ')}{CLI.RESET}")
            continue
        print(line.center(LINE_WIDTH, ' '))
    print()

    # Set up parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        title="Commands", dest='command', metavar='command')
    # List command
    LIST_COMMAND = 'list'
    subparsers.add_parser(LIST_COMMAND, help="list packages")
    # Build command
    BUILD_COMMAND = 'build'
    b_parser = subparsers.add_parser(BUILD_COMMAND, help="build package(s)")
    b_parser.add_argument('--all', action='store_true', dest='build_all',
                          help="build all packages")
    b_parser.add_argument("build_names", metavar='package', nargs='*',
                          help="packages to build")
    # Clean command
    CLEAN_COMMAND = 'clean'
    subparsers.add_parser(CLEAN_COMMAND,
                          help="clean build artifacts and the like")

    # Print help if no args
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    # Run parser
    args = parser.parse_args()

    # Send args to relevant command
    commands = {
        LIST_COMMAND: list_packages,
        BUILD_COMMAND: build,
        CLEAN_COMMAND: clean,
    }
    commands[args.command](parser, args)


def list_packages(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    packages = PackageManager.get_packages()
    print_max = 50
    print(f"{CLI.BOLD}{len(packages)} packages:{CLI.RESET}")
    for package in packages[:print_max]:
        print((f"  {package._path:<32} "
               f"{package.get_version()}-{package.get_release()}"))
    if len(packages) > print_max:
        print(f"  and {len(packages) - print_max} more...")


def build(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.build_all:
        to_build = PackageManager.get_packages()
    elif args.build_names:
        to_build = []
        for name in args.build_names:
            package = PackageManager.get_package(name)
            to_build.append(package)

    print(f"{CLI.BOLD}Building {len(to_build)} packages:{CLI.RESET}")
    # Format and print package names
    package_list = _wrap_join_list([p.get_name() for p in to_build], padding=2)
    print(package_list)
    print()

    # Clear build folder
    print("Clearing build folder... ", end='')
    try:
        _clean_folder(BUILD_PATH)
    except Exception as e:
        print("Error: ", e)
        raise e
    print("Done")

    for i, package in enumerate(to_build, 1):
        print(f"Building {i}/{len(to_build)} {package.get_name()}")
        package.build()


def clean(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    try:
        print("Clearing build folder... ", end='')
        _clean_folder(BUILD_PATH)
        print("Done")
        print("Clearing dist folder... ", end='')
        _clean_folder(DIST_PATH)
        print("Done")
    except Exception as e:
        print("Error: ", e)
        raise e


def _clean_folder(path: str) -> None:
    for item in os.scandir(path):
        if item.is_file():
            if item.name in CLEAN_SAFE:
                continue
            os.unlink(item)
        elif item.is_dir():
            shutil.rmtree(item)


def _wrap_join_list(
    items: Iterable[str],
    padding: int = 0,
    max_width: int = LINE_WIDTH
) -> str:
    # Sort into groups of correct length
    # Items too long will go on a line by themselves
    item_groups = []
    cur_group = [items[0]]
    cur_len = len(items[0]) + padding
    for item in items[1:]:
        item_len = len(item)
        new_len = cur_len + item_len + 1
        if new_len > max_width:
            item_groups.append(cur_group)
            cur_group = [item]
            cur_len = item_len + padding
        else:
            cur_group.append(item)
            cur_len = new_len

    # Final append if not empty
    if cur_group:
        item_groups.append(cur_group)

    # Format into string and return
    return "\n".join(
        ((' ' * padding) + ' '.join(group) for group in item_groups)
    )


if __name__ == '__main__':
    main()
