/** Modular API client for Hermes Dashboard */

export { fetchJSON, getSessionToken } from "./http";
export type { FetchJSONOptions } from "./types";

export { authApi, getWsTicket, buildWsAuthParam, buildWsUrl } from "./auth";
export { sessionsApi } from "./sessions";

// Re-export types
export type {
  StatusResponse,
  AuthMeResponse,
  SessionInfo,
  PaginatedSessions,
  SessionMessagesResponse,
  ModelInfo,
  EnvVarInfo,
  CronJob,
} from "./types";
