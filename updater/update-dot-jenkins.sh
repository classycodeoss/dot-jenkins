#!/bin/sh
INSTALL_DIR=/opt/dot-jenkins
echo "Updating dot-jenkins from github to $INSTALL_DIR and restarting supervisord"
curl -L --silent \
    https://github.com/suzukieng/dot-jenkins/archive/HEAD.tar.gz \
    | tar xz -C $INSTALL_DIR --strip-components 1 \
    && pkill -HUP supervisord
