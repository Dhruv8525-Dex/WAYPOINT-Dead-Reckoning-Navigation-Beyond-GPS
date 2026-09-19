import type { components } from "./api-schema";
import { useEffect, useState } from "react";
const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
let workspacePassword: string | null = null;
let passwordPrompt: Promise<string | null> | null = null;
export async function authenticatedFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const request = (password: string | null) => fetch(`${apiBase}${path}`, {
    ...options,
    headers: {
      ...options.headers,
      ...(password ? { Authorization: `Basic ${btoa(`waypoint:${password}`)}` } : {}),
    },
  });
  let response = await request(workspacePassword);
  if (response.status === 401) {
    if (!passwordPrompt) {
      passwordPrompt = Promise.resolve().then(() => window.prompt("Enter your Waypoint workspace password"));
    }
    workspacePassword = await passwordPrompt;
    passwordPrompt = null;
    if (workspacePassword) response = await request(workspacePassword);
  }
  return response;
}
export async function downloadResource(path: string, filename: string) {
  const response = await authenticatedFetch(`/api/v1${path}`);
  if (!response.ok) throw new Error(`Download failed (${response.status})`);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 60000);
}
export type Project = components["schemas"]["ProjectOut"];
export type RecordItem = {
  id: string;
  kind: string;
  project_id: string;
  name: string;
  data: any;
  created_at: string;
};
export type Job = {
  id: string;
  kind: string;
  status: string;
  progress: number;
  message: string;
  config: any;
  result_id: string | null;
  created_at: string;
};
export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await authenticatedFetch(`/api/v1${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const value = await response
      .json()
      .catch(() => ({ detail: "Server unavailable" }));
    throw new Error(
      typeof value.detail === "string"
        ? value.detail
        : JSON.stringify(value.detail),
    );
  }
  return response.json();
}
export function useResource<T>(path: string | null, initial: T, interval = 0) {
  const [data, setData] = useState(initial),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(true),
    [revision, setRevision] = useState(0);
  useEffect(() => {
    if (!path) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    let alive = true;
    setLoading(true);
    const load = () =>
      api<T>(path, { signal: controller.signal })
        .then((d) => {
          if (alive) {
            setData(d);
            setError("");
          }
        })
        .catch((e) => {
          if (alive && e.name !== "AbortError") setError(e.message);
        })
        .finally(() => {
          if (alive) setLoading(false);
        });
    load();
    const timer = interval ? window.setInterval(load, interval) : undefined;
    return () => {
      alive = false;
      controller.abort();
      clearInterval(timer);
    };
  }, [path, revision, interval]);
  return { data, error, loading, refresh: () => setRevision((r) => r + 1) };
}
export const post = (path: string, body: unknown) =>
  api(path, { method: "POST", body: JSON.stringify(body) });
export const fmt = (n: number | null | undefined, d = 2) =>
  n == null
    ? "Unavailable"
    : n.toLocaleString(undefined, { maximumFractionDigits: d });
export const timeLabel = (n: number) =>
  `${Math.floor(n / 60)
    .toString()
    .padStart(2, "0")}:${Math.floor(n % 60)
    .toString()
    .padStart(2, "0")}`;
