#!/bin/bash

# Check if update on start is configured
if [[ "$UPDATE_ON_START" != "true" ]]; then
    echo "UPDATE_ON_START is not set to true, continuing with loaded version"
    exit 0
fi
# Check if network is online
if ! ping -c 1 8.8.8.8; then
    echo "Network is not online, continuing with loaded version"
    exit 0
fi

pushd $CALM_HOME

if ! git diff-index --quiet HEAD -- || ! test -z "$(git ls-files --others)"; then
    echo "Changes in the repo have been found"
    if [[ "$FORCE_UPDATE" != "true" ]]; then
        echo "FORCE_UPDATE is not set to true, continuing with loaded version"
        exit 0
    fi
fi

git checkout origin $TRACKING_BRANCH
git reset HEAD --hard

git pull origin $TRACKING_BRANCH

echo "Repo has been updated"
