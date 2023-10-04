#!/bin/bash
# Builds the package and checks it with twine.

set -e

source ./get_path.sh

cd $REPO
python3 -m build
python3 -m twine check $REPO/dist/*
