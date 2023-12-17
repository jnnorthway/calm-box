#!/bin/bash

echo "Checking if UPDATE_ON_START is set..."
if [[ "$UPDATE_ON_START" != "true" ]]; then
    echo "UPDATE_ON_START is not set to true, continuing with loaded version"
    exit 0
fi
echo "OK"
echo "Checking if network is online..."
if ! timeout 1 ping -c 1 8.8.8.8; then
    echo "Network is not online, continuing with loaded version"
    exit 0
fi
echo "OK"

pushd $CALM_HOME
echo "Checking repo status..."
if ! git diff-index --quiet HEAD -- || ! test -z "$(git ls-files --others)"; then
    echo "Changes in the repo have been found"
    if [[ "$FORCE_UPDATE" != "true" ]]; then
        echo "FORCE_UPDATE is not set to true, continuing with loaded version"
        exit 0
    fi
fi
echo "OK"

echo "Updating..."
git checkout origin/$TRACKING_BRANCH
git reset HEAD --hard
git clean -f -d
git pull origin $TRACKING_BRANCH

echo "Repo has been updated"

echo "Installing new python requirements"
/usr/bin/python3 -m pip install -r requirements.txt
echo "Python requirements updated"
