#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Run docker container
# Mounts repo to /aur-packages and runs test_package_internal.sh
docker run -it --rm \
    -v "$PWD":/aur-packages \
    camas/aur-ci \
    aur-packages/.travis/test_package_internal.sh "$PACKAGE"
