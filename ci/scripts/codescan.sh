#!/bin/bash

set -e
set -x

TOOL=$1

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

function diff_files_branch() {
    local branch=${1:-"@{u}"}
    git diff --name-only --diff-filter=d "${branch}" -- '*.py'
}

function diff_files() {
    diff_files_branch 2>/dev/null || diff_files_branch origin/main
}

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