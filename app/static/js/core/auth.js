/**
 * Orchestrateur Authentification frontend.
 *
 * Ne contient aucune règle d'autorisation métier : l'autorité reste FastAPI.
 * Le frontend utilise seulement les permissions reçues pour masquer/afficher
 * des actions, jamais pour décider souverainement qu'une opération est permise.
 */

import {
  ApiError,
  apiGet,
  apiPost,
  clearAccessToken,
  getAccessToken,
  hasAccessToken,
  setAccessToken,
} from "./api.js";

const CURRENT_USER_CACHE_KEY = "hauqe-current-user-cache";

function extractToken(payload) {
  if (!payload || typeof payload !== "object") return null;

  return (
    payload.access_token
    || payload.token
    || payload.jeton
    || payload.bearer_token
    || payload.session_token
    || null
  );
}

function cacheCurrentUser(user) {
  try {
    sessionStorage.setItem(
      CURRENT_USER_CACHE_KEY,
      JSON.stringify(user || null)
    );
  } catch {}
}

export function getCachedCurrentUser() {
  try {
    return JSON.parse(
      sessionStorage.getItem(CURRENT_USER_CACHE_KEY) || "null"
    );
  } catch {
    return null;
  }
}

export function clearCurrentUserCache() {
  try { sessionStorage.removeItem(CURRENT_USER_CACHE_KEY); } catch {}
}

export async function login({
  email,
  password,
  remember = false,
}) {
  /*
   * Le backend historique peut exposer `password` ou `mot_de_passe`.
   * On tente d'abord le contrat standard `password`.
   * Uniquement en cas de 422 Pydantic, on réessaie avec `mot_de_passe`.
   * Cela évite d'envoyer deux champs de mot de passe à la fois.
   */
  let payload;

  try {
    payload = await apiPost(
      "/api/v1/auth/login",
      {
        email,
        password,
      },
      {
        auth: false,
        suppressGlobalAuth: true,
      }
    );
  } catch (error) {
    if (!(error instanceof ApiError) || error.status !== 422) {
      throw error;
    }

    payload = await apiPost(
      "/api/v1/auth/login",
      {
        email,
        mot_de_passe: password,
      },
      {
        auth: false,
        suppressGlobalAuth: true,
      }
    );
  }

  if (payload?.mfa_required) {
    return {
      mfaRequired: true,
      challengeToken: payload.challenge_token,
      expiresAt: payload.expires_at || null,
      raw: payload,
    };
  }

  const token = extractToken(payload);
  if (!token) {
    throw new Error(
      "La connexion a réussi mais aucun Bearer token n'a été reçu."
    );
  }

  setAccessToken(token, { persistent: remember });

  const user = await getCurrentUser({ force: true });

  return {
    mfaRequired: false,
    user,
    raw: payload,
  };
}

export async function verifyMfaLogin({
  challengeToken,
  codeOrRecovery,
  remember = false,
}) {
  const payload = await apiPost(
    "/api/v1/auth/mfa/verify",
    {
      challenge_token: challengeToken,
      code_or_recovery: codeOrRecovery,
    },
    {
      auth: false,
      suppressGlobalAuth: true,
    }
  );

  const token = extractToken(payload);
  if (!token) {
    throw new Error(
      "Le MFA a été validé mais aucun Bearer token n'a été reçu."
    );
  }

  setAccessToken(token, { persistent: remember });

  const user = await getCurrentUser({ force: true });

  return {
    user,
    raw: payload,
  };
}

export async function getCurrentUser({ force = false } = {}) {
  if (!hasAccessToken()) return null;

  if (!force) {
    const cached = getCachedCurrentUser();
    if (cached) return cached;
  }

  const user = await apiGet("/api/v1/me");
  cacheCurrentUser(user);
  return user;
}

export async function getCurrentProfile({ force = false } = {}) {
  if (!hasAccessToken()) return null;

  const cacheKey = "hauqe-current-profile-cache";

  if (!force) {
    try {
      const cached = JSON.parse(
        sessionStorage.getItem(cacheKey) || "null"
      );
      if (cached) return cached;
    } catch {}
  }

  const profile = await apiGet("/api/v1/me/profile");

  try {
    sessionStorage.setItem(cacheKey, JSON.stringify(profile));
  } catch {}

  return profile;
}

export function clearProfileCache() {
  try {
    sessionStorage.removeItem("hauqe-current-profile-cache");
  } catch {}
}

export async function logout() {
  const token = getAccessToken();

  try {
    if (token) {
      await apiPost(
        "/api/v1/auth/logout",
        null,
        {
          suppressGlobalAuth: true,
        }
      );
    }
  } finally {
    clearAccessToken();
    clearCurrentUserCache();
    clearProfileCache();
  }
}

export function hasPermission(permissionCode, user = null) {
  const source = user || getCachedCurrentUser();
  const permissions = source?.permissions || [];
  return Array.isArray(permissions)
    && permissions.includes(permissionCode);
}

export function hasAnyPermission(permissionCodes, user = null) {
  return permissionCodes.some(
    (code) => hasPermission(code, user)
  );
}

export function hasRole(roleCode, user = null) {
  const source = user || getCachedCurrentUser();
  const roles = source?.roles || [];
  return Array.isArray(roles) && roles.includes(roleCode);
}
