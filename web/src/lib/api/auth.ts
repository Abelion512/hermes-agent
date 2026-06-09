/** Authentication API */

import { fetchJSON, getSessionToken } from "./http";
import type { AuthMeResponse, StatusResponse } from "./types";

export const authApi = {
  getStatus: () => fetchJSON<StatusResponse>("/api/status"),

  getAuthMe: () =>
    fetchJSON<AuthMeResponse>("/api/auth/me", undefined, {
      allowUnauthorized: true,
    }),

  logout: async () => {
    const res = await fetch("/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    if (typeof window !== "undefined") {
      window.location.assign("/login");
    }
    return res;
  },
};

export async function getWsTicket(): Promise<{ ticket: string; ttl_seconds: number }> {
  return fetchJSON("/api/auth/ws-ticket");
}

export async function buildWsAuthParam(): Promise<[string, string]> {
  const token = await getSessionToken();
  if (token) {
    return ["token", token];
  }
  const { ticket } = await getWsTicket();
  return ["ticket", ticket];
}

export async function buildWsUrl(endpoint: string): Promise<string> {
  const [param, value] = await buildWsAuthParam();
  const protocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = typeof window !== "undefined" ? window.location.host : "localhost";
  const basePath = typeof window !== "undefined" ? (window.__HERMES_BASE_PATH__ ?? "") : "";
  return `${protocol}//${host}${basePath}${endpoint}?${param}=${encodeURIComponent(value)}`;
}
