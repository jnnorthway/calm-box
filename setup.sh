#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

REPO_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo CALM_HOME=$REPO_DIR > $REPO_DIR/.env

if [ -f $REPO_DIR/calm-box.service ]; then
    systemctl stop calm-box.service
    systemctl disable calm-box.service
    rm $REPO_DIR/calm-box.service
fi
cp $REPO_DIR/calm-box.service /etc/systemd/system/
sed -i "s#{REPLACE_ME}#$REPO_DIR/.env#g" /etc/systemd/system/calm-box.service

systemctl daemon-reload

while true; do
    read -p "Update on startup? (y/n) " rsp
    case $rsp in
        [yY] )
            echo UPDATE_ON_START="true" >> $REPO_DIR/.env
            break;;
        [nN] )
            echo UPDATE_ON_START="false" >> $REPO_DIR/.env
            break;;
        * )
            echo invalid response;;
    esac
done

while true; do
    read -p "Force update? (y/n) " rsp
    case $rsp in
        [yY] )
            echo FORCE_UPDATE="true" >> $REPO_DIR/.env
            break;;
        [nN] )
            echo FORCE_UPDATE="false" >> $REPO_DIR/.env
            break;;
        * )
            echo invalid response;;
    esac
done

read -p "Tracking branch? (default: main) " rsp
if [[ -z $rsp ]]; then
    echo TRACKING_BRANCH="main" >> $REPO_DIR/.env
else
    echo TRACKING_BRANCH="$rsp" >> $REPO_DIR/.env
fi

while true; do
    read -p "Enable calm-box.service on startup? (y/n) " rsp
    case $rsp in
        [yY] )
            systemctl enable calm-box.service
            break;;
        [nN] )
            break;;
        * )
            echo invalid response;;
    esac
done

while true; do
    read -p "Start calm-box.service now? (y/n) " rsp
    case $rsp in
        [yY] )
            systemctl start calm-box.service
            break;;
        [nN] )
            break;;
        * )
            echo invalid response;;
    esac
done
