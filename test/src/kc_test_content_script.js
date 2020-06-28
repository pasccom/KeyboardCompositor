window.wrappedJSObject['kcTest'] = cloneInto({
    sendMessage: function(message, element) {
        console.log("Sending message", message, "to element", element);
        element.focus();
        return new window.wrappedJSObject.Promise(exportFunction((resolve, reject) => {
            browser.runtime.sendMessage("keyboard_compositor@pas.com", message).then((ans) => {
                resolve(cloneInto(ans, window));
            }, (reject) => {
                reject(cloneInto(err, window));
            });
        }, window));
    },
}, window, {cloneFunctions: true});
