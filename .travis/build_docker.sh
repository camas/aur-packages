#!/bin/bash

# Fail immediately on error 
set -e

# Generate mirrorlist. Travis' servers are in the US
curl -s "https://www.archlinux.org/mirrorlist/?country=US&protocol=https&use_mirror_status=on" \
    | sed -e 's/^#Server/Server/' -e '/^#/d' \
    | rankmirrors -n 5 - > ./.travis/aur-ci-img/mirrorlist

# Build and upload image
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker build -t aur-ci ./.travis/aur-ci-img
docker tag aur-ci "$DOCKER_USERNAME"/aur-ci
docker push "$DOCKER_USERNAME"/aur-ci
