/* Copyright 2020 Pascal COMBES <pascom@orange.fr>
 * 
 * This file is part of KeyboardCompositor.
 * 
 * KeyboardCompositor is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * KeyboardCompositor is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with KeyboardCompositor. If not, see <http://www.gnu.org/licenses/>
 */

(function() {
    'use strict'

    var mappings = {}; // Mapping cache

    /*!
     * \brief Install extension on given element
     *
     * This function install the extension event listener on the given element.
     * The extension will then listen to \c keyup events and remap typed keys when needed.
     *
     * \param element The element on which to install the extension.
     */
    function installKeyMapper(element) {
        console.log("Installing on:", element);

        element.addEventListener('keydown', function(e) {
            if (e.key == 'Enter') {
                var posStart = e.target.selectionStart;
                var posEnd = e.target.selectionEnd;
                e.target.blur();
                e.target.focus();
                e.target.selectionStart = posStart;
                e.target.selectionEnd = posEnd;
            }
        });

        element.addEventListener('keyup', function(e) {
            // Do nothing if one of these modifiers is pressed:
            if (e.altKey || e.ctrlKey || e.metaKey)
                return;
            // Do nothing if mapping is not loaded:
            if (mappings[e.target.getAttribute('lang')] === undefined) {
                console.warn("Mapping \"" + e.target.getAttribute('lang') + "\" is not loading.");
                return;
            } else if (mappings[e.target.getAttribute('lang')] === undefined) {
                return;
            }
            // Check that nothing is selected:
            var posStart = e.target.selectionStart;
            var posEnd = e.target.selectionEnd;
            if (posStart != posEnd)
                return;
            // Apply mapping:
            var mapping = mappings[e.target.getAttribute('lang')];
            var t = e.target.value;
            for (var l = 3; l > 0; l--) {
                if ((l <= t.length) && (mapping[t.slice(posStart - l, posStart)] !== undefined))
                    break;
            }
            // Do nothing if this is not a letter in the mapping:
            if (l == 0)
                return;
            // Get mapped text
            var keys = mapping[t.slice(posStart - l, posStart)];
            // Delete original text:
            for (var c = 1; c <= l; c++) {
                var backspaceEventInit = {
                    key: "Backspace",
                    code: "Backspace",
                    view: e.view,
                    bubbles: true,
                    cancelable: true,
                };

                e.target.dispatchEvent(new KeyboardEvent('keydown', backspaceEventInit));
                e.target.value = t.slice(0, posStart - c) + t.slice(posStart);
                e.target.selectionStart = posStart - c;
                e.target.selectionEnd = posEnd - c;
                e.target.dispatchEvent(new KeyboardEvent('keyup', backspaceEventInit));
            }
            // Add mapped text:
            for (var c = 1; c <= keys.length; c++) {
                var keyEventInit = {
                    key: keys[c - 1],
                    code: e.code,
                    shiftKey: e.shiftKey,
                    view: e.view,
                    bubbles: true,
                    cancelable: true,
                };

                e.target.dispatchEvent(new KeyboardEvent('keydown', keyEventInit));
                e.target.value = t.slice(0, posStart - l) + keys.slice(0, c) + t.slice(posStart);
                e.target.selectionStart = posStart - l + c;
                e.target.selectionEnd = posEnd - l + c;
                e.target.dispatchEvent(new KeyboardEvent('keypress', keyEventInit));
                e.target.dispatchEvent(new KeyboardEvent('keyup', keyEventInit));
            }
        }, true);
    }

    /*!
     * \brief Searches for text fields
     *
     * This function searches for text fields among the descendants of the given element.
     * It currently matches \c textarea and \c input of type \c text.
     *
     * \param element The element to search for text fields.
     * \param list The list of available mappings.
     */
    function searchTextFields(element, list) {
        // Search for text areas
        for (const textArea of element.getElementsByTagName('textarea')) {
            list.forEach((mapping) => {
                if (textArea.getAttribute('lang') == mapping) {
                    loadMapping(mapping);
                    installKeyMapper(textArea);
                }
            });
        }

        // Search for text inputs
        for (const input of element.getElementsByTagName('input')) {
            list.forEach((mapping) => {
                if ((input.getAttribute('type') == 'text') && (input.getAttribute('lang') == mapping)) {
                    loadMapping(mapping);
                    installKeyMapper(input);
                }
            });
        }
    }

    /*!
     * \brief Load a mapping
     *
     * This function loads a mapping in the mapping cache, if it is not already loaded.
     *
     * \param name The name of the mapping to load.
     */
    function loadMapping(name)
    {
        if (mappings[name] === undefined) {
            mappings[name] = null;
            fetch(browser.runtime.getURL("mappings/" + name + ".json"), {method: "GET"})
                .then((response) => response.json())
                .then((mapping) => {mappings[name] = mapping;})
                .catch((error) => {console.error(error);});
        }
    }

    /*!
     * \brief Install mappings
     *
     * This function starts monitoring for DOM mutation on the web page,
     * so that when a text field is added it can install a key mapper.
     *
     * \param list The list of available mappings.
     */
    function installMappings(list)
    {
        console.log("Installing mappings:", list);

        // Search for text fields in every new node using a MutationObserver
        var bodyObserver = new MutationObserver(function(mutationRecords) {
            for (const record of mutationRecords) {
                record.addedNodes.forEach((element) => {searchTextFields(element, list);});
            }
        });

        bodyObserver.observe(document.body, {
            subtree: true,
            childList: true,
        });

        // Search for text fields on body
        searchTextFields(document.body, list);
    }

    browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
        var element = message.elementId ? browser.menus.getTargetElement(message.elementId) : document.activeElement;
        if (!element)
            return;

        if (message.command == "GET_LANG") {
            sendResponse([
                element.getAttribute('lang'),
                element.getAttribute('kc-lang'),
            ]);
        } else if (message.command == "SET_LANG") {
            element.setAttribute('kc-lang', message.lang);
        } else if (message.command == "REMOVE_LANG") {
            element.removeAttribute('kc-lang');
        }
    });

    fetch(browser.runtime.getURL("mappings/list.json"), {method: "GET"})
        .then((response) => response.json())
        .then((list) => {installMappings(list.map((e) => e.code));})
        .catch((error) => {console.error(error);});
})();
