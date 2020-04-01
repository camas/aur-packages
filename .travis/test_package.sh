#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

# Build packager
cargo build --manifest-path src/Cargo.toml
cp src/target/debug/packager packager
cp src/target/debug/package_tester image/package_tester

# Pull latest image to save on compile time
docker pull camas/aur-ci:"$TRAVIS_BUILD_ID"
docker tag camas/aur-ci:"$TRAVIS_BUILD_ID" camas/aur-packages

# Run tests
./packager -vvvv test "$PACKAGE"
