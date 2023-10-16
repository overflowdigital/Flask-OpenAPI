#!/bin/bash
# Sets up the worker environment.

set -e

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

sudo apt update
sudo apt upgrade -y

python -m pip install --upgrade pip
python -m pip install -r $REPO/ci/config/requirements.txt

mkdir -p $REPO/ci/codescan_logs
