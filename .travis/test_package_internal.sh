#!/bin/bash

# Show commands
set -x

# Fail immediately on error 
set -e

if [ -z "$1" ] 
then
    echo "No package supplied"
    exit 1
fi

# Print header
python packager.py header

# Prep/build/test package
python packager.py full --ci "$1"
