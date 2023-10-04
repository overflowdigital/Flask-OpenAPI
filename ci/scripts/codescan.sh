#!/bin/bash
# Runs a code scan tool on the repository.

set -e

TOOL=$1

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

# Run the tool on the repository based on the argument.
case $TOOL in
    'black')
        black --check $REPO/src > $REPO/ci/codescan_logs/black.log
        ;;
    'flake8')
        flake8 $REPO/src/flask_openapi --config $REPO/ci/config/.flake8rc $REPO/src > $REPO/ci/codescan_logs/flake8.log
        ;;
    'mypy')
        mypy --config-file $REPO/ci/config/.mypyrc $REPO/src > $REPO/ci/codescan_logs/mypy.log
        ;;
    'safety')
        safety check --full-report --file $REPO/requirements.txt > $REPO/ci/codescan_logs/safety.log
        ;;
    *)
        echo "Unknown tool: $TOOL"
        echo "Available tools: black, flake8, mypy, safety"
        exit 1
        ;;
esac