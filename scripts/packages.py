from typing import List, Dict
import os
import re
import shutil
import subprocess
import glob

from scripts.srcinfo import SRCINFO

PACKAGES_PATH = 'packages'
BUILD_PATH = 'build'
DIST_PATH = 'dist'
# https://www.gnu.org/savannah-checkouts/gnu/bash/manual/bash.html#Definitions
NAME_PATTERN = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')
PKGBUILD_PATTERN = re.compile(r'^([a-zA-Z_][a-zA-Z0-9_]*)=([^\n]+)')

CONFIG_HEADER_PATTERN = re.compile(r'^([a-z_]*):$')
CONFIG_VALUE_PATTERN = re.compile(r'^\t|    (.*)$')


class Package:

    def __init__(self, path: str) -> None:
        self._path = path
        self._pkgbuild = {}

        self.__read_pkgbuild()
        self.__check_pkgbuild_vars()

    def prepare(self, ci: bool = False) -> None:
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
        self.__exec(
            "makepkg --printsrcinfo > .SRCINFO",
            self.get_build_path())

        # Parse .SRCINFO
        srcinfo = SRCINFO(os.path.join(self.get_build_path(), '.SRCINFO'))

        # CI specific stuff
        if ci:
            # Uninstall all packages that were needed to run this script
            self.__exec("yay -Rs --noconfirm python-clicolor", '.')

        # Install dependencies
        deps = srcinfo._base.get('depends', [])
        make_deps = srcinfo._base.get('makedepends', [])
        check_deps = srcinfo._base.get('checkdepends', [])
        all_deps = deps + make_deps + check_deps
        if len(all_deps) > 0:
            print(f"Installing {len(all_deps)} dependencies")
            dep_str = '"' + '" "'.join(all_deps) + '"'
            self.__exec(f"yay -S --asdeps --noconfirm --needed {dep_str}", '.')
        else:
            print("No dependencies to install")

    def build(self) -> None:
        # Build package
        print(f"Building package")
        self.__exec(
            "makepkg --noconfirm --cleanbuild",
            self.get_build_path())

    def test(self, install: bool = True, ci: bool = False) -> None:
        # Assumes files exist in build dir then runs namcap and tries to
        # install the package

        # Read project namcap settings
        namcap_settings = self.__read_namcap_settings()

        # Find package files
        glob_str = os.path.join(self.get_build_path(),
                                f"{self.get_name()}*.pkg.*")
        results = [os.path.basename(r) for r in glob.glob(glob_str)]

        if len(results) != 1:
            raise Exception(f"Expected only 1 package. Found {len(results)}")

        # CI specific stuff
        if ci:
            # Install namcap
            self.__exec("yay -S --noconfirm --needed namcap", '.')

        # Run namcap
        exclusion_args = ""
        if namcap_settings['exclude']:
            exclusion_args = f"-e {','.join(namcap_settings['exclude'])} "
        archive_args = ' '.join(results)
        proc = self.__exec(
            f"namcap {exclusion_args}{archive_args} PKGBUILD",
            self.get_build_path(),
            capture=True)

        # Check namcap didn't warn or error
        output_raw = proc.stdout.decode()
        output = output_raw.splitlines()
        output = [o for o in output if
                  o not in namcap_settings['exclude_lines']]
        if output:
            print('\n'.join(output))
            raise Exception("Namcap found issues")

        # Install package
        if install:
            cmd = f"yay -U --noconfirm --noprogressbar {results[0]}"
            self.__exec(cmd, self.get_build_path())

    def __read_namcap_settings(self) -> Dict[str, object]:
        # Default
        settings = {
            'exclude': [],
            'exclude_lines': [],
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

    def __exec(self, cmd: str, directory: str, capture: bool = False
               ) -> subprocess.CompletedProcess:
        print(f"{directory}$ {cmd}")
        proc = subprocess.run(cmd, shell=True, cwd=directory,
                              capture_output=capture)
        if proc.returncode != 0:
            raise Exception(f"Returned error code {proc.returncode}")
        return proc

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
