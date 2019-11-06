#!/usr/bin/env python3

import argparse
import sys
from typing import Iterable, List
import os
import shutil
import subprocess

from clicolor.cli import CLI

from scripts.packages import PackageManager, BUILD_PATH, DIST_PATH

LINE_WIDTH = 66  # Newspaper optimal
CLEAN_SAFE = ['.gitignore', 'README']


def main() -> None:
    # Don't show traceback
    sys.tracebacklimit = 0

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
    # Header command
    HEADER_COMMAND = 'header'
    subparsers.add_parser(HEADER_COMMAND, help="show header")
    # Prepare command
    PREP_COMMAND = 'prepare'
    p_parser = subparsers.add_parser(PREP_COMMAND, help="prepare package(s)")
    p_parser.add_argument('--all', action='store_true', dest='prep_all',
                          help="prepare all packages")
    p_parser.add_argument("prep_names", metavar='package', nargs='*',
                          help="packages to prepare")
    # Test command
    TEST_COMMAND = 'test'
    t_parser = subparsers.add_parser(TEST_COMMAND, help="test package(s)")
    t_parser.add_argument('--all', action='store_true', dest='test_all',
                          help="test all packages")
    t_parser.add_argument('--no-install', action='store_true',
                          dest='test_no_install',
                          help="Don't install when testing")
    t_parser.add_argument("test_names", metavar='package', nargs='*',
                          help="packages to test")

    # Full command
    FULL_COMMAND = 'full'
    t_parser = subparsers.add_parser(FULL_COMMAND,
                                     help="run all tasks on package(s)")
    t_parser.add_argument('--all', action='store_true', dest='full_all',
                          help="use all packages")
    t_parser.add_argument('--ci', action='store_true', dest='full_ci',
                          help="CI specific option")
    t_parser.add_argument("full_names", metavar='package', nargs='*',
                          help="packages to use")

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
        HEADER_COMMAND: header,
        PREP_COMMAND: prepare,
        TEST_COMMAND: test,
        FULL_COMMAND: full,
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
               f"{package.version}-{package.release}"))
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
    else:
        parser.error("Need package input")

    print(f"{CLI.BOLD}Building {len(to_build)} packages:{CLI.RESET}")
    # Format and print package names
    package_list = _wrap_join_list([p.name for p in to_build], padding=2)
    print(package_list)
    print()
    for i, package in enumerate(to_build, 1):
        print(f"Building {i}/{len(to_build)} {package.name}")
        package.build()


def prepare(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.prep_all:
        to_prep = PackageManager.get_packages()
    elif args.prep_names:
        to_prep = []
        for name in args.prep_names:
            package = PackageManager.get_package(name)
            to_prep.append(package)
    else:
        parser.error("Need package input")

    print(f"{CLI.BOLD}Preparing {len(to_prep)} packages:{CLI.RESET}")
    # Format and print package names
    package_list = _wrap_join_list([p.name for p in to_prep], padding=2)
    print(package_list)
    print()
    for i, package in enumerate(to_prep, 1):
        print(f"Preparing {i}/{len(to_prep)} {package.name}")
        package.prepare()


def test(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.test_all:
        to_test = PackageManager.get_packages()
    elif args.test_names:
        to_test = []
        for name in args.test_names:
            package = PackageManager.get_package(name)
            to_test.append(package)
    else:
        parser.error("Need package input")

    print(f"{CLI.BOLD}Testing {len(to_test)} packages:{CLI.RESET}")
    # Format and print package names
    package_list = _wrap_join_list([p.name for p in to_test], padding=2)
    print(package_list)
    print()
    for i, package in enumerate(to_test, 1):
        print(f"Testing {i}/{len(to_test)} {package.name}")
        package.test(install=not args.test_no_install)


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


def full(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if args.full_all:
        to_do = PackageManager.get_packages()
    elif args.full_names:
        to_do = []
        for name in args.full_names:
            package = PackageManager.get_package(name)
            to_do.append(package)
    else:
        parser.error("Need package input")

    print((f"{CLI.BOLD}Running full process on {len(to_do)} packages:"
           f"{CLI.RESET}"))
    # Format and print package names
    package_list = _wrap_join_list([p.name for p in to_do], padding=2)
    print(package_list)
    print()
    for i, package in enumerate(to_do, 1):
        print((f"{CLI.BOLD}Preparing {i}/{len(to_do)} {package.name}"
               f"{CLI.RESET}"))
        package.prepare(ci=True)
        print((f"{CLI.BOLD}Building {i}/{len(to_do)} {package.name}"
               f"{CLI.RESET}"))
        package.build()
        print((f"{CLI.BOLD}Testing {i}/{len(to_do)} {package.name}"
               f"{CLI.RESET}"))
        package.test(ci=True)


def header(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    tag = [
        f"Camas' AUR Packager",
        "",
        "Builds, tests and deploys pacman packages",
        "https://github.com/camas/aur-packages/",
        "",
    ]
    git_branch = _exec_output("git rev-parse --abbrev-ref HEAD".split(' '))[0]
    git_hash = _exec_output("git rev-list -n 1 HEAD".split(' '))[0][:8]
    git_commits = _exec_output("git rev-list --count HEAD".split(' '))[0]
    tag.append(f"{git_branch} | {git_hash} | {git_commits} commits")

    print()
    for i, line in enumerate(tag):
        if i == 0:
            print(f"{CLI.BOLD}{line.center(LINE_WIDTH, ' ')}{CLI.RESET}")
            continue
        print(line.center(LINE_WIDTH, ' '))
    print()

    package_names = [p.name for p in PackageManager.get_packages()]
    package_list = _wrap_join_list(package_names).splitlines()
    for line in package_list:
        print(line.center(LINE_WIDTH, ' '))
    print()


def _exec_output(cmd: List[str]) -> List[str]:
    result = subprocess.run(cmd, capture_output=True, check=True)
    lines = result.stdout.decode().splitlines()
    return [l.rstrip() for l in lines]


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
