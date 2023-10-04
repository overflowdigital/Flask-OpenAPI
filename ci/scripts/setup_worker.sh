#!/bin/bash
# Sets up the worker environment.

set -e

source get_path.sh

sudo apt update
sudo apt upgrade -y

python3 -m pip install --upgrade pip
python3 -m pip install -r $REPO/ci/config/requirements.txt
