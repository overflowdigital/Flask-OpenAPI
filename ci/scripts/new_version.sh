#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

function auto_increment() {
    VERSION=$(python3 $REPO/ci/scripts/increment_version.py)
    sed 's/__version__ = .*/__version__ = "'$VERSION'"/g' -i $REPO/flask_openapi/__init__.py
}

function increment_manually() {
    VERSION=$1
    sed 's/__version__ = .*/__version__ = "'$VERSION'"/g' -i $REPO/flask_openapi/__init__.py
}


if [ $1 = 'auto_increment' ]; then
    auto_increment
else
    increment_manually
fi

