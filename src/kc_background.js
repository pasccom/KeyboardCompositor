function menuItemClicked(frameId, targetElementId, mapping)
{
    console.log("Clicked[" + mapping + "]: ", targetElementId);

    browser.tabs.query({
        active: true,
        currentWindow: true,
    }).then((tabs) => {
        if (mapping)
            browser.tabs.sendMessage(tabs[0].id, {
                'command': "SET_LANG",
                'elementId': targetElementId,
                'lang': mapping,
            });
        else
            browser.tabs.sendMessage(tabs[0].id, {
                'command': "REMOVE_LANG",
                'elementId': targetElementId,
            });
    });
}

function installMappings(list) {
    var kcMenuItems = [{
        id: browser.menus.create({
            title: "None",
            type: 'radio',
            checked: true,
            contexts: ['editable'],
            onclick: function(info) {
                if (info.editable)
                    menuItemClicked(info.frameId, info.targetElementId, null);
            },
        }, function() {
            if (browser.runtime.lastError) {
                console.log("error creating item 'none':" + browser.runtime.lastError);
            } else {
                console.log("item created successfully");
            }
        }),
        mapping: null,
    }];

    for (const mapping of list) {
        kcMenuItems.push({
            id: browser.menus.create({
                title: mapping.name,
                type: 'radio',
                contexts: ['editable'],
                onclick: function(info) {
                    if (info.editable)
                        menuItemClicked(info.frameId, info.targetElementId, mapping.code);
                },
            }, function() {
                if (browser.runtime.lastError) {
                    console.log("error creating item '" + mapping.code + "':" + browser.runtime.lastError);
                } else {
                    console.log("item created successfully");
                }
            }),
            mapping: mapping.code,
        });
    }

    browser.menus.onShown.addListener((info) => {
        browser.tabs.query({
            active: true,
            currentWindow: true,
        }).then((tabs) => {
            browser.tabs.sendMessage(tabs[0].id, {
                'command': "GET_LANG",
                'elementId': info.targetElementId,
            }, {frameId: info.frameId}).then((attributeArray) => {
                Promise.all(kcMenuItems.map((menuItemInfo) => {
                    if (!menuItemInfo.mapping) {
                        var mapping = list.find((e) => (e.code == attributeArray[0]));
                        return browser.menus.update(menuItemInfo.id, {
                            title: mapping ? "Default (" + mapping.name + ")" : "None",
                            checked: menuItemInfo.mapping == attributeArray[1],
                        });
                    } else {
                        return browser.menus.update(menuItemInfo.id, {
                            checked: menuItemInfo.mapping == attributeArray[1],
                        });
                    }
                })).then(() => {
                    browser.menus.refresh();
                });
            });
        });
    });

    browser.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
        console.log("Got external message:", message);
        return browser.tabs.query({
            active: true,
            currentWindow: true,
        }).then((tabs) => browser.tabs.sendMessage(tabs[0].id, message));
    });
}

fetch(browser.runtime.getURL("mappings/list.json"), {method: "GET"})
        .then((response) => response.json())
        .then((list) => {installMappings(list);})
        .catch((error) => {console.error(error);});
