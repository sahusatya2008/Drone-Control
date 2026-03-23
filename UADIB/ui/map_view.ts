export type GPSPoint = { lat: number; lon: number; alt?: number };

export function toGeoJSONPath(points: GPSPoint[]) {
  return {
    type: "Feature",
    geometry: {
      type: "LineString",
      coordinates: points.map((p) => [p.lon, p.lat, p.alt ?? 0]),
    },
    properties: {},
  };
}
