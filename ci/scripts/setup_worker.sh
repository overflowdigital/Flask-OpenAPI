#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$SCRIPTPATH../")

sudo apt-get update && sudo apt-get upgrade -y
python3 -m pip install --upgrade pip
python3 -m pip install -r ci/requirements.txt
python3 -m pip install -r requirements.txt
sudo python3 -m setup develop