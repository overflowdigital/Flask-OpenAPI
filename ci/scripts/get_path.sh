#!/bin/bash
# Get the path to the repository root directory.

REPO="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
REPO=$(dirname "$REPO../")
export REPO=$(dirname "$REPO../")

echo "Root of repository: $REPO"