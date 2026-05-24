import { ApiError, apiFetch } from "./api";

export type UserRole = "customer" | "provider";

export type AuthUser = {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  birth_date: string | null;
  role: UserRole;
  sms_2fa_enabled?: boolean;
  totp_configured?: boolean;
  date_joined: string;
};

type LoginSuccessResponse = {
  requires_2fa: false;
  access: string;
  refresh: string;
  user: AuthUser;
};

type LoginTwoFactorResponse = {
  requires_2fa: true;
  pre_auth_token: string;
  available_2fa_methods: string[];
  detail?: string;
};

export type LoginResponse = LoginSuccessResponse | LoginTwoFactorResponse;

type RegisterPayload = {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role?: UserRole;
};

type TokenPairResponse = {
  access: string;
  refresh: string;
  user: AuthUser;
};

export type TwoFactorStatus = {
  sms_2fa_enabled: boolean;
  totp_configured: boolean;
  available_2fa_methods: string[];
};

export type TotpSetupResponse = {
  secret: string;
  provisioning_uri: string;
};

const LEGACY_ACCESS = "carepath_access";
const LEGACY_REFRESH = "carepath_refresh";
const LEGACY_USER = "carepath_user";
const ACCESS_KEY = "bithealth_access";
const REFRESH_KEY = "bithealth_refresh";
const USER_KEY = "bithealth_user";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function migrateStorageKeys(): void {
  if (!isBrowser()) return;
  const pairs: [string, string][] = [
    [LEGACY_ACCESS, ACCESS_KEY],
    [LEGACY_REFRESH, REFRESH_KEY],
    [LEGACY_USER, USER_KEY],
  ];
  for (const [legacy, next] of pairs) {
    const value = localStorage.getItem(legacy);
    if (value && !localStorage.getItem(next)) {
      localStorage.setItem(next, value);
      localStorage.removeItem(legacy);
    }
  }
}

migrateStorageKeys();

export const AUTH_PUBLIC_PATHS = ["/login", "/sign-up", "/forgot-password"] as const;

export function isAuthPublicPath(pathname: string): boolean {
  return (AUTH_PUBLIC_PATHS as readonly string[]).includes(pathname);
}

/** Provider dashboard routes (/provider, /provider/schedule, …) — not marketplace /providers/:id */
export function isProviderDashboardPath(pathname: string): boolean {
  return pathname === "/provider" || pathname.startsWith("/provider/");
}

export function getStoredAccessToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getStoredRefreshToken(): string | null {
  if (!isBrowser()) return null;
  return localStorage.getItem(REFRESH_KEY);
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

export function getRoleHome(role: UserRole): string {
  return role === "provider" ? "/provider" : "/";
}

export async function login(identifier: string, password: string): Promise<LoginResponse> {
  const data = await apiFetch<LoginResponse>("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
    skipAuth: true,
  });

  if (!data.requires_2fa) {
    persistSession(data.access, data.refresh, data.user);
  }

  return data;
}

export async function completeTwoFactorLogin(
  preAuthToken: string,
  method: "sms" | "totp",
  code: string,
): Promise<AuthUser> {
  const challenge = await apiFetch<{ detail?: string; otp_code?: string }>(
    "/api/auth/2fa/challenge/",
    {
      method: "POST",
      body: JSON.stringify({ pre_auth_token: preAuthToken, method }),
      skipAuth: true,
    },
  );

  const verifyPath =
    method === "sms" ? "/api/auth/2fa/sms/verify-login/" : "/api/auth/2fa/totp/verify-login/";
  const data = await apiFetch<TokenPairResponse>(verifyPath, {
    method: "POST",
    body: JSON.stringify({ pre_auth_token: preAuthToken, code }),
    skipAuth: true,
  });

  persistSession(data.access, data.refresh, data.user);
  return data.user;
}

export async function register(payload: RegisterPayload): Promise<AuthUser> {
  await apiFetch<AuthUser>("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuth: true,
  });
  const result = await login(payload.email, payload.password);
  if (result.requires_2fa) {
    throw new ApiError("Two-factor authentication required after registration.", 200, result);
  }
  persistSession(result.access, result.refresh, result.user);
  return result.user;
}

export async function fetchMe(token?: string): Promise<AuthUser> {
  return apiFetch<AuthUser>("/api/auth/me/", { token });
}

export async function logout(): Promise<void> {
  if (!isBrowser()) return;
  const refresh = getStoredRefreshToken();
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

export async function requestPasswordReset(phoneNumber: string): Promise<{ otp_code?: string }> {
  return apiFetch("/api/auth/password-reset/request/", {
    method: "POST",
    body: JSON.stringify({ phone_number: phoneNumber }),
    skipAuth: true,
  });
}

export async function confirmPasswordReset(
  phoneNumber: string,
  otp: string,
  newPassword: string,
): Promise<void> {
  await apiFetch("/api/auth/password-reset/confirm/", {
    method: "POST",
    body: JSON.stringify({ phone_number: phoneNumber, otp, new_password: newPassword }),
    skipAuth: true,
  });
}

export async function fetchTwoFactorStatus(): Promise<TwoFactorStatus> {
  return apiFetch<TwoFactorStatus>("/api/auth/2fa/status/");
}

export async function setTwoFactorMethod(
  method: "sms" | "totp",
  enabled: boolean,
): Promise<TwoFactorStatus> {
  return apiFetch<TwoFactorStatus>("/api/auth/2fa/method/", {
    method: "POST",
    body: JSON.stringify({ method, enabled }),
  });
}

export async function setupTotp(): Promise<TotpSetupResponse> {
  return apiFetch<TotpSetupResponse>("/api/auth/2fa/totp/setup/", { method: "POST" });
}

export async function confirmTotpSetup(code: string): Promise<void> {
  await apiFetch("/api/auth/2fa/totp/confirm/", {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export async function disableTwoFactor(password: string): Promise<void> {
  await apiFetch("/api/auth/2fa/disable/", {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export async function startTwoFactorChallenge(
  preAuthToken: string,
  method: "sms" | "totp",
): Promise<{ otp_code?: string }> {
  return apiFetch("/api/auth/2fa/challenge/", {
    method: "POST",
    body: JSON.stringify({ pre_auth_token: preAuthToken, method }),
    skipAuth: true,
  });
}

export async function verifyTwoFactorLogin(
  preAuthToken: string,
  method: "sms" | "totp",
  code: string,
): Promise<AuthUser> {
  const verifyPath =
    method === "sms" ? "/api/auth/2fa/sms/verify-login/" : "/api/auth/2fa/totp/verify-login/";
  const data = await apiFetch<TokenPairResponse>(verifyPath, {
    method: "POST",
    body: JSON.stringify({ pre_auth_token: preAuthToken, code }),
    skipAuth: true,
  });
  persistSession(data.access, data.refresh, data.user);
  return data.user;
}
