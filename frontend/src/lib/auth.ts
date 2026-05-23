import { apiFetch } from "./api";

export type UserRole = "customer" | "provider";

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  birth_date: string | null;
  role: UserRole;
  date_joined: string;
};

type LoginResponse = {
  access: string;
  refresh: string;
  user: AuthUser;
};

type RegisterPayload = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: UserRole;
};

const ACCESS_KEY = "carepath_access";
const REFRESH_KEY = "carepath_refresh";
const USER_KEY = "carepath_user";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export const AUTH_PUBLIC_PATHS = ["/login", "/sign-up"] as const;

export function isAuthPublicPath(pathname: string): boolean {
  return (AUTH_PUBLIC_PATHS as readonly string[]).includes(pathname);
}

export function getStoredAccessToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (!isBrowser()) return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function persistSession(access: string, refresh: string, user: AuthUser): void {
  if (!isBrowser()) return;
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await apiFetch<LoginResponse>("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  persistSession(data.access, data.refresh, data.user);
  return data.user;
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  await apiFetch<AuthUser>("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return login(payload.email, payload.password);
}

export async function fetchMe(token: string): Promise<AuthUser> {
  return apiFetch<AuthUser>("/api/auth/me/", { token });
}

export async function logout(): Promise<void> {
  if (!isBrowser()) return;
  const refresh = localStorage.getItem(REFRESH_KEY);
  if (refresh) {
    try {
      await apiFetch("/api/auth/logout/", {
        method: "POST",
        body: JSON.stringify({ refresh }),
      });
    } catch {
      // Clear local session even if server logout fails.
    }
  }
  clearSession();
}
