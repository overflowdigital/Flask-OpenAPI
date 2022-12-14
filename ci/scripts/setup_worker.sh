#!/bin/bash

set -e
set -x

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
REPO=$(dirname "$REPO../")

sudo apt-get update && sudo apt-get upgrade -y
python3 -m pip install --upgrade pip
python3 -m pip install -r $REPO/ci/config/requirements.txt
python3 -m pip install -r $REPO/requirements.txt
<<<<<<< HEAD
sudo python3 -m pip install -e $REPO
=======
sudo python3 setup.py develop
sudo python3 setup.py check
>>>>>>> aaaa1eb1472d50640cb4789ec83391af0aad8de5
