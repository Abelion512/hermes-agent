/** Shared types for Hermes API client */

export interface StatusResponse {
  status: string;
  version?: string;
}

export interface AuthMeResponse {
  user?: {
    id: string;
    name: string;
    email?: string;
  };
  session?: {
    id: string;
    expires_at?: string;
  };
}

export interface SessionInfo {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface PaginatedSessions {
  sessions: SessionInfo[];
  total: number;
  limit: number;
  offset: number;
}

export interface SessionMessagesResponse {
  messages: Array<{
    role: string;
    content: string;
    timestamp?: string;
  }>;
}

export interface SessionLatestDescendantResponse {
  id: string;
  title: string;
}

export interface ModelInfo {
  name: string;
  provider: string;
  context_window?: number;
}

export interface ModelInfoResponse {
  current: ModelInfo;
  available: ModelInfo[];
}

export interface ModelOptionsResponse {
  models: ModelInfo[];
}

export interface AuxiliaryModelsResponse {
  auxiliary: ModelInfo[];
}

export interface ModelAssignmentRequest {
  model: string;
  provider?: string;
}

export interface ModelAssignmentResponse {
  ok: boolean;
  model: ModelInfo;
}

export interface EnvVarInfo {
  value?: string;
  is_secret?: boolean;
  source?: string;
}

export interface CronJob {
  id: string;
  name: string;
  schedule: string;
  prompt: string;
  profile: string;
  enabled: boolean;
}

export interface CronDeliveryTarget {
  id: string;
  type: string;
  config: Record<string, unknown>;
}

export interface AnalyticsResponse {
  data: Array<{
    date: string;
    requests: number;
    tokens: number;
    cost: number;
  }>;
}

export interface ModelsAnalyticsResponse {
  data: Array<{
    model: string;
    requests: number;
    tokens: number;
  }>;
}

export interface LogsResponse {
  logs: Array<{
    timestamp: string;
    level: string;
    component: string;
    message: string;
  }>;
}

export interface SessionStoreStats {
  total_sessions: number;
  empty_sessions: number;
  total_messages: number;
}

export interface FetchJSONOptions {
  allowUnauthorized?: boolean;
}
