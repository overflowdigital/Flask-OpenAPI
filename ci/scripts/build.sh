#!/bin/bash
# Builds the package and checks it with twine.

set -e

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

cd $REPO
python3 -m build
python3 -m twine check $REPO/dist/*
