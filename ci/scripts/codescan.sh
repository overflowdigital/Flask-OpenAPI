#!/bin/bash

set -e
set -x

TOOL=$1


REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

diff_files=gh pr view $PR --json files --jq '.files.[].path'


echo "Running against files: $(diff_files)"

case $TOOL in
    'black')
        black --check $(diff_files)
        ;;
    'isort')
        isort --check-only $(diff_files)
        ;;
    'flake8')
        flake8 $REPO/src/flask_openapi --config $REPO/ci/config/.flake8rc $(diff_files)
        ;;
    'mypy')
        mypy --config-file $REPO/ci/config/.mypyrc $REPO/src/flask_openapi $(diff_files)
        ;;
    'safety')
        safety check --full-report --file $REPO/requirements.txt
        ;;
    *)
        echo "Unknown tool: $TOOL"
        exit 1
        ;;
esac