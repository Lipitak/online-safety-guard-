function render(x) {
  const wrap = document.createElement("div");
  if (x == null || x === "") return wrap;
  if (typeof x === "string" || typeof x === "number") {
    const p = document.createElement("p");
    p.textContent = x;
    wrap.appendChild(p);
  } else if (Array.isArray(x)) {
    const ul = document.createElement("ul");
    x.forEach(i => {
      const li = document.createElement("li");
      li.textContent = typeof i === "object" ? JSON.stringify(i) : i;
      ul.appendChild(li);
    });
    wrap.appendChild(ul);
  } else if (typeof x === "object") {
    Object.entries(x).forEach(([k, v]) => {
      const h = document.createElement("h3");
      h.textContent = k.replace(/_/g, " ");
      wrap.appendChild(h);
      wrap.appendChild(render(v));
    });
  }
  return wrap;
}

chrome.storage.local.get("lastScam", ({ lastScam }) => {
  const out = document.getElementById("out");
  out.textContent = "";
  if (!lastScam) { out.textContent = "Koi data nahi mila."; return; }

  const top = document.createElement("div");
  top.className = "box";
  top.appendChild(render("Page: " + (lastScam.url || "")));
  top.appendChild(render("Risk: " + Math.round((lastScam.confidence || 0) * 100) + "%"));
  top.appendChild(render(lastScam.reason));
  out.appendChild(top);

  if (lastScam.dom_reasons && lastScam.dom_reasons.length) {
    out.appendChild(render({ "page me kya suspicious tha": lastScam.dom_reasons }));
  }
  if (lastScam.url_check && lastScam.url_check.risk_note) {
    out.appendChild(render({ "link ki problem": lastScam.url_check.risk_note }));
  }
  if (lastScam.remediation) {
    out.appendChild(render({ "ab kya karo / solution": lastScam.remediation }));
  }
});