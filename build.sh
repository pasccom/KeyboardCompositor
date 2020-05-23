#!/bin/sh

test -d dist || mkdir dist
zip -r -FS dist/phonetic_keyboard.xpi manifest.json phonetic_keyboard.js
