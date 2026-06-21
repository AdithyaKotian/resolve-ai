export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL ?? "ws://127.0.0.1:8000";

interface ErrorResponse {
  detail?: string;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);

    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,

    headers: {
      Accept: "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorMessage = "The backend request failed.";

    try {
      const errorResponse =
        (await response.json()) as ErrorResponse;

      if (errorResponse.detail) {
        errorMessage = errorResponse.detail;
      }
    } catch {
      // Keep the safe generic message when the response is not JSON.
    }

    throw new ApiError(errorMessage, response.status);
  }

  return (await response.json()) as T;
}