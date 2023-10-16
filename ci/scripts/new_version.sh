#!/bin/bash
# This script is used to update the version of the package.

set -e
set -x

PWD=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $PWD/get_path.sh

# Get the argument
ARG=$1

# Function to replace the version
function replace() {
    VERSION=$1
    echo "Replacing version with: $VERSION"
    sed -i "s/__version__ = .*/__version__ = \""$VERSION"\"/g" "$REPO/src/flask_openapi/__init__.py"
}

# Check if the argument is empty
if [ -z "$ARG" ]; then
    echo "No argument provided. Please provide a version number or 'auto_increment'"
    exit 1
fi

echo "Got argument: $ARG"
echo "Repo root is: $REPO"

# Check if the argument is auto_increment
if [ $ARG == 'auto_increment' ]; then
    EXISTING_VERSION_DEF_LOCATION="$REPO/src/flask_openapi/__init__.py"
    read_file=""

    # Read the file line by line
    while IFS= read -r line; do
        # Check if the line contains the version definition
        if [[ $line == '__version__ = '* ]]; then
            read_file="$line"
            break
        fi
    done < "$EXISTING_VERSION_DEF_LOCATION"

    # Get the version number
    VERSION=$(echo "$read_file" | awk -F= '{print $2}' | tr -d ' "')
    IFS="." read -ra parts <<< "$VERSION"

    echo "Current version is: $VERSION"

    # Increment the minor version
    MAJOR="${parts[0]}"
    MINOR="${parts[1]}"
    PATCH="${parts[2]%'\'*}"

    ((MINOR++))

    # Replace the version
    replace "$MAJOR.$MINOR.$PATCH"
else
    # Replace the version
    replace $ARG
fi

