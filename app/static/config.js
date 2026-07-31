/**
 * Configuration frontend HAUQE Certif.
 *
 * L'API utilise la même origine que l'interface.
 * En local comme en production, le navigateur appelle ainsi le serveur qui
 * lui a réellement fourni l'application, sans port interne codé en dur.
 */
export const APP_CONFIG = Object.freeze({
  apiBaseUrl: window.location.origin,
  apiPrefix: "/api/v1",
  defaultRoute: "dashboard",
  appName: "HAUQE Certif",
  requestTimeoutMs: 15000,
});
