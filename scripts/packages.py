from typing import List, Tuple
import os
import re
import shutil
import subprocess
import glob
import json

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
    def build_path(self) -> str:
        return os.path.join(BUILD_PATH, self._path)

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

    def prepare(self, ci: bool = False) -> None:
        # Clear build directory
        try:
            shutil.rmtree(self.build_path)
        except FileNotFoundError:
            pass

        # Copy files to build directory
        print(f"Copying files to {self.build_path}")
        shutil.copytree(self.package_path, self.build_path)

        # Create .SRCINFO
        print(f"Creating .SRCINFO")
        self.__exec("makepkg --printsrcinfo > .SRCINFO", self.build_path)

        # Parse .SRCINFO
        srcinfo = SRCINFO(os.path.join(self.build_path, '.SRCINFO'))

        # CI specific stuff
        if ci:
            # Uninstall all packages that were needed to run this script
            to_uninstall = ['git', 'python-clicolor', 'python-yaml',
                            'python-schema', 'python-aur', 'python-requests']
            self.__exec(f"yay -Rs --noconfirm {' '.join(to_uninstall)}")

        # Install dependencies
        deps = srcinfo._base.get('depends', [])
        make_deps = srcinfo._base.get('makedepends', [])
        check_deps = srcinfo._base.get('checkdepends', [])
        all_deps = deps + make_deps + check_deps
        if len(all_deps) > 0:
            print(f"Installing {len(all_deps)} dependencies")
            dep_str = '"' + '" "'.join(all_deps) + '"'
            self.__exec(f"yay -S --asdeps --noconfirm --needed {dep_str}")
        else:
            print("No dependencies to install")

    def build(self) -> None:
        # Build package
        print(f"Building package")
        self.__exec("makepkg --noconfirm --cleanbuild", self.build_path)

    def test(self, install: bool = True, ci: bool = False) -> None:
        # Assumes files exist in build dir then runs namcap and tries to
        # install the package

        # Find package files
        glob_str = os.path.join(self.build_path,
                                f"{self.name}*.pkg.*")
        results = [os.path.basename(r) for r in glob.glob(glob_str)]

        if len(results) != 1:
            raise Exception(f"Expected only 1 package. Found {len(results)}")

        # CI specific stuff
        if ci:
            # Install packages needed for testing
            needed = ['namcap', 'shellcheck']
            self.__exec(f"yay -S --noconfirm --needed {' '.join(needed)}")

        # Run namcap
        archive_args = ' '.join(results)
        proc = self.__exec(
            f"namcap {archive_args} PKGBUILD",
            self.build_path,
            capture=True)

        # Check namcap didn't warn or error
        output_raw = proc.stdout.decode()
        output = output_raw.splitlines()
        output = [o for o in output if
                  o not in self._settings.namcap_excluded_lines]
        if output:
            print('\n'.join(output))
            raise Exception("Namcap found issues")

        # Install package
        if install:
            cmd = f"yay -U --noconfirm --noprogressbar {results[0]}"
            self.__exec(cmd, self.build_path)

        # Shellcheck
        with open(self.pkgbuild_path, 'r') as f:
            pkgbuild_data = f.read()

        with open(os.path.join(SCRIPT_PATH, 'shellcheck_stub.sh'), 'r') as f:
            stub_data = f.read()

        final_data = stub_data + pkgbuild_data
        self.__exec('shellcheck -', stdin=final_data)

        # Get versions
        self.check_versions()

    def check_versions(self) -> None:
        print("Checking versions")

        def compare(a, b):
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

        # Get local version
        pkgver, pkgrel = self.get_srcinfo_version()
        print(f"Local version:    {pkgver}-{pkgrel}")

        # Check for upstream ver
        up_settings = self._settings.upstream
        if up_settings:
            up_type = up_settings['type']
            if up_type == 'pypi':
                upver = self.get_pypi_version()
            print(f"Upstream version: {upver}")
            cmp_res = compare(upver, pkgver)
            if cmp_res == 1:
                raise Exception("Upstream version is higher than package!")
            if cmp_res == -1:
                raise Exception("Package version is higher than upstream!")
        else:
            print(f"Upstream version: N/A")

        # Check AUR version
        aurver, aurrel = self.get_AUR_version()
        print(f"AUR version:      {aurver}-{aurrel}")
        cmp_res = compare(aurver + f".{aurrel}", pkgver + f".{pkgrel}")
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

    def get_pypi_version(self) -> str:
        resp = requests.get(f"https://pypi.org/pypi/{self.name}/json")
        info = json.loads(resp.text)
        return info['info']['version']

    def get_srcinfo_version(self) -> Tuple[str, int]:
        srcinfo = SRCINFO(os.path.join(self.build_path, '.SRCINFO'))
        pkgver = srcinfo._base.get('pkgver')
        pkgrel = srcinfo._base.get('pkgrel')
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
