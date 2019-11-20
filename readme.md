# Camas' AUR Packages/Manager

[![Build Status](https://travis-ci.com/camas/aur-packages.svg?branch=master)](https://travis-ci.com/camas/aur-packages)

A package manager/tester/deployer for all of my aur packages. Uses Travis CI for CI

All packages are in `/packages`

Per-package settings are stored in `/packages/[name]/.settings.yaml`

All travis related files are in `/.travis`

Packages are built in `/build` and deployed in `/dist`. Both are cleaned at the start of these steps

Uses `packager.py` to manage packages

Requires `yay`, `namcap`

Requires pip packages `requests`, `python-dateutil`, `pyyaml`, `schema` and `clicolor`

## Useful Links

Links to various things I've read while creating this

- <https://github.com/alexf91/AUR-PKGBUILDs> - Similar project that I originally forked before re-creating from scratch

- <https://wiki.archlinux.org/index.php/PKGBUILD> - `PKGBUILD` file specification

- <https://wiki.archlinux.org/index.php/.SRCINFO> - `.SRCINFO` file specification

- <https://wiki.archlinux.org/index.php/Makepkg> - `makepkg` docs

- <https://docs.travis-ci.com/user/build-matrix/> - Travis build matrix docs. Used to create seperate jobs for every package

- <https://wiki.archlinux.org/index.php/Namcap#Dependencies> - `namcap` docs. Used to test packages

- <https://github.com/koalaman/shellcheck/blob/master/README.md> - `shellcheck` docs. Used to test `PKGBUILD` for script errors

- <https://wiki.archlinux.org/index.php/creating_packages> - Package creation wiki page

- <https://wiki.archlinux.org/index.php/Arch_package_guidelines> - Package guidelines

- <https://wiki.archlinux.org/index.php/AUR_submission_guidelines> - AUR package guidelines

## Example usage

```shell_session
$ python packager.py header
                       Camas' AUR Packager

            Builds, tests and deploys pacman packages
              https://github.com/camas/aur-packages/

                  master | ec5213bb | 94 commits

            atlauncher-git pdlist-git python-clicolor
  python-dnsdumpster-api-git python-od python-setuptools-git-ver
                            seclists-c

$ python packager.py test --all
...
a few hundred lines and a few minutes later
...
All packages tested successfully
```
