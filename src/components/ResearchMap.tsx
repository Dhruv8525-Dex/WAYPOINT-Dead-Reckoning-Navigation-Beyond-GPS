import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
export const methodColors: Record<string, string> = {
  reference: "#8c9a80",
  inertial: "#bc775b",
  ekf: "#b19a4c",
  ml: "#2d7055",
};
export function ResearchMap({
  paths,
  current = 0,
  visible,
}: {
  paths: Record<string, { lat: (number | null)[]; lng: (number | null)[] }>;
  current?: number;
  visible?: Record<string, boolean>;
}) {
  const el = useRef<HTMLDivElement>(null),
    map = useRef<L.Map | null>(null),
    group = useRef<L.LayerGroup | null>(null),
    last = useRef("");
  useEffect(() => {
    if (!el.current) return;
    const instance = L.map(el.current, { zoomControl: true }).setView(
      [12.97, 77.59],
      12,
    );
    map.current = instance;
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(instance);
    group.current = L.layerGroup().addTo(instance);
    const observer = new ResizeObserver(() => instance.invalidateSize());
    observer.observe(el.current);
    return () => {
      observer.disconnect();
      instance.remove();
      map.current = null;
      last.current = "";
    };
  }, []);
  useEffect(() => {
    const g = group.current,
      m = map.current;
    if (!g || !m) return;
    g.clearLayers();
    let bounds: L.LatLngTuple[] = [];
    for (const [key, path] of Object.entries(paths)) {
      if (visible?.[key] === false) continue;
      const points: L.LatLngTuple[] = [];
      const step = Math.max(1, Math.floor(path.lat.length / 2000));
      for (let i = 0; i < path.lat.length; i += step) {
        if (path.lat[i] != null && path.lng[i] != null)
          points.push([path.lat[i]!, path.lng[i]!]);
      }
      if (points.length) {
        L.polyline(points, {
          color: methodColors[key] || "#467a5b",
          weight: key === "reference" ? 3 : 2,
          opacity: 0.8,
          dashArray: key === "reference" ? "5 6" : undefined,
        }).addTo(g);
        bounds.push(...points);
        const index = Math.min(current, path.lat.length - 1);
        if (path.lat[index] != null && path.lng[index] != null)
          L.circleMarker([path.lat[index]!, path.lng[index]!], {
            radius: 5,
            color: methodColors[key],
            fillOpacity: 1,
          }).addTo(g);
      }
    }
    const signature = Object.entries(paths)
      .map(
        ([k, v]) =>
          `${k}:${v.lat.length}:${v.lat[0]}:${v.lat[v.lat.length - 1]}`,
      )
      .join("|");
    if (bounds.length && signature !== last.current) {
      m.fitBounds(L.latLngBounds(bounds), { padding: [30, 30], maxZoom: 17 });
      last.current = signature;
    }
  }, [paths, current, visible]);
  return (
    <div
      className="research-map"
      ref={el}
      aria-label="Recorded and estimated navigation trajectories"
    />
  );
}
