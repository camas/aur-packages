from typing import List, Tuple
import os
import re
import shutil
import subprocess
import glob

import requests
import aur

from scripts.srcinfo import SRCINFO
from scripts.settings import Settings

PACKAGES_PATH = 'packages'
BUILD_PATH = 'build'
DIST_PATH = 'dist'
SCRIPT_PATH = 'scripts'
# https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#Definitions
NAME_PATTERN = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
PKGBUILD_PATTERN = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)=([^\n]+)')

CONFIG_HEADER_PATTERN = re.compile(r'^([a-z_]*):$')
CONFIG_VALUE_PATTERN = re.compile(r'^\t|    (.*)$')


class Package:

    @property
    def settings_path(self) -> str:
        return os.path.join(self.package_path, '.settings.yaml')

    @property
    def package_path(self) -> str:
        return os.path.join(PACKAGES_PATH, self._path)

    @property
    def dist_path(self) -> str:
        return os.path.join(DIST_PATH, self._path)

    @property
    def pkgbuild_path(self) -> str:
        return os.path.join(self.package_path, 'PKGBUILD')

    @property
    def name(self) -> str:
        return self._path

    @property
    def version(self) -> str:
        return self._pkgbuild['pkgver']

    @property
    def release(self) -> str:
        return self._pkgbuild['pkgrel']

    def __init__(self, path: str) -> None:
        self._path = path
        self._pkgbuild = {}

        self._settings = Settings(self.settings_path)

        self.__read_pkgbuild()
        self.__check_pkgbuild_vars()

    def distribute(self) -> None:
        # Clear distribution directory
        try:
            shutil.rmtree(self.dist_path)
        except FileNotFoundError:
            pass
        os.mkdir(self.dist_path)

        # Clone repo
        self.__exec(f'git clone ssh://aur@aur.archlinux.org/{self.name}.git',
                    self.dist_path)

        repo_path = os.path.join(self.dist_path, self.name)
        git_dir = os.path.abspath(os.path.join(repo_path, '.git'))
        git_dir_opt = f'GIT_DIR="{git_dir}"'

        # Copy
        for file in glob.glob(f'{self.package_path}/**/*', recursive=True):
            rel_name = file[len(self.package_path) + 1:]
            dest = f"{repo_path}/{rel_name}"
            shutil.copy(file, dest)
            self.__exec(f'{git_dir_opt} git add {rel_name}', repo_path)

        # Generate .srcinfo
        self.__exec("makepkg --printsrcinfo > .SRCINFO", repo_path)
        self.__exec(f'{git_dir_opt} git add .SRCINFO', repo_path)

        # Check version is newer
        aurver, aurrel = self.get_AUR_version()
        ver, rel = self.get_srcinfo_version()
        print(f"Local version:    {ver}-{rel}")
        print(f"AUR version:      {aurver}-{aurrel}")
        if ver == aurver:
            if rel != aurrel + 1:
                raise Exception(f"rel {rel} isn't 1 higher than AUR {aurrel}")
        else:
            if rel != 1:
                raise Exception(f"Newer version but rel {rel} isn't 1")
            res = _compare(ver, aurver)
            if res != 1:
                raise Exception(f"Version {ver} isn't newer than AUR {aurver}")

        # Show diff
        self.__exec(f'{git_dir_opt} git diff --staged', repo_path)

        # Check if ok
        res = input('Commit message (or blank to abort): ').strip()
        if not res:
            print("Exiting...")
            return

        # Push changes
        self.__exec(f'{git_dir_opt} git commit -m "{res}"', repo_path)
        self.__exec(f'{git_dir_opt} git push', repo_path)

    def test(self) -> None:
        # Run test.sh in a docker container
        docker_cmd = [
            'sudo',
            'docker',
            'run',
            '--rm',
            'camas/aur-packages',
            '/packages/test.sh',
            self.name,
        ]
        subprocess.run(docker_cmd, check=True)

        # Check versions
        self.check_versions()

    def check_versions(self) -> None:
        print("Checking versions")

        # Get local version
        pkgver, pkgrel = self.get_srcinfo_version()
        print(f"Local version:    {pkgver}-{pkgrel}")

        # Check for upstream ver
        up_settings = self._settings.upstream
        if up_settings:
            up_type = up_settings['type']
            up_name = up_settings['name']
            if up_type == 'pypi':
                upver = self.get_pypi_version(up_name)
            elif up_type == 'github':
                url = f"https://api.github.com/repos/{up_name}/tags"
                resp = requests.get(url)
                data = resp.json()
                upver = data[0]['name']
            else:
                raise Exception(f"Unknown upstream type {up_type}")
            print(f"Upstream version: {upver}")
            cmp_res = _compare(upver, pkgver)
            if cmp_res == 1:
                raise Exception("Upstream version is higher than package!")
            if cmp_res == -1:
                raise Exception("Package version is higher than upstream!")
        else:
            print(f"Upstream version: N/A")

        # Check AUR version
        aurver, aurrel = self.get_AUR_version()
        print(f"AUR version:      {aurver}-{aurrel}")
        cmp_res = _compare(aurver + f".{aurrel}", pkgver + f".{pkgrel}")
        if cmp_res == 1:
            raise Exception("AUR version higher than local!")
        if cmp_res == -1:
            print("Package higher than AUR version")

    def get_AUR_version(self) -> Tuple[str, int]:
        # Query api and parse version string
        info = aur.info(self.name)
        ver_split = info.version.split('-')
        pkgver = ver_split[0]
        pkgrel = int(ver_split[1])

        return (pkgver, pkgrel)

    def get_pypi_version(self, name: str) -> str:
        resp = requests.get(f"https://pypi.org/pypi/{name}/json")
        info = resp.json()
        return info['info']['version']

    def get_srcinfo_version(self) -> Tuple[str, int]:
        cmd = f"./scripts/get_package_version.sh {self.name}"
        proc = self.__exec(cmd, self.package_path, True)
        data = proc.stdout.decode().splitlines()
        pkgver = data[0]
        pkgrel = int(data[1])
        return (pkgver, pkgrel)

    def __exec(self, cmd: str, directory: str = '.', capture: bool = False,
               stdin: str = None) -> subprocess.CompletedProcess:
        if stdin:
            stdin = stdin.encode()
        print(f"{directory}$ {cmd}")
        proc = subprocess.run(cmd, shell=True, cwd=directory,
                              capture_output=capture, input=stdin)
        if proc.returncode != 0:
            raise Exception(f"Returned error code {proc.returncode}")
        return proc

    def __read_pkgbuild(self) -> None:
        # Doesn't read multiline arguments properly
        with open(self.pkgbuild_path, 'r') as f:
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


class PackageManager:

    @staticmethod
    def get_packages() -> List[Package]:
        packages = []
        for path in os.listdir(PACKAGES_PATH):
            package = Package(path)
            packages.append(package)
        packages.sort(key=lambda x: x.name)
        return packages

    @staticmethod
    def get_package(name: str) -> Package:
        return Package(name)


def _compare(a, b):
    # Returns 1 if a > b, -1 if a < b, 0 if a == b
    # Handles any version strings with chars from 'a-z0-9\.'
    a = a.split('.')
    b = b.split('.')
    if len(a) != len(b):
        raise Exception(f"Versions {a} {b} are of different formats")

    for i in range(len(a)):
        a_part = int(a[i], base=36)
        b_part = int(b[i], base=36)

        if a_part > b_part:
            return 1
        elif b_part > a_part:
            return -1
        elif i == len(a) - 1:
            return 0
