#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

python3 -m pip install --upgrade pip
python3 -m pip install -r $REPO/ci/config/requirements.txt
