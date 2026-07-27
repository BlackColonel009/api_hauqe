/**
 * Client API central HAUQE Certif.
 *
 * Responsabilités :
 * - préfixe API commun ;
 * - stockage du Bearer token ;
 * - envoi JSON ;
 * - gestion homogène 401/403/409/422/423/5xx ;
 * - extraction des messages FastAPI ;
 * - événements globaux pour le shell et le verrouillage.
 *
 * Règle importante :
 * aucune page métier ne doit appeler fetch() directement pour une API privée.
 */

import { APP_CONFIG } from "./config.js";

const SESSION_TOKEN_KEY = "hauqe-access-token";
const PERSISTENT_TOKEN_KEY = "hauqe-access-token-persistent";
const AUTH_EVENT = "hauqe:auth-state";
const LOCK_EVENT = "hauqe:session-locked";

export class ApiError extends Error {
  constructor(message, status = 0, detail = null, response = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.response = response;
  }
}

function storageAvailable(storage) {
  try {
    const key = "__hauqe_test__";
    storage.setItem(key, "1");
    storage.removeItem(key);
    return true;
  } catch {
    return false;
  }
}

export function setAccessToken(token, { persistent = false } = {}) {
  clearAccessToken();
  if (!token) return;

  const target = persistent && storageAvailable(localStorage)
    ? localStorage
    : sessionStorage;

  target.setItem(
    persistent ? PERSISTENT_TOKEN_KEY : SESSION_TOKEN_KEY,
    token
  );

  window.dispatchEvent(new CustomEvent(AUTH_EVENT, {
    detail: { authenticated: true }
  }));
}

export function getAccessToken() {
  return (
    sessionStorage.getItem(SESSION_TOKEN_KEY)
    || localStorage.getItem(PERSISTENT_TOKEN_KEY)
    || null
  );
}

export function hasAccessToken() {
  return Boolean(getAccessToken());
}

export function clearAccessToken() {
  try { sessionStorage.removeItem(SESSION_TOKEN_KEY); } catch {}
  try { localStorage.removeItem(PERSISTENT_TOKEN_KEY); } catch {}

  window.dispatchEvent(new CustomEvent(AUTH_EVENT, {
    detail: { authenticated: false }
  }));
}

function normalizePath(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;

  const base = String(APP_CONFIG.apiBaseUrl || window.location.origin)
    .replace(/\/+$/, "");

  if (path.startsWith("/")) return `${base}${path}`;
  return `${base}/${path}`;
}

export function apiUrl(path) {
  return normalizePath(path);
}

async function parseResponseBody(response) {
  if (response.status === 204) return null;

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try { return await response.json(); } catch { return null; }
  }

  try {
    const text = await response.text();
    return text || null;
  } catch {
    return null;
  }
}

export function extractApiMessage(payload, fallback = "Une erreur est survenue.") {
  if (!payload) return fallback;

  if (typeof payload === "string") return payload;

  if (typeof payload.detail === "string") return payload.detail;

  if (payload.detail && typeof payload.detail === "object") {
    if (typeof payload.detail.message === "string") {
      return payload.detail.message;
    }
    if (typeof payload.detail.code === "string") {
      return payload.detail.code;
    }
  }

  if (Array.isArray(payload.detail)) {
    const first = payload.detail[0];
    if (first?.msg) return first.msg;
  }

  if (typeof payload.message === "string") return payload.message;

  return fallback;
}

function isAuthRoute() {
  const route = location.hash.replace(/^#\/?/, "").split("/")[0];
  return ["connexion", "mot-de-passe-oublie"].includes(route);
}

function handleGlobalStatus(status, payload) {
  if (status === 401) {
    clearAccessToken();

    if (!isAuthRoute()) {
      sessionStorage.setItem(
        "hauqe-return-after-login",
        location.hash || "#/dashboard"
      );
      location.hash = "#/connexion";
    }
    return;
  }

  if (status === 423) {
    window.dispatchEvent(new CustomEvent(LOCK_EVENT, {
      detail: payload?.detail || payload || {}
    }));
  }
}

/**
 * apiRequest(path, options)
 *
 * options spécifiques :
 * - auth=false         : requête publique
 * - body=<object>      : JSON automatiquement sérialisé
 * - timeoutMs=15000    : timeout réseau
 * - suppressGlobalAuth : ne pas rediriger automatiquement sur 401
 */
export async function apiRequest(path, options = {}) {
  const {
    auth = true,
    body,
    timeoutMs = APP_CONFIG.requestTimeoutMs || 15000,
    suppressGlobalAuth = false,
    headers: customHeaders = {},
    ...fetchOptions
  } = options;

  const headers = new Headers(customHeaders);
  const token = getAccessToken();

  if (auth && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let requestBody = body;
  const isFormData = body instanceof FormData;

  if (body !== undefined && body !== null && !isFormData) {
    if (typeof body !== "string") {
      requestBody = JSON.stringify(body);
    }
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
  }

  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response;
  try {
    response = await fetch(normalizePath(path), {
      ...fetchOptions,
      headers,
      body: requestBody,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timer);

    if (error?.name === "AbortError") {
      throw new ApiError(
        "Le serveur met trop de temps à répondre.",
        0,
        { code: "NETWORK_TIMEOUT" }
      );
    }

    throw new ApiError(
      "Impossible de joindre le serveur.",
      0,
      { code: "NETWORK_ERROR", cause: String(error) }
    );
  }

  clearTimeout(timer);

  const payload = await parseResponseBody(response);

  if (!response.ok) {
    if (!suppressGlobalAuth) {
      handleGlobalStatus(response.status, payload);
    }

    const fallbackByStatus = {
      400: "Requête invalide.",
      401: "Authentification requise.",
      403: "Vous n'avez pas l'autorisation nécessaire.",
      404: "Ressource introuvable.",
      409: "Cette opération entre en conflit avec l'état actuel.",
      422: "Certaines informations sont invalides.",
      423: "Votre session est verrouillée.",
      500: "Erreur interne du serveur.",
      503: "Service temporairement indisponible.",
    };

    throw new ApiError(
      extractApiMessage(
        payload,
        fallbackByStatus[response.status] || `Erreur API ${response.status}.`
      ),
      response.status,
      payload?.detail ?? payload,
      response
    );
  }

  return payload;
}


export async function apiBlob(path, options = {}) {
  const {
    auth = true,
    timeoutMs = APP_CONFIG.requestTimeoutMs || 15000,
    suppressGlobalAuth = false,
    headers: customHeaders = {},
    ...fetchOptions
  } = options;

  const headers = new Headers(customHeaders);
  const token = getAccessToken();

  if (auth && token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response;

  try {
    response = await fetch(normalizePath(path), {
      ...fetchOptions,
      method: fetchOptions.method || "GET",
      headers,
      signal: controller.signal,
    });
  } catch (error) {
    clearTimeout(timer);

    if (error?.name === "AbortError") {
      throw new ApiError(
        "Le serveur met trop de temps à répondre.",
        0,
        { code: "NETWORK_TIMEOUT" }
      );
    }

    throw new ApiError(
      "Impossible de joindre le serveur.",
      0,
      { code: "NETWORK_ERROR", cause: String(error) }
    );
  }

  clearTimeout(timer);

  if (!response.ok) {
    let payload = null;
    try {
      payload = await response.json();
    } catch {
      try {
        payload = await response.text();
      } catch {}
    }

    if (!suppressGlobalAuth) {
      handleGlobalStatus(response.status, payload);
    }

    throw new ApiError(
      extractApiMessage(payload, `Erreur API ${response.status}.`),
      response.status,
      payload?.detail ?? payload,
      response
    );
  }

  return response.blob();
}

export function apiGet(path, options = {}) {
  return apiRequest(path, { ...options, method: "GET" });
}

export function apiPost(path, body, options = {}) {
  return apiRequest(path, { ...options, method: "POST", body });
}

export function apiPatch(path, body, options = {}) {
  return apiRequest(path, { ...options, method: "PATCH", body });
}

export function apiDelete(path, options = {}) {
  return apiRequest(path, { ...options, method: "DELETE" });
}

export function describeApiError(error) {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      message: error.message,
      detail: error.detail,
    };
  }
  return {
    status: 0,
    message: error?.message || "Erreur inattendue.",
    detail: null,
  };
}
