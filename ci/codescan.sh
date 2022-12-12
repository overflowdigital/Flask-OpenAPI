#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$SCRIPTPATH../")

flake8 $REPO/flask_openapi --extend-ignore=E501
#mypy --show-error-codes --pretty --ignore-missing-imports --disable-error-code attr-defined $REPO/flask_openapi
pylint --rcfile=$REPO/ci/.pylintrc $REPO/flask_openapi
safety check --full-report -i 40459