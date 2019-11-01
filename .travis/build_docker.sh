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
