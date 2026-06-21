import { apiRequest } from "./client";
import type { BackendHealth } from "../types";

export function getBackendHealth(): Promise<BackendHealth> {
  return apiRequest<BackendHealth>("/api/health");
}