#!/bin/sh

test -d dist || mkdir dist
zip -r -FS dist/keyboard_compositor.xpi manifest.json kc_content_script.js
