#!/bin/bash
# Sets up the worker environment.

set -e

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

sudo apt update
sudo apt upgrade -y

sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1
sudo update-alternatives --config python

python3 -m pip install --upgrade pip
python3 -m pip install -r $REPO/ci/config/requirements.txt

mkdir -p $REPO/ci/codescan_logs
