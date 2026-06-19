/** HTTP utilities for Hermes API client */

import type { FetchJSONOptions } from "./types";

const BASE = typeof window !== "undefined" ? (window.__HERMES_BASE_PATH__ ?? "") : "";

export async function fetchJSON<T>(
  url: string,
  init?: RequestInit,
  options?: FetchJSONOptions,
): Promise<T> {
  const headers = new Headers(init?.headers);
  const token = typeof window !== "undefined" ? window.__HERMES_SESSION_TOKEN__ : undefined;
  if (token) {
    headers.set("X-Hermes-Session-Token", token);
  }
  
  const res = await fetch(`${BASE}${url}`, {
    ...init,
    headers,
    credentials: init?.credentials ?? "include",
  });
  
  if (!res.ok) {
    if (res.status === 401 && !options?.allowUnauthorized) {
      throw new Error("Unauthorized");
    }
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  
  return res.json();
}

export async function getSessionToken(): Promise<string> {
  if (typeof window === "undefined") {
    throw new Error("Session token only available in browser");
  }
  return window.__HERMES_SESSION_TOKEN__ ?? "";
}
