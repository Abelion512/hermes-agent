/** Session management API */

import { fetchJSON } from "./http";
import type {
  PaginatedSessions,
  SessionMessagesResponse,
  SessionLatestDescendantResponse,
  SessionStoreStats,
} from "./types";

export const sessionsApi = {
  getSessions: (limit = 20, offset = 0) =>
    fetchJSON<PaginatedSessions>(`/api/sessions?limit=${limit}&offset=${offset}`),

  getSessionMessages: (id: string) =>
    fetchJSON<SessionMessagesResponse>(`/api/sessions/${encodeURIComponent(id)}/messages`),

  getSessionLatestDescendant: (id: string) =>
    fetchJSON<SessionLatestDescendantResponse>(
      `/api/sessions/${encodeURIComponent(id)}/latest-descendant`,
    ),

  deleteSession: (id: string) =>
    fetchJSON<{ ok: boolean }>(`/api/sessions/${encodeURIComponent(id)}`, {
      method: "DELETE",
    }),

  getEmptySessionsCount: () =>
    fetchJSON<{ count: number }>("/api/sessions/empty/count"),

  deleteEmptySessions: () =>
    fetchJSON<{ ok: boolean; deleted: number }>("/api/sessions/empty", {
      method: "DELETE",
    }),

  bulkDeleteSessions: (ids: string[]) =>
    fetchJSON<{ ok: boolean; deleted: number }>("/api/sessions/bulk-delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids }),
    }),

  renameSession: (id: string, title: string) =>
    fetchJSON<{ ok: boolean; title: string }>(
      `/api/sessions/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      },
    ),

  getSessionStats: () => fetchJSON<SessionStoreStats>("/api/sessions/stats"),

  exportSessionUrl: (id: string) =>
    `/api/sessions/${encodeURIComponent(id)}/export`,

  pruneSessions: (older_than_days: number, source?: string) =>
    fetchJSON<{ ok: boolean; removed: number }>("/api/sessions/prune", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ older_than_days, source }),
    }),
};
