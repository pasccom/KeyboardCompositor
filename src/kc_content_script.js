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

    var keyMapper = {
        /*!
         * \brief Wraps the event target
         *
         * This function adds a shim to ensure all the required event target properties are available.
         * The required event target properties are:
         * \li \c value
         * \li \c selectionStart
         * \li \c selectionEnd
         *
         * \param e The event to handle.
         */
        wrapEventTarget: function(e) {
            if (e.target.selectionStart === undefined)
                Object.defineProperty(e.target, 'selectionStart', {
                    get: () => {
                        var selection = window.getSelection();
                        if (selection.rangeCount == 1) {
                            var range = selection.getRangeAt(0);
                            if (range.startContainer == range.endContainer)
                                return range.startOffset;
                        }
                        return undefined;
                    },
                    set: (start) => {
                        var selection = window.getSelection();
                        if (selection.rangeCount == 1) {
                            var range = selection.getRangeAt(0);
                            if (range.startContainer == range.endContainer)
                                selection.collapse(range.commonAncestorContainer, start);
                        }
                    },
                });
            if (e.target.selectionEnd === undefined)
                Object.defineProperty(e.target, 'selectionEnd', {
                    get: () => {
                        var selection = window.getSelection();
                        if (selection.rangeCount == 1) {
                            var range = selection.getRangeAt(0);
                            if (range.startContainer == range.endContainer)
                                return range.endOffset;
                        }
                        return undefined;
                    },
                    set: (end) => {
                        var selection = window.getSelection();
                        if (selection.rangeCount == 1) {
                            var range = selection.getRangeAt(0);
                            if (range.startContainer == range.endContainer)
                                selection.collapse(range.commonAncestorContainer, end);
                        }
                    },
                });
            if (e.target.value === undefined)
                Object.defineProperty(e.target, 'value', {
                    get: () => {
                        var selection = window.getSelection();
                        if (selection.rangeCount == 1) {
                            var range = selection.getRangeAt(0);
                            if (range.startContainer == range.endContainer)
                                return range.commonAncestorContainer.textContent;
                        }
                        return undefined;
                    },
                    set: (value) => {
                        var selection = window.getSelection();
                        if (selection.rangeCount == 1) {
                            var range = selection.getRangeAt(0);
                            if (range.startContainer == range.endContainer)
                                range.commonAncestorContainer.textContent = value;
                        }
                    },
                });
            return e;
        },

        /*!
         * \brief Keyboard event handler
         *
         * This function is the event listener entry point.
         * It filters out event with modifiers set and routes the other events to the handler functions.
         * \param e The event to handle.
         */
        handleEvent: function(e) {
            // Do nothing if one of these modifiers is pressed:
            if (e.altKey || e.ctrlKey || e.metaKey)
                return;
            if (e.type == 'keydown')
                this.onKeyDown(this.wrapEventTarget(e));
            if (e.type == 'keyup')
                this.onKeyUp(this.wrapEventTarget(e));
        },

        /*!
         * \brief Key down event handler
         *
         * This function shoud be called whenever a key is pressed.
         * It unfocuses and focuses the element when the \c Enter key is pressed.
         * This is required for some websites to work.
         * \param e The event to handle.
         */
        onKeyDown: function(e) {
            if (e.key != 'Enter')
                return;

            var posStart = e.target.selectionStart;
            var posEnd = e.target.selectionEnd;
            e.target.blur();
            e.target.focus();
            e.target.selectionStart = posStart;
            e.target.selectionEnd = posEnd;
        },

        /*!
         * \brief Key up event handler
         *
         * This function shoud be called whenever a key is released.
         * It applies the mappings. This is thus the core of the extension.
         * \param e The event to handle.
         */
        onKeyUp: function(e) {
            // Get mapping:
            var mapping = e.target.getAttribute('kc-lang');
            if (!mapping)
                mapping = e.target.getAttribute('lang');
            // Do nothing if mapping is not loaded:
            if (mappings[mapping] === undefined) {
                console.error("Mapping \"" + mapping + "\" is not loading.");
                return;
            } else if (mappings[mapping] === null) {
                console.warn("Mapping \"" + mapping + "\" is not loaded.");
                return;
            } else {
                mapping = mappings[mapping];
            }
            // Check that nothing is selected:
            var posStart = e.target.selectionStart;
            var posEnd = e.target.selectionEnd;
            if ((posStart === undefined) || (posEnd === undefined) || (posStart != posEnd))
                return;
            // Apply mapping:
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
                var backspaceKeyEventInit = {
                    key: "Backspace",
                    code: "Backspace",
                    view: e.view,
                    bubbles: true,
                    cancelable: true,
                };
                var backspaceInputEventInit = {
                    inputType: "deleteContentBackward",
                    view: e.view,
                    bubbles: true,
                    cancelable: true,
                };

                e.target.dispatchEvent(new KeyboardEvent('keydown', backspaceKeyEventInit));
                e.target.value = t.slice(0, posStart - c) + t.slice(posStart);
                e.target.dispatchEvent(new InputEvent('input', backspaceInputEventInit));
                e.target.selectionStart = posStart - c;
                e.target.selectionEnd = posEnd - c;
                e.target.dispatchEvent(new KeyboardEvent('keyup', backspaceKeyEventInit));
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
                var inputEventInit = {
                    data: keys[c - 1],
                    inputType: "insertText",
                    view: e.view,
                    bubbles: true,
                    cancelable: true,
                };

                e.target.dispatchEvent(new KeyboardEvent('keydown', keyEventInit));
                e.target.value = t.slice(0, posStart - l) + keys.slice(0, c) + t.slice(posStart);
                e.target.dispatchEvent(new KeyboardEvent('keypress', keyEventInit));
                e.target.dispatchEvent(new InputEvent('input', inputEventInit));
                e.target.selectionStart = posStart - l + c;
                e.target.selectionEnd = posEnd - l + c;
                e.target.dispatchEvent(new KeyboardEvent('keyup', keyEventInit));
            }
        },

        /*!
        * \brief Install key mapper on given element
        *
        * This function install the key mapper event listeners on the given element.
        * The extension will then listen to \c keyup events and remap typed keys when needed.
        * It will also listen to \c keydown events, as this is needed for Duolingo to work weel
        *
        * \param element The element on which to install the extension.
        */
        install: function(element) {
            console.log("Installing on:", element);

            element.addEventListener('keydown', this);
            element.addEventListener('keyup', this, true);
        },

        /*!
        * \brief Unnstall key mapper on given element
        *
        * This function uninstall the key mapper event listeners on the given element.
        *
        * \param element The element on which to uninstall the extension.
        */
        uninstall: function(element) {
            console.log("Uninstalling on:", element);

            element.removeEventListener('keydown', this);
            element.removeEventListener('keyup', this, true);
        },
    };

    function addLanguageIcon(element, mapping) {
        var icon = document.createElement('IMG');
        icon.setAttribute('src', browser.runtime.getURL('icons/32x32/flags/' + mapping.icon));
        icon.setAttribute('class', 'kc-flag');
        icon.setAttribute('alt', mapping.name);
        icon.setAttribute('title', mapping.name);

        var root = icon;
        if (getComputedStyle(element).getPropertyValue('display') == 'block') {
            icon.setAttribute('style', 'vertical-align: top;');
            root = document.createElement('DIV');
            root.setAttribute('class', 'kc-div');
            root.appendChild(icon);
        }

        removeLanguageIcon(element);
        if (element.nextSibling)
            element.parentNode.insertBefore(root, element.nextSibling);
        else
            element.parentNode.appendChild(root);

        var elementRect = element.getBoundingClientRect();
        var iconRect = icon.getBoundingClientRect();

        if (getComputedStyle(element).getPropertyValue('display') == 'block') {
            icon.setAttribute('style', 'left: ' + (elementRect.right - iconRect.right - 4) + 'px; top: ' + (elementRect.bottom - iconRect.top - 32) + 'px;');
        } else {
            icon.setAttribute('style', 'margin-left: ' + (elementRect.right - iconRect.right - 32 - 4) + 'px; margin-bottom: ' + (iconRect.bottom - elementRect.bottom) + 'px;');
        }
    }

    function removeLanguageIcon(element) {
        var icon = element.nextElementSibling;
        if (icon && (icon.tagName == 'IMG') && (icon.className == 'kc-flag'))
            element.parentNode.removeChild(icon);
        if (icon && (icon.tagName == 'DIV') && (icon.className == 'kc-div'))
            element.parentNode.removeChild(icon);
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
                if (textArea.getAttribute('lang') == mapping.code) {
                    loadMapping(mapping.code);
                    keyMapper.install(textArea);
                    addLanguageIcon(textArea, mapping);
                }
            });
        }

        // Search for text inputs
        for (const input of element.getElementsByTagName('input')) {
            list.forEach((mapping) => {
                if ((input.getAttribute('type') == 'text') && (input.getAttribute('lang') == mapping.code)) {
                    loadMapping(mapping.code);
                    keyMapper.install(input);
                    addLanguageIcon(input, mapping);
                }
            });
        }

        // Search editable elements
        for (const editable of element.querySelectorAll('[contentEditable="true"]')) {
            list.forEach((mapping) => {
                if (editable.getAttribute('lang') == mapping.code) {
                    loadMapping(mapping.code);
                    keyMapper.install(editable);
                    addLanguageIcon(editable, mapping);
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
                record.addedNodes.forEach((node) => {
                    if ((node.nodeType == Node.ELEMENT_NODE)
                     || (node.nodeType == Node.DOCUMENT_NODE)
                     || (node.nodeType == Node.DOCUMENT_FRAGMENT_NODE))
                        searchTextFields(node, list);
                });
            }
        });

        bodyObserver.observe(document.body, {
            subtree: true,
            childList: true,
        });

        // Search for text fields on body
        searchTextFields(document.body, list);

        browser.runtime.onMessage.addListener((message, sender, sendResponse) => {
            var element = message.elementId ? browser.menus.getTargetElement(message.elementId) : document.activeElement;

            while (element && element.isContentEditable && (element.contentEditable != 'true'))
                element = element.parentElement;
            if (!element)
                return;

            var oldKCLang = element.getAttribute('kc-lang');

            if (message.command == "GET_LANG") {
                sendResponse([
                    element.getAttribute('lang'),
                    oldKCLang,
                ]);
            } else if (message.command == "SET_LANG") {
                loadMapping(message.lang);
                element.setAttribute('kc-lang', message.lang);
                addLanguageIcon(element, list.find((e) => (e.code == element.getAttribute('kc-lang'))));
                if (!oldKCLang && !list.find((e) => (e.code == element.getAttribute('lang'))))
                    keyMapper.install(element);
            } else if (message.command == "REMOVE_LANG") {
                removeLanguageIcon(element);
                element.removeAttribute('kc-lang');
                if (oldKCLang && !list.find((e) => (e.code == element.getAttribute('lang'))))
                    keyMapper.uninstall(element);
                else if (oldKCLang)
                    addLanguageIcon(element, list.find((e) => (e.code == element.getAttribute('lang'))));
            }
        });
    }

    fetch(browser.runtime.getURL("mappings/list.json"), {method: "GET"})
        .then((response) => response.json())
        .then((list) => {installMappings(list);})
        .catch((error) => {console.error(error);});
})();
