document.addEventListener("DOMContentLoaded", function() {
  const guardToggle = document.getElementById("guardToggle");
  const statusText = document.getElementById("statusText");
  const pulseDot = document.getElementById("pulseDot");
  const scanBtn = document.getElementById("scanCurrentBtn");
  const resultBox = document.getElementById("scanResult");

  guardToggle.addEventListener("change", function() {
    if (this.checked) {
      statusText.textContent = "24/7 GUARD ACTIVE";
      statusText.style.color = "#34c759";
      pulseDot.style.background = "#34c759";
      pulseDot.style.boxShadow = "0 0 10px #34c759";
    } else {
      statusText.textContent = "GUARD PAUSED";
      statusText.style.color = "#ff9500";
      pulseDot.style.background = "#ff9500";
      pulseDot.style.boxShadow = "none";
    }
  });

  scanBtn.addEventListener("click", async function() {
    scanBtn.disabled = true;
    scanBtn.textContent = "Scanning Active Tab...";
    resultBox.style.display = "block";
    resultBox.textContent = "🔍 Requesting AI Threat Analysis...";

    try {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        if (!tabs || !tabs[0]) {
          resultBox.textContent = "⚠️ Could not read active tab.";
          scanBtn.disabled = false;
          scanBtn.textContent = "🔍 Scan Active Page Now";
          return;
        }

        const activeTab = tabs[0];
        fetch("http://localhost:5001/analyze-page", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: activeTab.url,
            title: activeTab.title,
            text: "User requested manual tab security audit."
          })
        })
        .then(res => res.json())
        .then(data => {
          if (data.verdict === "Scam") {
            resultBox.style.borderColor = "#ff3b30";
            resultBox.innerHTML = `<b style="color:#ff3b30">🚨 SCAM THREAT DETECTED!</b><br>${data.reason}`;
          } else {
            resultBox.style.borderColor = "#34c759";
            resultBox.innerHTML = `<b style="color:#34c759">✅ Page Appears Safe</b><br>${activeTab.url}`;
          }
        })
        .catch(err => {
          resultBox.textContent = "⚠️ Server Offline. Make sure app.py is running on port 5001.";
        })
        .finally(() => {
          scanBtn.disabled = false;
          scanBtn.textContent = "🔍 Scan Active Page Now";
        });
      });
    } catch (e) {
      resultBox.textContent = "Error scanning tab: " + e.message;
      scanBtn.disabled = false;
      scanBtn.textContent = "🔍 Scan Active Page Now";
    }
  });
});
