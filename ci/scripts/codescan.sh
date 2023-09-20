#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

black --check $REPO/src/flask_openapi
mypy --config-file $REPO/ci/config/.mypyrc $REPO/src/flask_openapi
safety check --full-report
