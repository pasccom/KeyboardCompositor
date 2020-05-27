(function() {
    'use strict'

    var mapping = {
        // Lower case letters:
        // -------------------
        a : "а",
        b : "б",
        c : "с",
        d : "д",
        e : "е",
        f : "ф",
        g : "г",
        // No h
        i : "и",
        j : "ж",
        k : "к",
        l : "л",
        m : "м",
        n : "н",
        o : "о",
        p : "п",
        // No q
        r : "р",
        // No s
        t : "т",
        u : "у",
        v : "в",
        // No w
        x : "х",
        // No y
        z : "з",
        // Soft vovels:
        ya : "я",
        yA : "я",
        yi : "й",
        yI : "й",
        yo : "ё",
        yO : "ё",
        yu : "ю",
        yU : "ю",
        yy : "ы",
        yY : "ы",
        // Compound letters:
        "тs" : "ц",
        "тS" : "ц",
        "sh" : "ш",
        "sH" : "ш",
        "сh" : "ч",
        "сH" : "ч",
        "шсh" : "щ",
        "шсH" : "щ",
        "шСh" : "щ",
        "шСH" : "щ",
        // Signs:
        qd : "ъ",
        qD : "ъ",
        qs : "ь",
        qS : "ь",
        // Accented letters:
        "è": "э",

        // Upper case letters:
        // -------------------
        A : "А",
        B : "Б",
        C : "С",
        D : "Д",
        E : "Е",
        F : "Ф",
        G : "Г",
        // No H
        I : "И",
        J : "Ж",
        K : "К",
        L : "Л",
        M : "М",
        N : "Н",
        O : "О",
        P : "П",
        // No Q
        R : "Р",
        // No S
        T : "Т",
        U : "У",
        V : "В",
        // No W
        X : "Х",
        // No Y
        Z : "З",
        // Soft vovels:
        YA : "Я",
        Ya : "Я",
        YI : "Й",
        Yi : "Й",
        YO : "Ё",
        Yo : "Ё",
        YU : "Ю",
        Yu : "Ю",
        YY : "Ы",
        Yy : "Ы",
        // Compound letters:
        "ТS" : "Ц",
        "Тs" : "Ц",
        "SH" : "Ш",
        "Sh" : "Ш",
        "СH" : "Ч",
        "Сh" : "Ч",
        "ШСH" : "Щ",
        "ШСh" : "Щ",
        "ШсH" : "Щ",
        "Шсh" : "Щ",
        // Signs:
        QD : "Ъ",
        Qd : "Ъ",
        QS : "Ь",
        Qs : "Ь",
        // Accented letters:
        "È": "Э",
    };

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

        element.addEventListener('keyup', function(e) {
            // Do nothing if one of these modifiers is pressed:
            if (e.altKey || e.ctrlKey || e.metaKey)
                return;
            // Check that nothing is selected:
            var posStart = element.selectionStart;
            var posEnd = element.selectionEnd;
            if (posStart != posEnd)
                return;
            // Apply mapping:
            var t = element.value;
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
                element.value = t.slice(0, posStart - c) + t.slice(posStart);
                element.selectionStart = posStart - c;
                element.selectionEnd = posEnd - c;
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
                element.value = t.slice(0, posStart - l) + keys.slice(0, c) + t.slice(posStart);
                element.selectionStart = posStart - l + c;
                element.selectionEnd = posEnd - l + c;
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
     */
    function searchTextFields(element) {
        for (const textArea of element.getElementsByTagName('textarea')) {
            if (textArea.getAttribute('lang') == 'ru') {
                installKeyMapper(textArea);
            }
        }

        for (const input of element.getElementsByTagName('input')) {
            if ((input.getAttribute('type') == 'text') && (input.getAttribute('lang') == 'ru')) {
                installKeyMapper(input);
            }
        }
    }

    // Search for text fields in every new node using a MutationObserver
    var bodyObserver = new MutationObserver(function(mutationRecords) {
        for (const record of mutationRecords) {
            record.addedNodes.forEach(searchTextFields);
        }
    });

    bodyObserver.observe(document.body, {
        subtree: true,
        childList: true,
    });

    // Search for text fields on body
    searchTextFields(document.body);
})();
