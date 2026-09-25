export type Identity = {
  user: { id: string; name: string; email: string; created_at: string };
  csrf_token: string;
};

export type Page<T> = {
  data: T[];
  pagination: { has_more: boolean; next_cursor: string | null };
};

export type Organization = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  role: "OWNER" | "ADMIN" | "MANAGER" | "DEVELOPER" | "VIEWER";
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public requestId?: string,
  ) {
    super(message);
  }
}

export async function authRequest(
  action: string,
  options?: { body?: object; csrf?: string; signal?: AbortSignal },
): Promise<Identity | null> {
  const response = await fetch(`/api/v1/auth/${action}`, {
    method: action === "me" ? "GET" : "POST",
    credentials: "same-origin",
    cache: "no-store",
    signal: options?.signal,
    headers: {
      "Content-Type": "application/json",
      "X-EIP-Request": "1",
      ...(options?.csrf ? { "X-CSRF-Token": options.csrf } : {}),
    },
    body: action === "me" ? undefined : JSON.stringify(options?.body || {}),
  });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok)
    throw new ApiError(
      response.status,
      data.error?.message || "Something went wrong. Please try again.",
      data.error?.request_id,
    );
  return data as Identity;
}

export async function organizationsRequest<T>(
  path = "",
  options?: {
    method?: "GET" | "POST" | "PATCH" | "DELETE";
    body?: object;
    signal?: AbortSignal;
  },
): Promise<T> {
  const response = await fetch(`/api/v1/organizations${path}`, {
    method: options?.method || "GET",
    signal: options?.signal,
    credentials: "same-origin",
    cache: "no-store",
    headers: { "Content-Type": "application/json", "X-EIP-Request": "1" },
    body: ["POST", "PATCH"].includes(options?.method || "")
      ? JSON.stringify(options?.body || {})
      : undefined,
  });
  if (response.status === 204) return undefined as T;
  const data = await response.json();
  if (!response.ok)
    throw new ApiError(
      response.status,
      data.error?.message || "Something went wrong. Please try again.",
      data.error?.request_id,
    );
  return data as T;
}
