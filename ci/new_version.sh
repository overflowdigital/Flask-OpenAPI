#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$SCRIPTPATH../")

VERSION=$1

echo 'Bumping version to $VERSION'
sed 's/__version__ =  .*/__version__ = "'$VERSION'"/g' -i flask_openapi/__init__.py