#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Generate mirrorlist. Travis' servers are in the US
curl -s "https://www.archlinux.org/mirrorlist/?country=US&protocol=https&use_mirror_status=on" \
    | sed -e 's/^#Server/Server/' -e '/^#/d' \
    | ./.travis/rankmirrors -n 5 - > ./.travis/aur-ci-img/mirrorlist

# Build and upload image
docker login -u "camas" -p "$DOCKER_PASSWORD"
docker build -t aur-ci -f ./.travis/aur-ci-img/Dockerfile .
docker tag aur-ci camas/aur-ci
docker push camas/aur-ci
