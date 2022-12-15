#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

flake8 $REPO/src/flask_openapi --config $REPO/ci/config/.flake8rc || true
mypy --config-file $REPO/ci/config/.mypyrc $REPO/src/flask_openapi || true
pylint --rcfile=$REPO/ci/config/.pylintrc $REPO/src/flask_openapi || true
safety check --full-report