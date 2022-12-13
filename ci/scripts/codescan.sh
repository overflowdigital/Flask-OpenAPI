#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$SCRIPTPATH../")

flake8 $REPO/flask_openapi --config $REPO/ci/config/.flake8rc
mypy --config-file $REPO/ci/config/.mypyrc $REPO/flask_openapi || true
pylint --rcfile=$REPO/ci/config/.pylintrc $REPO/flask_openapi
safety check --full-report