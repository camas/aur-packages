# Camas' AUR Packages/Manager

[![Build Status](https://travis-ci.com/camas/aur-packages.svg?branch=master)](https://travis-ci.com/camas/aur-packages)

A package manager/tester/deployer for all of my aur packages. Uses Travis CI for CI

All packages are in `/packages`

All travis related files are in `/.travis`

Packages are built in `/build` and deployed in `/dist`. Both are cleaned at the start of these steps

Uses `packager.py` to manage packages

Requires `yay`, `namcap`

Requires pip packages `requests`, `python-dateutil` and `clicolor`

## Example

Lines starting with `$` are typed in. Lines starting with `{path}$` are output from `packager.py`

```shell_session
$ python packager.py header
                       Camas' AUR Packager

            Builds, tests and deploys pacman packages
              https://github.com/camas/aur-packages/

                  master | 374a2ef5 | 55 commits

    python-dnsdumpster-api-git atlauncher-git python-clicolor
pdlist-git python-clicolor-git python-setuptools-git-ver python-od

$ python packager.py prepare python-clicolor
Preparing 1 packages:
  python-clicolor

Preparing 1/1 python-clicolor
Copying files to build/python-clicolor
Creating .SRCINFO
build/python-clicolor$ makepkg --printsrcinfo > .SRCINFO
Installing 2 dependencies
.$ yay -S --asdeps --noconfirm --needed "python" "python-setuptools"
warning: python-3.7.4-2 is up to date -- skipping
warning: python-setuptools-1:41.2.0-1 is up to date -- skipping
 there is nothing to do

$ python packager.py build python-clicolor
Building 1 packages:
  python-clicolor

Building 1/1 python-clicolor
Building package
build/python-clicolor$ makepkg --noconfirm --cleanbuild
==> Making package: python-clicolor 1.0.7-1 (Fri 01 Nov 2019 08:59:49 PM GMT)
==> Checking runtime dependencies...
==> Checking buildtime dependencies...
==> Retrieving sources...
  -> Downloading clicolor-1.0.7.tar.gz...
==> Validating source files with sha256sums...
    clicolor-1.0.7.tar.gz ... Passed
==> Removing existing $srcdir/ directory...
==> Extracting sources...
  -> Extracting clicolor-1.0.7.tar.gz with bsdtar
==> Starting build()...
running build
running build_py
creating build
creating build/lib
creating build/lib/clicolor
copying clicolor/__init__.py -> build/lib/clicolor
copying clicolor/cli.py -> build/lib/clicolor
==> Entering fakeroot environment...
==> Starting package()...
running install
running install_lib
...
running install_scripts
==> Tidying install...
  -> Removing libtool files...
  -> Purging unwanted files...
  -> Removing static library files...
  -> Stripping unneeded symbols from binaries and libraries...
  -> Compressing man and info pages...
==> Checking for packaging issues...
==> Creating package "python-clicolor"...
  -> Generating .PKGINFO file...
  -> Generating .BUILDINFO file...
  -> Generating .MTREE file...
  -> Compressing package...
==> Leaving fakeroot environment.
==> Finished making: python-clicolor 1.0.7-1 (Fri 01 Nov 2019 08:59:55 PM GMT)

$ python packager.py test python-clicolor
Testing 1 packages:
  python-clicolor

Testing 1/1 python-clicolor
build/python-clicolor$ namcap python-clicolor-1.0.7-1-any.pkg.tar.lzo PKGBUILD
build/python-clicolor$ yay -U --noconfirm --noprogressbar python-clicolor-1.0.7-1-any.pkg.tar.lzo
loading packages...
warning: python-clicolor-1.0.7-1 is up to date -- reinstalling
resolving dependencies...
looking for conflicting packages...

Packages (1) python-clicolor-1.0.7-1

Total Installed Size:  0.06 MiB
Net Upgrade Size:      0.00 MiB

:: Proceed with installation? [Y/n]
checking keyring...
checking package integrity...
loading package files...
checking for file conflicts...
checking available disk space...
:: Processing package changes...
reinstalling python-clicolor...
:: Running post-transaction hooks...
(1/1) Arming ConditionNeedsUpdate...
```
