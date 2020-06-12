console.log("Coucou from background!");

function menuItemClicked(frameId, targetElementId, mapping)
{
    console.log("Clicked[" + mapping + "]: ", targetElementId);
    if (mapping)
        browser.tabs.executeScript({ // TODO notify content script instead and remove permissions
            frameId: frameId,
            code: `browser.menus.getTargetElement(${targetElementId}).setAttribute('kc-lang', '${mapping}');`,
        });
    else
        browser.tabs.executeScript({ // TODO notify content script instead and remove permissions
            frameId: frameId,
            code: `browser.menus.getTargetElement(${targetElementId}).removeAttribute('kc-lang');`,
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
                title: mapping,
                type: 'radio',
                contexts: ['editable'],
                onclick: function(info) {
                    if (info.editable)
                        menuItemClicked(info.frameId, info.targetElementId, mapping);
                },
            }, function() {
                if (browser.runtime.lastError) {
                    console.log("error creating item '" + mapping + "':" + browser.runtime.lastError);
                } else {
                    console.log("item created successfully");
                }
            }),
            mapping: mapping,
        });
    }

    browser.menus.onShown.addListener((info) => {
        browser.tabs.executeScript({ // TODO ask content script instead and remove permissions
            frameId: info.frameId,
            code: `[browser.menus.getTargetElement(${info.targetElementId}).getAttribute('lang'),
                    browser.menus.getTargetElement(${info.targetElementId}).getAttribute('kc-lang')];`,
        }).then((attributeArray) => {
            Promise.all(kcMenuItems.map((menuItemInfo) => {
                if (!menuItemInfo.mapping)
                    return browser.menus.update(menuItemInfo.id, {
                        title: attributeArray[0][0] ? "Default (" + attributeArray[0][0] + ")" : "None",
                        checked: menuItemInfo.mapping == attributeArray[0][1],
                    });
                else
                    return browser.menus.update(menuItemInfo.id, {
                        checked: menuItemInfo.mapping == attributeArray[0][1],
                    });
            })).then(() => {
                browser.menus.refresh();
            });
        });
    });
}

fetch(browser.runtime.getURL("mappings/list.json"), {method: "GET"})
        .then((response) => response.json())
        .then((list) => {installMappings(list);})
        .catch((error) => {console.error(error);});
