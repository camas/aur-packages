#!/bin/bash

set -e

# Check package provided as argument
if [[ -z "$1" ]]; then
    echo "Package name not given"
    exit 1
fi
package="$1"

cd /packages/"$package"
source PKGBUILD

# Install dependencies
mk_name="makedepends_$(uname -m)"
tmp=$mk_name[@]
mk_var=( ${!tmp} )
d_name="depends_$(uname -m)"
tmp=$d_name[@]
d_var=( ${!tmp} )
chk_var="makedepends_$(uname -m)"
tmp=$chk_var[@]
chk_var=( ${!tmp} )
yay -S --noconfirm --asdeps --needed "${makedepends[@]}" "${depends[@]}" "${checkdepends[@]}" "${mk_var[@]}" "${d_var[@]}" "${chk_var[@]}"

# Build and install package
echo "Building $package"
makepkg --printsrcinfo > .SRCINFO
makepkg --noconfirm -i

# Remove makedepends
yay -R --noconfirm "${makedepends[@]}"

# Shell
if [[ -n "$AUR_SHELL" ]]; then
    bash
    exit
fi

# Test package
echo "Installing packages needed for tests"
yay -S --noconfirm --needed namcap shellcheck-static
echo "Testing $package"

# Namcap
touch .namcap_ignore
set +e
nam_out=$(namcap PKGBUILD "*.pkg.*" | grep -xvf .namcap_ignore)
set -e
if [[ -n "$nam_out" ]]; then
    echo "$nam_out"
    exit 1
fi

# Shellcheck
cat /packages/shellcheck_stub.sh PKGBUILD | shellcheck -
