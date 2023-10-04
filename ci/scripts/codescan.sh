#!/bin/bash

set -e
set -x

TOOL=$1

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

case $TOOL in
    'black')
        black --check $REPO/src
        ;;
    'flake8')
        flake8 $REPO/src/flask_openapi --config $REPO/ci/config/.flake8rc $REPO/src
        ;;
    'mypy')
        mypy --config-file $REPO/ci/config/.mypyrc $REPO/src || true
        ;;
    'safety')
        safety check --full-report --file $REPO/requirements.txt
        ;;
    *)
        echo "Unknown tool: $TOOL"
        exit 1
        ;;
esac