#!/bin/bash

# Show commands
set -x

# Fail immediately on error
set -e

# Login to docker
docker login -u "camas" -p "$DOCKER_PASSWORD"

if [[ "$TRAVIS_EVENT_TYPE" == 'cron' ]]
then
    # Full build of image
    python packager.py image fullbuild
else
    # Build using cache
    docker pull camas/aur-ci:latest
    docker tag camas/aur-ci:latest camas/aur-packages
    python packager.py image build
fi

# Tag and push
docker tag camas/aur-packages camas/aur-ci:latest
docker tag camas/aur-packages camas/aur-ci:"$TRAVIS_BUILD_ID"
docker push camas/aur-ci:latest
docker push camas/aur-ci:"$TRAVIS_BUILD_ID"
