from typing import List, Dict
import os
import re
import shutil
import subprocess

PACKAGES_PATH = 'packages'
BUILD_PATH = 'build'
DIST_PATH = 'dist'
# https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#Definitions
NAME_PATTERN = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
PKGBUILD_PATTERN = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)=([^\n]+)')

CONFIG_HEADER_PATTERN = re.compile(r'^([a-z]*):$')
CONFIG_VALUE_PATTERN = re.compile(r'^\t|    (.*)$')


class Package:

    def __init__(self, path: str) -> None:
        self._path = path
        self._pkgbuild = {}

        self.__read_pkgbuild()
        self.__check_pkgbuild_vars()

    def prepare(self) -> None:
        # Clear build directory
        try:
            shutil.rmtree(self.get_build_path())
        except FileNotFoundError:
            pass

        # Copy files to build directory
        print(f"Copying files to {self.get_build_path()}")
        shutil.copytree(self.get_package_path(), self.get_build_path())

        # Create .SRCINFO
        print(f"Creating .SRCINFO")
        self.__exec_shell(
            "makepkg --printsrcinfo > .SRCINFO",
            self.get_build_path())

        # Install dependencies
        # TODO

    def build(self) -> None:
        # Build package
        print(f"Building package")
        self.__exec(
            "makepkg --noconfirm --cleanbuild".split(' '),
            self.get_build_path())

    def test(self) -> None:
        # Assumes files exist in build dir

        # Read project namcap settings
        namcap_settings = self.__read_namcap_settings()
        # Run namcap
        pass

    def __read_namcap_settings(self) -> Dict[str, object]:
        # Default
        settings = {
            'exclude': [],
        }
        path = os.path.join(self.get_package_path(), '.namcap')

        if not os.path.exists(path):
            return settings

        # Read lines
        with open(path, 'r') as f:
            lines = f.read().splitlines()

        # Parse
        cur_setting = None
        for i, line in enumerate(lines, 1):
            # Ignore blank lines and comments
            if not line.strip() or line.strip()[0] == '#':
                continue
            # Try match header
            header_match = CONFIG_HEADER_PATTERN.match(line)
            if header_match:
                cur_setting = header_match.group(1)
                continue
            # Try match value
            value_match = CONFIG_VALUE_PATTERN.match(line)
            if value_match:
                settings[cur_setting].append(value_match.group(1))
                continue

            raise Exception(f"Error reading .namcap file at line {i}")

        return settings

    def __exec(self, cmd: List[str], directory: str) -> None:
        cmd_str = '" "'.join(cmd)
        print(f"{directory}$ \"{cmd_str}\"")
        proc = subprocess.run(cmd, cwd=directory)
        if proc.returncode != 0:
            raise Exception()

    def __exec_shell(self, cmd: str, directory: str) -> None:
        print(f"{directory}$ {cmd}")
        proc = subprocess.run(cmd, shell=True, cwd=directory)
        if proc.returncode != 0:
            raise Exception()

    def __read_pkgbuild(self) -> None:
        # Doesn't read multiline arguments properly
        with open(self.get_pkgbuild_path(), 'r') as f:
            for line in f.read().splitlines():
                result = PKGBUILD_PATTERN.match(line)
                if result:
                    name = result.group(1)
                    value = result.group(2)
                    self._pkgbuild[name] = value

    def __check_pkgbuild_vars(self) -> None:
        # Check names
        for name in self._pkgbuild.keys():
            if not NAME_PATTERN.match(name):
                raise Exception(f"{name} is not a valid variable name")

    def get_package_path(self) -> str:
        return os.path.join(PACKAGES_PATH, self._path)

    def get_build_path(self) -> str:
        return os.path.join(BUILD_PATH, self._path)

    def get_pkgbuild_path(self) -> str:
        return os.path.join(self.get_package_path(), 'PKGBUILD')

    def get_name(self) -> str:
        return self._path

    def get_version(self) -> str:
        return self._pkgbuild['pkgver']

    def get_release(self) -> str:
        return self._pkgbuild['pkgrel']


class PackageManager:

    @staticmethod
    def get_packages() -> List[Package]:
        packages = []
        for path in os.listdir(PACKAGES_PATH):
            package = Package(path)
            packages.append(package)
        return packages

    @staticmethod
    def get_package(name: str) -> Package:
        return Package(name)
