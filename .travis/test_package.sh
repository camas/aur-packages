#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Pull latest image to save on compile time
docker pull camas/aur-ci

# Run tests
python packager.py test "$PACKAGE"
