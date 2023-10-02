#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

python3 -m pytest $REPO/ci/tests --ignore=$REPO/ci/tests/suite -c $REPO/ci/config/.pytestrc -s -vv --cov=$REPO/src/flask_openapi/ --cov-config=$REPO/ci/config/.coveragerc --cov-report xml:$REPO/ci/tests/coverage.xml --junit-xml=$REPO/ci/tests/report.xml --full-trace --log-file=$REPO/ci/tests/pytest.log --doctest-modules $REPO/src/flask_openapi
