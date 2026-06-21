import { apiRequest } from "./client";

import type {
  AgentEvent,
  SessionDetailResponse,
  SessionListResponse,
} from "../types";

export function getSessions(
  limit = 50,
): Promise<SessionListResponse> {
  return apiRequest<SessionListResponse>(
    `/api/sessions?limit=${limit}`,
  );
}

export function getSession(
  sessionId: string,
): Promise<SessionDetailResponse> {
  const encodedSessionId =
    encodeURIComponent(sessionId);

  return apiRequest<SessionDetailResponse>(
    `/api/sessions/${encodedSessionId}`,
  );
}

export function getSessionEvents(
  sessionId: string,
): Promise<AgentEvent[]> {
  const encodedSessionId =
    encodeURIComponent(sessionId);

  return apiRequest<AgentEvent[]>(
    `/api/sessions/${encodedSessionId}/events`,
  );
}