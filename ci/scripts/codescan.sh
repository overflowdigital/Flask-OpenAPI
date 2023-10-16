#!/bin/bash
# Runs a code scan tool on the repository.

set -e
set -x

TOOL=$1

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

# Run the tool on the repository based on the argument.
case $TOOL in
    'black')
	touch $REPO/ci/codescan_logs/black.log
        python -m black --check $REPO/src 2>&1 | tee $REPO/ci/codescan_logs/black.log
        ;;
    'flake8')
	touch $REPO/ci/codescan_logs/flake8.log
        python -m flake8 $REPO/src/flask_openapi --config $REPO/ci/config/.flake8rc $REPO/src 2>&1 | tee $REPO/ci/codescan_logs/flake8.log
        ;;
    'mypy')
	touch $REPO/ci/codescan_logs/mypy.log
        python -m mypy --config-file $REPO/ci/config/.mypyrc $REPO/src 2>&1 | tee $REPO/ci/codescan_logs/mypy.log
        ;;
    'safety')
	touch $REPO/ci/codescan_logs/safety.log
        python -m safety check --full-report --file $REPO/requirements.txt 2>&1 | tee $REPO/ci/codescan_logs/safety.log
        ;;
    *)
        echo "Unknown tool: $TOOL"
        echo "Available tools: black, flake8, mypy, safety"
        exit 1
        ;;
esac
