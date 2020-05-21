# Camas' AUR Packages/Manager

![Build Status](https://github.com/camas/aur-packages/workflows/build-rust/badge.svg
) ![Package Status](https://github.com/camas/aur-packages/workflows/test-packages/badge.svg
)

A package manager/tester/deployer for all of my aur packages.

All packages are in `/packages`

Per-package settings are stored in `/packages/[name]/.settings.yaml`

Packages are deployed using `/dist`

Use `packager` to manage packages

## Useful Links

Links to various things I've read while creating this

- <https://github.com/alexf91/AUR-PKGBUILDs> - Similar project that I originally forked before re-creating from scratch

- <https://wiki.archlinux.org/index.php/PKGBUILD> - `PKGBUILD` file specification

- <https://wiki.archlinux.org/index.php/.SRCINFO> - `.SRCINFO` file specification

- <https://wiki.archlinux.org/index.php/Makepkg> - `makepkg` docs

- <https://wiki.archlinux.org/index.php/Namcap#Dependencies> - `namcap` docs. Used to test packages

- <https://github.com/koalaman/shellcheck/blob/master/README.md> - `shellcheck` docs. Used to test `PKGBUILD` for script errors

- <https://wiki.archlinux.org/index.php/creating_packages> - Package creation wiki page

- <https://wiki.archlinux.org/index.php/Arch_package_guidelines> - Package guidelines

- <https://wiki.archlinux.org/index.php/AUR_submission_guidelines> - AUR package guidelines
