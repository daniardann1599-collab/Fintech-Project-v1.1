import { APP_ROUTES } from "./config.js";
import { apiRequest } from "./api.js";
import { clearSession, getSession, saveSession } from "./storage.js";

export async function registerUser({ email, password, role = "CUSTOMER" }) {
  return apiRequest("/register", {
    method: "POST",
    body: { email, password, role },
    auth: false,
  });
}

export async function loginWithPassword(email, password) {
  const tokenPayload = await apiRequest("/auth/token", {
    method: "POST",
    body: { username: email, password },
    form: true,
    auth: false,
  });

  saveSession({ token: tokenPayload.access_token, user: null, customerId: null });
  const user = await apiRequest("/auth/me");
  saveSession({ token: tokenPayload.access_token, user, customerId: null });
  return { token: tokenPayload.access_token, user };
}

export async function syncCurrentUser() {
  const session = getSession();
  if (!session?.token) return null;

  const user = await apiRequest("/auth/me");
  saveSession({ ...session, user });
  return { ...session, user };
}

export async function requireAuth(role = null) {
  const session = getSession();
  if (!session?.token) {
    window.location.href = APP_ROUTES.login;
    return null;
  }

  let latestSession = session;
  try {
    latestSession = (await syncCurrentUser()) || session;
  } catch {
    clearSession();
    window.location.href = APP_ROUTES.login;
    return null;
  }

  if (role && latestSession.user?.role !== role) {
    window.location.href = latestSession.user?.role === "ADMIN" ? APP_ROUTES.admin : APP_ROUTES.customer;
    return null;
  }

  return latestSession;
}

export function redirectByRole(role) {
  window.location.href = role === "ADMIN" ? APP_ROUTES.admin : APP_ROUTES.customer;
}

export function logout() {
  clearSession();
  window.location.href = APP_ROUTES.login;
}
