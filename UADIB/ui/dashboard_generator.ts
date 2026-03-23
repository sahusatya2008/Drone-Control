export type DroneCapabilities = {
  navigation: boolean;
  camera_control: boolean;
  waypoint_navigation: boolean;
  obstacle_avoidance: boolean;
  payload_control: boolean;
  mission_builder: boolean;
  realtime_telemetry: boolean;
};

export type DashboardWidget = {
  id: string;
  type: string;
  title: string;
  position: { x: number; y: number; w: number; h: number };
};

export function generateDashboard(capabilities: DroneCapabilities): DashboardWidget[] {
  const widgets: DashboardWidget[] = [
    { id: "hud", type: "flight_hud", title: "Flight HUD", position: { x: 0, y: 0, w: 6, h: 4 } },
    { id: "battery", type: "battery", title: "Battery", position: { x: 6, y: 0, w: 2, h: 2 } },
  ];

  if (capabilities.navigation) {
    widgets.push({ id: "map", type: "map", title: "Map Navigation", position: { x: 0, y: 4, w: 5, h: 4 } });
  }
  if (capabilities.camera_control) {
    widgets.push({ id: "camera", type: "camera", title: "Camera View", position: { x: 5, y: 4, w: 3, h: 4 } });
  }
  if (capabilities.waypoint_navigation) {
    widgets.push({ id: "planner", type: "mission_planner", title: "Mission Planner", position: { x: 0, y: 8, w: 8, h: 4 } });
  }
  if (capabilities.obstacle_avoidance) {
    widgets.push({ id: "obstacle", type: "obstacle_monitor", title: "Obstacle Monitor", position: { x: 8, y: 0, w: 4, h: 4 } });
  }

  return widgets;
}
