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
for mapping in $(ls "$BASE_PATH/src/mappings/"); do
    echo -n "Processing mapping: $mapping ..."
    cat "$BASE_PATH/src/mappings/$mapping" | sed -e 's;//.*$;;' -e 's; \+;;g' | tr -d '\n' | sed -e 's;,\(]\|}\);\1;' > "$BASE_PATH/mappings/${mapping%.*}.json"
    mappingList="$mappingList,\"${mapping%.*}\""
    echo "DONE"
done
echo -n "[${mappingList#,}]" > "$BASE_PATH/mappings/list.json"

# Build the *.xpi file
test -d dist || mkdir dist
zip -r -FS dist/keyboard_compositor.xpi manifest.json kc_content_script.js mappings/*.json
