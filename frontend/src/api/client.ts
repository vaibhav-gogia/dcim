export class ApiError extends Error { constructor(public status: number, message: string) { super(message); } }

const BASE_URL = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options?.method && options.method !== "GET" ? { "X-CSRF-Token": decodeURIComponent(document.cookie.split("; ").find(c => c.startsWith("dcim_csrf="))?.split("=")[1] ?? "") } : {}),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let message = `Request failed (${res.status}). Please try again.`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") message = body.detail;
      else if (Array.isArray(body.detail)) message = body.detail.map((item: { loc?: (string | number)[]; msg: string }) =>
        `${item.loc?.slice(1).join(".") ?? "Input"}: ${item.msg}`).join("; ");
    } catch { /* Keep the fallback message for non-JSON responses. */ }
    if (res.status === 401 && path !== "/auth/login") window.dispatchEvent(new Event("auth-expired"));
    throw new ApiError(res.status, message);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, headers?: Record<string, string>) =>
    request<T>(path, { method: "POST", headers, body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
