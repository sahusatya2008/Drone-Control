let telemetrySocket = null;

const MANUAL_TEXT = {
  access: "Set your API token. Any protected endpoint (real connect, controls, telemetry snapshot, mission, geofence) uses this token in X-UADIB-Token.",
  simulation: "Simulation Demo uses /system/demo/simulation. It auto-connects to the simulator endpoint, runs takeoff, captures telemetry, then lands. Use this to verify full flow quickly.",
  realConnect: "Real Drone Connect uses /system/connect with your endpoint. Supported patterns include mavlink://..., ros2://..., sdk://..., serial://... depending on adapter support.",
  cameraView: "Provide a real camera source (RTSP/HTTP/USB index), configure it, verify health, then start live view. This is intended for real drone camera streams.",
  flight: "Takeoff/land/hover/RTL are primary flight actions. Set Speed updates cruise speed. Set Yaw rotates heading in degrees. Always connect first.",
  movementCamera: "Move Delta applies relative position change (lat/lon/alt). Camera Start/Stop toggles stream state in telemetry. For physical drones, this maps to adapter commands.",
  telemetry: "Start Live Telemetry opens WebSocket /ws/telemetry and streams updates. Stop closes socket. Fetch Snapshot calls /drone/telemetry once.",
  mission: "Mission Builder sends three waypoints to /system/mission/build. Backend optimizes order and returns mission distance and ETA simulation.",
  safety: "Apply Geofence sends boundaries to /drone/geofence. Telemetry reports if position is inside fence and whether failsafe landing is recommended.",
  cameraView: "This section appears when the connected drone has camera capability. Configure source and verify health before starting live view.",
};

function byId(id) {
  return document.getElementById(id);
}

const tokenEl = byId("token");
const simSourceEl = byId("simSource");
const realSourceEl = byId("realSource");
const connProtocolEl = byId("connProtocol");
const connHostEl = byId("connHost");
const connPortEl = byId("connPort");
const connTransportEl = byId("connTransport");
const connDeviceEl = byId("connDevice");
const cameraSourceEl = byId("cameraSource");
const cameraTokenEl = byId("cameraToken");
const cameraFeedEl = byId("cameraFeed");
const cameraCardEl = byId("cameraCard");

function tokenHeader() {
  return { "X-UADIB-Token": tokenEl.value || "changeme" };
}

function showJson(el, data) {
  el.textContent = JSON.stringify(data, null, 2);
}

function showError(el, err) {
  el.textContent = typeof err === "string" ? err : JSON.stringify(err, null, 2);
}

function showFacilities(facilities = []) {
  const facilitiesListEl = byId("facilitiesList");
  facilitiesListEl.innerHTML = "";
  facilities.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    facilitiesListEl.appendChild(li);
  });
}

function setCameraCardVisibility(data = {}) {
  if (!cameraCardEl) return;
  const caps = data.capabilities || data.dashboard?.capabilities || {};
  const cameraAvailable = Boolean(caps.camera_control || data.profile?.camera);
  cameraCardEl.classList.toggle("hidden", !cameraAvailable);
}

function extractHostFromSource(source = "") {
  try {
    if (!source) return "";
    if (source.startsWith("mavlink://")) {
      const tail = source.replace("mavlink://", "");
      const parts = tail.split(":");
      return parts.length >= 2 ? parts[1] : "";
    }
    if (source.startsWith("sdk://")) {
      return source.replace("sdk://", "").split(":")[0];
    }
    if (source.startsWith("udp://") || source.startsWith("tcp://")) {
      return source.split("://")[1]?.split(":")[0] || "";
    }
    return "";
  } catch {
    return "";
  }
}

function inferCameraSourceFromConnection(data = {}) {
  if (cameraSourceEl.value.trim()) return cameraSourceEl.value.trim();
  const host = extractHostFromSource(data.resolved_source || data.endpoint?.source || realSourceEl.value || "");
  if (!host) return "";
  // Common defaults used by many drone gateways/camera bridges.
  return `rtsp://${host}:8554/live`;
}

function deriveFacilities(data = {}) {
  if (Array.isArray(data.facilities) && data.facilities.length > 0) {
    return data.facilities;
  }

  const caps = data.capabilities || data.dashboard?.capabilities || {};
  const facilities = [
    "Automatic protocol detection and adapter selection",
    "Drone profile extraction and capability mapping",
    "Dynamic dashboard generation",
    "REST + WebSocket control and telemetry",
  ];

  if (caps.navigation) facilities.push("Navigation and GPS operations");
  if (caps.camera_control) facilities.push("Camera control and stream operations");
  if (caps.waypoint_navigation) facilities.push("Waypoint mission planning");
  if (caps.obstacle_avoidance) facilities.push("Obstacle monitoring/avoidance");
  if (caps.mission_builder) facilities.push("Mission optimization and simulation");
  if (caps.realtime_telemetry) facilities.push("Real-time telemetry visualization");

  return facilities;
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw data;
  }
  return data;
}

async function runDemo() {
  const output = byId("demoResult");
  try {
    const data = await requestJson("/system/demo/simulation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: simSourceEl.value }),
    });
    showJson(output, data.demo_flow || data);
    showJson(byId("dashboardBox"), data.dashboard || {});
    showFacilities(deriveFacilities(data));
    setCameraCardVisibility(data);
  } catch (err) {
    showError(output, err);
  }
}

async function connectDemoOnly() {
  const output = byId("demoResult");
  try {
    const data = await requestJson("/system/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...tokenHeader() },
      body: JSON.stringify({ source: simSourceEl.value }),
    });
    showJson(output, data);
    showJson(byId("dashboardBox"), data.dashboard || {});
    showFacilities(deriveFacilities(data));
    setCameraCardVisibility(data);
  } catch (err) {
    showError(output, err);
  }
}

async function connectReal() {
  const output = byId("connectResult");
  try {
    const data = await requestJson("/system/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...tokenHeader() },
      body: JSON.stringify({ source: realSourceEl.value }),
    });
    showJson(output, data);
    if (data.dashboard) {
      showJson(byId("dashboardBox"), data.dashboard);
    }
    showFacilities(deriveFacilities(data));
    setCameraCardVisibility(data);
    await autoEnableCameraIfAvailable(data);
  } catch (err) {
    showError(output, err);
  }
}

async function connectRealDetails() {
  const output = byId("connectResult");
  const protocol = connProtocolEl.value;
  const host = connHostEl.value.trim();
  const payload = {
    protocol,
    host,
    port: Number(connPortEl.value),
    transport: connTransportEl.value.trim(),
    device: connDeviceEl.value.trim(),
    topic: protocol === "ros2" && host ? host : "",
    camera_source: cameraSourceEl.value.trim() || null,
  };
  if (!payload.device) delete payload.device;
  if (!payload.topic) delete payload.topic;
  if (!payload.camera_source) delete payload.camera_source;

  try {
    const data = await requestJson("/system/connect/details", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...tokenHeader() },
      body: JSON.stringify(payload),
    });
    showJson(output, data);
    realSourceEl.value = data.resolved_source || realSourceEl.value;
    if (data.dashboard) {
      showJson(byId("dashboardBox"), data.dashboard);
    }
    showFacilities(deriveFacilities(data));
    setCameraCardVisibility(data);
    await autoEnableCameraIfAvailable(data);
  } catch (err) {
    showError(output, err);
  }
}

async function autoEnableCameraIfAvailable(data = {}) {
  const output = byId("cameraResult");
  const hasCamera = Boolean(data.profile?.camera || data.capabilities?.camera_control || data.dashboard?.capabilities?.camera_control);
  if (!hasCamera) {
    showJson(output, { status: "skipped", reason: "Connected drone reported no camera capability" });
    return;
  }

  const inferred = inferCameraSourceFromConnection(data);
  if (!inferred) {
    showJson(output, { status: "pending", message: "Camera capability detected. Please provide camera source and click Configure Camera Source." });
    return;
  }

  cameraSourceEl.value = inferred;
  await configureCamera();
  await cameraHealth();
  startCameraView();
}

async function refreshDashboard() {
  const output = byId("connectResult");
  try {
    const data = await requestJson("/system/dashboard", {
      method: "GET",
      headers: tokenHeader(),
    });
    showJson(byId("dashboardBox"), data);
    showFacilities(deriveFacilities(data));
    setCameraCardVisibility(data);
    showJson(output, { status: "ok", dashboard_refreshed: true });
  } catch (err) {
    showError(output, err);
  }
}

async function command(path, payload = {}, resultBoxId = "flightResult") {
  const output = byId(resultBoxId);
  try {
    const data = await requestJson(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...tokenHeader() },
      body: JSON.stringify(payload),
    });
    showJson(output, data);
  } catch (err) {
    showError(output, err);
  }
}

async function runPreflight() {
  const output = byId("preflightResult");
  try {
    const data = await requestJson("/drone/preflight", {
      method: "GET",
      headers: tokenHeader(),
    });
    showJson(output, data);
    return data;
  } catch (err) {
    showError(output, err);
    return { ok: false };
  }
}

function parseWaypoint(raw) {
  const [lat, lon, alt] = raw.split(",").map((x) => Number(x.trim()));
  if (!Number.isFinite(lat) || !Number.isFinite(lon) || !Number.isFinite(alt)) {
    throw new Error(`Invalid waypoint format: ${raw}`);
  }
  return { lat, lon, alt };
}

async function buildMission() {
  const output = byId("missionResult");
  try {
    const waypoints = [parseWaypoint(byId("wp1").value), parseWaypoint(byId("wp2").value), parseWaypoint(byId("wp3").value)];
    const data = await requestJson("/system/mission/build", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...tokenHeader() },
      body: JSON.stringify({ waypoints }),
    });
    showJson(output, data);
  } catch (err) {
    showError(output, err.message || err);
  }
}

async function setGeofence() {
  const output = byId("safetyResult");
  const payload = {
    min_lat: Number(byId("minLat").value),
    max_lat: Number(byId("maxLat").value),
    min_lon: Number(byId("minLon").value),
    max_lon: Number(byId("maxLon").value),
  };
  await command("/drone/geofence", payload, "safetyResult");
}

async function telemetrySnapshot() {
  const output = byId("telemetryBox");
  try {
    const data = await requestJson("/drone/telemetry", {
      method: "GET",
      headers: tokenHeader(),
    });
    showJson(output, data);
  } catch (err) {
    showError(output, err);
  }
}

async function configureCamera() {
  const output = byId("cameraResult");
  try {
    const data = await requestJson("/system/camera/configure", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...tokenHeader() },
      body: JSON.stringify({ source: cameraSourceEl.value.trim() }),
    });
    showJson(output, data);
  } catch (err) {
    showError(output, err);
  }
}

async function cameraHealth() {
  const output = byId("cameraResult");
  try {
    const data = await requestJson("/system/camera/health", {
      method: "GET",
      headers: tokenHeader(),
    });
    showJson(output, data);
  } catch (err) {
    showError(output, err);
  }
}

function startCameraView() {
  const token = (cameraTokenEl.value || tokenEl.value || "changeme").trim();
  const src = `/system/camera/stream?token=${encodeURIComponent(token)}&t=${Date.now()}`;
  cameraFeedEl.src = src;
  cameraFeedEl.classList.remove("hidden");
}

function stopCameraView() {
  cameraFeedEl.src = "";
  cameraFeedEl.classList.add("hidden");
}

function startTelemetry() {
  const output = byId("telemetryBox");
  if (telemetrySocket) {
    telemetrySocket.close();
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  telemetrySocket = new WebSocket(`${protocol}://${window.location.host}/ws/telemetry`);
  telemetrySocket.onmessage = (event) => {
    try {
      showJson(output, JSON.parse(event.data));
    } catch {
      output.textContent = event.data;
    }
  };
  telemetrySocket.onclose = () => {
    telemetrySocket = null;
  };
}

function stopTelemetry() {
  if (telemetrySocket) {
    telemetrySocket.close();
    telemetrySocket = null;
  }
}

function renderManual(targetId, key) {
  const el = byId(targetId);
  el.textContent = MANUAL_TEXT[key] || "Manual not available.";
  el.classList.toggle("hidden");
}

function initManualButtons() {
  document.querySelectorAll(".manual-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-manual");
      const targetId = `${key}Manual`;
      renderManual(targetId, key);
    });
  });
}

byId("runDemo").addEventListener("click", runDemo);
byId("connectDemoOnly").addEventListener("click", connectDemoOnly);
byId("connectReal").addEventListener("click", connectReal);
byId("connectRealDetails").addEventListener("click", connectRealDetails);
byId("refreshDashboard").addEventListener("click", refreshDashboard);

byId("preflightBtn").addEventListener("click", runPreflight);
byId("takeoffBtn").addEventListener("click", async () => {
  const pre = await runPreflight();
  if (!pre.ok) {
    showError(byId("flightResult"), { detail: "Preflight failed. Resolve issues before takeoff." });
    return;
  }
  command("/drone/takeoff", { payload: { altitude_m: Number(byId("takeoffAlt").value) } }, "flightResult");
});
byId("landBtn").addEventListener("click", () => command("/drone/land", { payload: {} }, "flightResult"));
byId("hoverBtn").addEventListener("click", () => command("/drone/hover", {}, "flightResult"));
byId("rtlBtn").addEventListener("click", () => command("/drone/rtl", {}, "flightResult"));
byId("setSpeedBtn").addEventListener("click", () => command("/drone/set_speed", { speed_mps: Number(byId("speedVal").value) }, "flightResult"));
byId("setYawBtn").addEventListener("click", () => command("/drone/yaw", { yaw_deg: Number(byId("yawVal").value) }, "flightResult"));

byId("moveBtn").addEventListener("click", () => command("/drone/move", {
  delta_lat: Number(byId("deltaLat").value),
  delta_lon: Number(byId("deltaLon").value),
  delta_alt: Number(byId("deltaAlt").value),
}, "movementResult"));
byId("cameraStartBtn").addEventListener("click", () => command("/drone/camera/start", {}, "movementResult"));
byId("cameraStopBtn").addEventListener("click", () => command("/drone/camera/stop", {}, "movementResult"));

byId("startWs").addEventListener("click", startTelemetry);
byId("stopWs").addEventListener("click", stopTelemetry);
byId("pullTelemetry").addEventListener("click", telemetrySnapshot);

byId("buildMissionBtn").addEventListener("click", buildMission);
byId("setGeofenceBtn").addEventListener("click", setGeofence);
byId("cameraConfigure").addEventListener("click", configureCamera);
byId("cameraHealth").addEventListener("click", cameraHealth);
byId("cameraStartView").addEventListener("click", startCameraView);
byId("cameraStopView").addEventListener("click", stopCameraView);

initManualButtons();
