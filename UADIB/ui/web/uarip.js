function byId(id) {
  return document.getElementById(id);
}

function showJson(id, data) {
  byId(id).textContent = JSON.stringify(data, null, 2);
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw data;
  }
  return data;
}

byId("loadOverview").addEventListener("click", async () => {
  const data = await requestJson("/uarip/overview");
  showJson("overviewBox", data);
});

byId("inferProtocol").addEventListener("click", async () => {
  const lines = byId("packetHex").value.split("\n").map((v) => v.trim()).filter(Boolean);
  const data = await requestJson("/uarip/protocol/infer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ packets_hex: lines }),
  });
  showJson("protocolBox", data);
});

byId("buildGraph").addEventListener("click", async () => {
  const payload = {
    navigation: byId("capNav").checked,
    camera_control: byId("capCam").checked,
    waypoint_navigation: byId("capWay").checked,
    obstacle_avoidance: byId("capObs").checked,
    payload_control: byId("capPayload").checked,
  };
  const data = await requestJson("/uarip/capability/graph", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  showJson("graphBox", data);
});

byId("runSwarm").addEventListener("click", async () => {
  const agents = JSON.parse(byId("swarmJson").value);
  const data = await requestJson("/uarip/swarm/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agents }),
  });
  showJson("swarmBox", data);
});

byId("listProviders").addEventListener("click", async () => {
  const data = await requestJson("/uarip/simulation/providers");
  showJson("simBox", data);
});

byId("launchSim").addEventListener("click", async () => {
  const data = await requestJson("/uarip/simulation/launch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ provider: "PyBullet", scenario: "urban-swarm" }),
  });
  showJson("simBox", data);
});

byId("runAnomaly").addEventListener("click", async () => {
  const signal = byId("signalInput").value.split(",").map((x) => Number(x.trim())).filter((x) => Number.isFinite(x));
  const data = await requestJson("/uarip/security/anomaly", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ signal }),
  });
  showJson("securityBox", data);
});
