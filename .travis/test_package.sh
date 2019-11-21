#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Pull latest image to save on compile time
docker pull camas/aur-ci:"$TRAVIS_BUILD_ID"
docker tag camas/aur-ci:"$TRAVIS_BUILD_ID" camas/aur-packages

# Run tests
python packager.py test "$PACKAGE"
