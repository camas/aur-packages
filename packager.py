#!/usr/bin/env python3

import argparse
import sys
from typing import Iterable, List
import os
import subprocess
from pathlib import Path

from clicolor.cli import CLI

from scripts.packages import PackageManager

LINE_WIDTH = 66  # Newspaper optimal
CLEAN_SAFE = ['.gitignore', 'README']
DOCKER_TAG = 'camas/aur-packages'


class Packager:

    def main(self) -> None:
        # Don't show traceback
        sys.tracebacklimit = 0

        # Set up parser
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(
            title="Commands", dest='command', metavar='command')

        # List command
        LIST_COMMAND = 'list'
        subparsers.add_parser(LIST_COMMAND, help="list packages")

        # Header command
        HEADER_COMMAND = 'header'
        subparsers.add_parser(HEADER_COMMAND, help="show header")

        # Test command
        TEST_COMMAND = 'test'
        t_parser = subparsers.add_parser(TEST_COMMAND, help="test package(s)")
        t_parser.add_argument('--all', action='store_true', dest='test_all',
                              help="test all packages")
        t_parser.add_argument('--shell', action='store_true', dest='shell',
                              help="test all packages")
        t_parser.add_argument("test_names", metavar='package', nargs='*',
                              help="packages to test")

        # Dist command
        DIST_COMMAND = 'dist'
        d_parser = subparsers.add_parser(DIST_COMMAND,
                                         help="distribute the package")
        d_parser.add_argument("name", metavar='package', help="package to use")

        # Image command
        IMAGE_COMMAND = 'image'
        im_parser = subparsers.add_parser(IMAGE_COMMAND,
                                          help="Image functions")
        im_commands = im_parser.add_subparsers(
            title="Commands",
            dest='im_command',
            metavar='command')
        im_commands.add_parser('build', help='Build the docker image')
        im_commands.add_parser(
            'fullbuild', help='Fully build the docker image')

        # Print help if no args
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)

        # Run parser
        args = parser.parse_args()

        # Run relevant command
        self._parser = parser
        self._args = args
        if args.command == IMAGE_COMMAND:
            commands = {
                'build': self.build_image,
                'fullbuild': self.build_image_full,
            }
            commands[args.im_command]()
        else:
            commands = {
                HEADER_COMMAND: self.header,
                LIST_COMMAND: self.list_packages,
                TEST_COMMAND: self.test,
                DIST_COMMAND: self.distribute,
            }
            commands[args.command]()

    def header(self) -> None:
        tag = [
            f"Camas' AUR Packager",
            "",
            "Builds, tests and deploys pacman packages",
            "https://github.com/camas/aur-packages/",
            "",
        ]
        git_branch = _exec_output(
            "git rev-parse --abbrev-ref HEAD".split(' '))[0]
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

    def list_packages(self) -> None:
        packages = PackageManager.get_packages()
        print_max = 50
        print(f"{CLI.BOLD}{len(packages)} packages:{CLI.RESET}")
        for package in packages[:print_max]:
            print((f"  {package._path:<32} "
                   f"{package.version}-{package.release}"))
        if len(packages) > print_max:
            print(f"  and {len(packages) - print_max} more...")

    def distribute(self) -> None:
        package = PackageManager.get_package(self._args.name)
        print(f"{CLI.BOLD}Distributing  {package.name}{CLI.RESET}")
        package.distribute()

    def test(self) -> None:
        if self._args.test_all:
            to_test = PackageManager.get_packages()
        elif self._args.test_names:
            to_test = []
            for name in self._args.test_names:
                package = PackageManager.get_package(name)
                to_test.append(package)
        else:
            self._parser.error("Need package input")

        self.build_image()

        print(f"{CLI.BOLD}Testing {len(to_test)} packages:{CLI.RESET}")
        # Format and print package names
        package_list = _wrap_join_list([p.name for p in to_test], padding=2)
        print(package_list)
        print()
        for i, package in enumerate(to_test, 1):
            print((f"{CLI.BOLD}Testing {i}/{len(to_test)} {package.name}"
                   f"{CLI.RESET}"))
            package.test(self._args.shell)
        print(f"{CLI.BOLD}Packages tested successfully{CLI.RESET}")

    def build_image(self) -> None:
        print(f"{CLI.BOLD}Building docker image{CLI.RESET}")
        self._build_image()
        print(f"{CLI.BOLD}Finished building docker image{CLI.RESET}")

    def build_image_full(self) -> None:
        print(f"{CLI.BOLD}Fully building docker image{CLI.RESET}")
        self._build_image(False)
        print(f"{CLI.BOLD}Finished building docker image{CLI.RESET}")

    def _build_image(self, use_cache: bool = True):
        # Generate docker options
        docker_options = [
            '-f',
            str(Path('image/Dockerfile')),
            '--tag',
            DOCKER_TAG,
            '--cache-from',
            'camas/aur-packages',
        ]
        # Set country docker image will use use to generate it's mirrorlist
        if 'MIRRORLIST_COUNTRY' in os.environ:
            docker_options.extend([
                '--build-arg',
                f'MIRRORLIST_COUNTRY={os.environ.get("MIRRORLIST_COUNTRY")}',
            ])
        else:
            print(f"MIRRORLIST_COUNTRY not set. Using default")
        # Cache option
        if not use_cache:
            docker_options.append('--no-cache')

        # Create final command
        docker_cmd = [
            'sudo',
            'docker',
            'build',
            *docker_options,
            '.',
        ]

        # Build image
        subprocess.run(docker_cmd, check=True)


def _exec_output(cmd: List[str]) -> List[str]:
    result = subprocess.run(cmd, capture_output=True, check=True)
    lines = result.stdout.decode().splitlines()
    return [l.rstrip() for l in lines]


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
    packager = Packager()
    packager.main()
