import { apiRequest } from "./client";

import type {
  ChatRequest,
  ChatResponse,
} from "../types";

export function sendChatMessage(
  payload: ChatRequest,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/api/chat", {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify(payload),
  });
}