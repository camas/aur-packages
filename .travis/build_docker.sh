#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Generate mirrorlist. Travis' servers are in the US
curl -s "https://www.archlinux.org/mirrorlist/?country=US&protocol=https&use_mirror_status=on" \
    | sed -e 's/^#Server/Server/' -e '/^#/d' \
    | ./.travis/rankmirrors -n 5 - > ./.travis/aur-ci-img/mirrorlist

# Login to docker
docker login -u "camas" -p "$DOCKER_PASSWORD"

if [[ "$TRAVIS_EVENT_TYPE" == 'cron' ]]
then
    # Full build of image
    docker build -t aur-ci -f ./.travis/aur-ci-img/Dockerfile .
else
    # Build using cache
    docker pull camas/aur-ci:latest
    docker build -t aur-ci -f ./.travis/aur-ci-img/Dockerfile \
        --cache-from camas/aur-ci:latest .
fi

# Tag and push
docker tag aur-ci camas/aur-ci:latest
docker tag aur-ci camas/aur-ci:"$TRAVIS_BUILD_ID"
docker push camas/aur-ci:latest
docker push camas/aur-ci:"$TRAVIS_BUILD_ID"
