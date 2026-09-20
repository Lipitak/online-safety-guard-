// ScamShield 24/7 Chrome Extension Content Script (Manifest V3)
(function() {
  console.log("🛡️ ScamShield 24/7 Desktop Protection Active...");

  const pageUrl = window.location.href;
  const pageTitle = document.title;
  const bodyText = document.body ? document.body.innerText.slice(0, 2000) : "";
  const hasPasswordField = !!document.querySelector('input[type="password"]');
  const hasCardField = !!document.querySelector('input[name*="card"], input[id*="card"], input[name*="cvv"]');

  fetch("http://localhost:5001/detect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: `${pageTitle}. ${bodyText}`,
      url: pageUrl,
      package_name: "com.android.chrome",
      has_password_field: hasPasswordField,
      has_card_field: hasCardField,
      is_http: window.location.protocol === "http:"
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.is_scam) {
      if (data.severity === "critical") {
        console.warn("🚨 CRITICAL SCAM DETECTED: Full Page Takeover Triggered!", data);
        renderCriticalFullPageTakeover(data);
      } else {
        console.info("⚠️ MODERATE SCAM FLAGGED: Non-intrusive Top Banner Displayed.", data);
        renderModerateInlineFlag(data);
      }
    }
  })
  .catch(err => {
    console.error("ScamShield Backend Unreachable:", err);
  });

  // 1. CRITICAL SEVERITY: Full-Page Red Takeover Overlay
  function renderCriticalFullPageTakeover(data) {
    if (document.getElementById("scamShieldCriticalOverlay")) return;

    const overlay = document.createElement("div");
    overlay.id = "scamShieldCriticalOverlay";
    overlay.style.cssText = `
      position: fixed !important;
      top: 0 !important; left: 0 !important;
      width: 100vw !important; height: 100vh !important;
      background: rgba(185, 28, 28, 0.97) !important;
      z-index: 2147483647 !important;
      display: flex !important;
      flex-direction: column !important;
      align-items: center !important;
      justify-content: center !important;
      color: #ffffff !important;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
      text-align: center !important;
      padding: 30px !important;
    `;

    overlay.innerHTML = `
      <div style="font-size: 72px; margin-bottom: 12px;">🚨</div>
      <h1 style="font-size: 32px; font-weight: 800; color: #ffffff; margin-bottom: 8px; text-transform: uppercase;">
        EMERGENCY RED ALERT — CRITICAL SCAM BLOCKED
      </h1>
      <div style="font-size: 18px; font-weight: 700; color: #fde047; margin-bottom: 20px;">
        TURANT BAND KARO / IS APP KO BAND KARO / KISI KO OTP MAT BATAO
      </div>
      <p style="font-size: 15px; max-width: 640px; line-height: 1.5; color: #ffe4e4; margin-bottom: 28px;">
        <strong>Category:</strong> ${data.category.toUpperCase()}<br>
        <strong>Reason:</strong> ${data.reason}
      </p>
      <div style="display: flex; gap: 16px;">
        <button id="scamShieldExitBtn" style="
          padding: 14px 28px;
          background: #22c55e;
          color: #000000;
          border: none;
          border-radius: 12px;
          font-size: 16px;
          font-weight: 800;
          cursor: pointer;
        ">🛡️ SAFE EXIT (GO BACK)</button>
      </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById("scamShieldExitBtn").addEventListener("click", function() {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.href = "https://www.google.com";
      }
    });

    // Play Voice Warning if present
    if (data.spoken_warning && 'speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(data.spoken_warning.text_local || "Emergency Warning!");
      u.lang = data.spoken_warning.speech_lang || "en-US";
      window.speechSynthesis.speak(u);
    }
  }

  // 2. MODERATE SEVERITY: Non-Intrusive Top Banner Flag
  function renderModerateInlineFlag(data) {
    if (document.getElementById("scamShieldModerateBanner")) return;

    const banner = document.createElement("div");
    banner.id = "scamShieldModerateBanner";
    banner.style.cssText = `
      position: fixed !important;
      top: 0 !important; left: 0 !important; width: 100% !important;
      background: #1e1b4b !important;
      border-bottom: 3px solid #e8641c !important;
      color: #f3f4f6 !important;
      z-index: 2147483646 !important;
      padding: 10px 20px !important;
      display: flex !important;
      align-items: center !important;
      justify-content: space-between !important;
      font-family: -apple-system, sans-serif !important;
      font-size: 13px !important;
      box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
    `;

    banner.innerHTML = `
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="font-size: 18px;">⚠️</span>
        <div>
          <strong style="color: #f97316;">ScamShield Flag (${data.category.replace('_', ' ').toUpperCase()}):</strong> ${data.reason}
        </div>
      </div>
      <button id="scamShieldCloseBanner" style="
        background: transparent; border: none; color: #9ca3af; font-size: 18px; cursor: pointer;
      ">&times;</button>
    `;

    document.body.prepend(banner);

    document.getElementById("scamShieldCloseBanner").addEventListener("click", function() {
      banner.remove();
    });
  }
})();