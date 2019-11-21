#!/bin/bash

set -e

package="$1"

source packages/"$package"/PKGBUILD

echo "$pkgver"
echo "$pkgrel"
