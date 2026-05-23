import {
  clearSession,
  getStoredAccessToken,
  getStoredRefreshToken,
  persistSession,
  type AuthUser,
} from "./auth";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

function formatApiErrorMessage(data: unknown): string | undefined {
  if (!data || typeof data !== "object") return undefined;
  const record = data as Record<string, unknown>;
  if (typeof record.detail === "string") return record.detail;
  if (Array.isArray(record.detail)) {
    return record.detail.map(String).join(" ");
  }
  const parts: string[] = [];
  for (const [key, value] of Object.entries(record)) {
    if (Array.isArray(value)) {
      parts.push(`${key}: ${value.map(String).join(", ")}`);
    } else if (typeof value === "string") {
      parts.push(`${key}: ${value}`);
    }
  }
  return parts.length > 0 ? parts.join(". ") : undefined;
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getStoredRefreshToken();
  if (!refresh) return null;

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const response = await fetch(buildApiUrl("/api/auth/refresh/"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        });
        const text = await response.text();
        const data = text ? (JSON.parse(text) as Record<string, unknown>) : null;
        if (!response.ok || !data?.access) {
          clearSession();
          return null;
        }
        const access = String(data.access);
        const nextRefresh = data.refresh ? String(data.refresh) : refresh;
        const userRaw = localStorage.getItem("bithealth_user");
        const user = userRaw ? (JSON.parse(userRaw) as AuthUser) : null;
        if (user) persistSession(access, nextRefresh, user);
        else {
          localStorage.setItem("bithealth_access", access);
          localStorage.setItem("bithealth_refresh", nextRefresh);
        }
        return access;
      } catch {
        clearSession();
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

function redirectToLogin(): void {
  if (typeof window === "undefined") return;
  const redirect = window.location.pathname + window.location.search;
  if (redirect.startsWith("/login") || redirect.startsWith("/sign-up")) return;
  window.location.href = `/login?redirect=${encodeURIComponent(redirect)}`;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { token?: string | null; skipAuth?: boolean } = {},
): Promise<T> {
  const { token, skipAuth, headers, ...rest } = options;
  const authToken = skipAuth ? null : (token ?? getStoredAccessToken());

  async function doFetch(bearer: string | null): Promise<Response> {
    return fetch(buildApiUrl(path), {
      ...rest,
      headers: {
        ...(rest.body ? { "Content-Type": "application/json" } : {}),
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...headers,
      },
    });
  }

  let response = await doFetch(authToken);

  if (response.status === 401 && !skipAuth && authToken) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      response = await doFetch(newToken);
    } else {
      redirectToLogin();
      throw new ApiError("Session expired. Please sign in again.", 401, null);
    }
  }

  const text = await response.text();
  const data = text ? (JSON.parse(text) as unknown) : null;

  if (!response.ok) {
    const message = formatApiErrorMessage(data) ?? response.statusText;
    throw new ApiError(message, response.status, data);
  }

  return data as T;
}

export { API_BASE_URL };
