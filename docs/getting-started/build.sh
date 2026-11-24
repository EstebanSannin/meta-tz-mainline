#!/bin/sh
# Render getting-started.html to ../../GETTING-STARTED.pdf with headless Chrome (needs network for the Inter font).
set -e
cd "$(dirname "$0")"
CHROME=${CHROME:-"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"}
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=15000 \
    --print-to-pdf="$PWD/../../GETTING-STARTED.pdf" "file://$PWD/getting-started.html"
