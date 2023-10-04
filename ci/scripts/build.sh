#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

cd $REPO
python3 -m build
python3 -m twine check $REPO/dist/*
pip install $REPO/dist/Flask_OpenAPI3_UI-9.9.9-py3-none-any.whl