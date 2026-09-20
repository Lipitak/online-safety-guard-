const API = "http://localhost:5001";

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "SCAN_PAGE") {
    fetch(API + "/analyze-page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(msg.payload)
    })
      .then(r => r.json())
      .then(data => sendResponse({ ok: true, data }))
      .catch(err => sendResponse({ ok: false, error: String(err) }));
    return true;
  }

  if (msg.type === "OPEN_EXPLAIN") {
    chrome.storage.local.set({ lastScam: msg.data }, () => {
      chrome.tabs.create({ url: chrome.runtime.getURL("explain.html") });
    });
    sendResponse({ ok: true });
  }
});