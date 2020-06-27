#!/bin/bash
# Copyright 2020 Pascal COMBES <pascom@orange.fr>
# 
# This file is part of KeyboardCompositor.
# 
# KeyboardCompositor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# KeyboardCompositor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with KeyboardCompositor. If not, see <http://www.gnu.org/licenses/>

BASE_PATH="$(dirname "$0")"

# Compile mappings and list them
mappingList=
for mapping in $(ls "$BASE_PATH/src/mappings.in/"); do
    echo -n "Processing mapping: $mapping ..."
    cat "$BASE_PATH/src/mappings.in/$mapping" | sed -e 's;//.*$;;' -e 's; \+;;g' | tr -d '\n' | sed -e 's;,\(]\|}\);\1;' > "$BASE_PATH/src/mappings/${mapping%.*}.json"
    mappingName="$(grep '^// Name: ' "$BASE_PATH/src/mappings.in/$mapping" | cut -c 10-)"
    mappingIcon="$(grep '^// Icon: ' "$BASE_PATH/src/mappings.in/$mapping" | cut -c 10-)"
    mappingList="$mappingList,{\"code\":\"${mapping%.*}\", \"name\":\"${mappingName}\", \"icon\":\"${mappingIcon}\"}"
    echo "DONE"
done
echo -n "[${mappingList#,}]" > "$BASE_PATH/src/mappings/list.json"

# Build the *.xpi file
test -d dist || mkdir dist
pushd src
zip -r -FS ../dist/keyboard_compositor.xpi \
    manifest.json                          \
    kc_background.js                       \
    kc_content_script.js                   \
    kc_content_script.css                  \
    mappings/*.json                        \
    icons/32x32/flags/*.png
popd


