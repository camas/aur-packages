#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Make build folder world writeable
chmod -R 777 build

# Run docker container
# Mounts repo to /aur-packages and runs test_package_internal.sh
docker run -it \
    -v "$PWD":/aur-packages \
    -w /aur-packages \
    camas/aur-ci:"$TRAVIS_BUILD_ID" \
    /aur-packages/.travis/test_package_internal.sh "$PACKAGE"
