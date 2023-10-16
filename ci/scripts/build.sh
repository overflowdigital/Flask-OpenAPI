#!/bin/bash
# Builds the package and checks it with twine.

set -e

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

cd $REPO
python -m build
python -m twine check $REPO/dist/*
