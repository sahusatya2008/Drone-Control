(() => {
  "use strict";

  const blockedKeys = new Set([
    "F12",
  ]);

  function prevent(e) {
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();
    return false;
  }

  // Block mouse-based inspection/copy workflows.
  document.addEventListener("contextmenu", prevent, true);
  document.addEventListener("dblclick", prevent, true);
  document.addEventListener("copy", prevent, true);
  document.addEventListener("cut", prevent, true);
  document.addEventListener("paste", prevent, true);
  document.addEventListener("selectstart", prevent, true);
  document.addEventListener("dragstart", prevent, true);

  // Block common keyboard shortcuts for devtools/source/print/save/copy/paste.
  document.addEventListener("keydown", (e) => {
    const key = e.key.toUpperCase();
    if (blockedKeys.has(key)) {
      return prevent(e);
    }

    const ctrl = e.ctrlKey || e.metaKey;
    const shift = e.shiftKey;

    if (ctrl && ["C", "V", "X", "U", "S", "P"].includes(key)) {
      return prevent(e);
    }
    if (ctrl && shift && ["I", "J", "C", "K"].includes(key)) {
      return prevent(e);
    }
    return true;
  }, true);

  // Basic devtools-open deterrence.
  const overlay = document.createElement("div");
  overlay.style.cssText = [
    "position:fixed",
    "inset:0",
    "z-index:99999",
    "display:none",
    "align-items:center",
    "justify-content:center",
    "background:#020617",
    "color:#e2e8f0",
    "font:600 18px/1.4 sans-serif",
    "text-align:center",
    "padding:24px",
  ].join(";");
  overlay.textContent = "Security lock active. Inspection and copying are restricted.";
  document.addEventListener("DOMContentLoaded", () => document.body.appendChild(overlay));

  let tripped = false;
  setInterval(() => {
    const threshold = 160;
    const widthGap = window.outerWidth - window.innerWidth;
    const heightGap = window.outerHeight - window.innerHeight;
    const opened = widthGap > threshold || heightGap > threshold;

    if (opened) {
      tripped = true;
      overlay.style.display = "flex";
      document.body.style.filter = "blur(8px)";
      document.body.style.pointerEvents = "none";
    } else if (!opened && !tripped) {
      overlay.style.display = "none";
      document.body.style.filter = "";
      document.body.style.pointerEvents = "";
    }
  }, 700);
})();
