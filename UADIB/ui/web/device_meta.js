function browserFallbackConfig() {
  return {
    hostname: window.location.hostname || "local-device",
    os: navigator.userAgentData?.platform || navigator.platform || "UnknownOS",
    architecture: "browser-runtime",
    user_agent: navigator.userAgent || "unknown",
    cpu_count: navigator.hardwareConcurrency || "n/a",
  };
}

function stableBrowserDeviceId() {
  const existing = localStorage.getItem("uadib_device_id");
  if (existing) return existing;

  const seed = [
    navigator.userAgent || "",
    navigator.platform || "",
    navigator.language || "",
    String(navigator.hardwareConcurrency || ""),
    Intl.DateTimeFormat().resolvedOptions().timeZone || "",
  ].join("|");

  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash << 5) - hash + seed.charCodeAt(i);
    hash |= 0;
  }
  const value = `UADIB-BR-${Math.abs(hash).toString(16).toUpperCase().padStart(8, "0")}`;
  localStorage.setItem("uadib_device_id", value);
  return value;
}

async function loadDeviceMeta() {
  const el = document.getElementById("deviceMeta");
  if (!el) return;

  try {
    let response = await fetch("/system/device");
    let data = await response.json().catch(() => ({}));

    if (!response.ok || !data.device_id) {
      response = await fetch("/api/system/device");
      data = await response.json().catch(() => ({}));
    }

    const cfg = data.configuration || browserFallbackConfig();
    const deviceId = data.device_id || stableBrowserDeviceId();
    el.innerHTML = `
      <div><b>Device ID:</b> ${deviceId}</div>
      <div><b>Host:</b> ${cfg.hostname || window.location.hostname || "local-device"}</div>
      <div><b>OS:</b> ${cfg.os || navigator.platform || "UnknownOS"} ${cfg.architecture || ""}</div>
    `;
  } catch {
    const cfg = browserFallbackConfig();
    el.innerHTML = `
      <div><b>Device ID:</b> ${stableBrowserDeviceId()}</div>
      <div><b>Host:</b> ${cfg.hostname}</div>
      <div><b>OS:</b> ${cfg.os} ${cfg.architecture}</div>
    `;
  }
}

loadDeviceMeta();
