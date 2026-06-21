import { apiRequest } from "./client";

import type {
  DemoResetResponse,
} from "../types";

export function resetDemoData():
  Promise<DemoResetResponse> {
  return apiRequest<DemoResetResponse>(
    "/api/demo/reset",
    {
      method: "POST",
    },
  );
}