#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

python3 -m pytest $REPO/ci/tests --ignore=$REPO/ci/tests/suite -c $REPO/ci/config/.pytestrc -s -vv --cov --cov-config=$REPO/ci/config/.coveragerc --junit-xml=$REPO/ci/tests/report.xml --doctest-modules flask_openapi
