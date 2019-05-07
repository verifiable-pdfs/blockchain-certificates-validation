#!/bin/bash
# Copy files from customize/ directory to their relevant locations

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [ ! -d $DIR/customize ]; then
    echo "customize/ directory not found, exiting..."
    exit 1
fi

echo "Copying files from customize/ to their relevant locations..."

if [ -f $DIR/customize/config.ini ]; then
    cp $DIR/customize/config.ini $DIR/
    echo "Copied config.ini..."
fi
if [ -f $DIR/customize/logo.png ]; then
    cp $DIR/customize/logo.png $DIR/static/logo.png
    echo "Copied logo.png..."
fi
if [ -f $DIR/customize/main.css ]; then
    cp $DIR/customize/main.css $DIR/static/main.css
    echo "Copied main.css..."
fi