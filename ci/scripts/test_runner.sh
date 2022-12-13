#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

python3 -m pytest $REPO/ci/tests -s -vv --cov --cov-config=$REPO/ci/config/.coveragerc --doctest-modules flask_openapi