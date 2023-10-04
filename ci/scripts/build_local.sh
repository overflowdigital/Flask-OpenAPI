#!/bin/bash
# Builds the package and installs it locally.

set -e

# Change this to whatever python interpreter you use.
PYTHON_INTERP="/opt/homebrew/bin/python3.10"

source ./get_path.sh

rm -rf $REPO/dist
$PYTHON_INTERP -m build
$PYTHON_INTERP -m pip uninstall Flask-OpenAPI3-UI
$PYTHON_INTERP -m pip install $REPO/dist/Flask_OpenAPI3_UI-9.9.9-py3-none-any.whl