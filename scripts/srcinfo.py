import re

SRCINFO_PATTERN = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*) = (.*)$')

FIELDS = ['pkgdesc', 'url', 'install', 'changelog']
BASE_FIELDS = ['pkgver', 'pkgrel', 'epoch']
ARRAY_FIELDS = ['arch', 'groups', 'license', 'noextract', 'options', 'backup',
                'validpgpkeys']
ARCH_FIELDS = ['source', 'depends', 'makedepends', 'optdepends', 'provides',
               'conflicts', 'replaces', 'md5sums', 'sha1sums', 'sha224sums',
               'sha256sums', 'sha384sums', 'sha521sums']


class SRCINFO:
    def __init__(self, path: str) -> None:
        self._read_path = path

        self.__read(path)

    def __read(self, path):
        with open(path, 'r') as f:
            lines = f.read().splitlines()

        self._base = {}
        self._packages = {}

        cur_section = None
        is_base = True
        done_base = False
        for line in lines:
            match = SRCINFO_PATTERN.match(line)
            if not match:
                continue

            key = match.group(1)
            value = match.group(2).rstrip()

            if key == 'pkgbase':
                if done_base:
                    raise Exception("Already read a pkgbase section")
                cur_section = self._base
                is_base = True
                done_base = True
                cur_section[key] = value
                continue

            if key == 'pkgname':
                cur_section = {}
                self._packages[value] = cur_section
                is_base = False
                cur_section[key] = value
                continue

            if key in FIELDS:
                if key in cur_section:
                    raise Exception(f"Value for {key} already exists")
                cur_section[key] = value
            elif key in BASE_FIELDS:
                if not is_base:
                    emsg = f"{key} can only be used in a pkgbase section"
                    raise Exception(emsg)
            elif key in ARRAY_FIELDS:
                if key not in cur_section:
                    cur_section[key] = []
                cur_section[key].append(value)
            elif key.split('_', maxsplit=1)[0] in ARCH_FIELDS:
                if key not in cur_section:
                    cur_section[key] = []
                cur_section[key].append(value)
            else:
                raise Exception(f"Unknown key {key}")
