import Cookies from "js-cookie";

const TOKEN_KEY = "stockplane.access_token";
const USER_KEY = "stockplane.user";
const MEMBERSHIPS_KEY = "stockplane.memberships";

const SESSION_EXPIRES_DAYS = 1;

const cookieOptions = {
  path: "/",
  sameSite: "lax",
  secure: import.meta.env.PROD,
  expires: SESSION_EXPIRES_DAYS,
};

function getJsonCookie(key) {
  const raw = Cookies.get(key);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setJsonCookie(key, value) {
  Cookies.set(key, JSON.stringify(value), cookieOptions);
}

export function getToken() {
  return Cookies.get(TOKEN_KEY) ?? null;
}

function setToken(accessToken) {
  Cookies.set(TOKEN_KEY, accessToken, cookieOptions);
}

function clearToken() {
  Cookies.remove(TOKEN_KEY, { path: "/" });
}

export function getStoredUser() {
  return getJsonCookie(USER_KEY);
}

export function getMemberships() {
  const memberships = getJsonCookie(MEMBERSHIPS_KEY);
  return Array.isArray(memberships) ? memberships : [];
}

export function setSession({ accessToken, user, memberships }) {
  setToken(accessToken);
  setJsonCookie(USER_KEY, user);
  setJsonCookie(MEMBERSHIPS_KEY, memberships ?? []);
}

export function clearSession() {
  clearToken();
  Cookies.remove(USER_KEY, { path: "/" });
  Cookies.remove(MEMBERSHIPS_KEY, { path: "/" });
}

export function hasSession() {
  return Boolean(getToken());
}

export function getDefaultBusinessId() {
  const memberships = getMemberships();
  return memberships[0]?.business?.id ?? null;
}
