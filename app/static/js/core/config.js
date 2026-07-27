/**
 * Configuration frontend HAUQE Certif.
 *
 * API locale actuellement utilisée pendant l'intégration.
 * En production, remplacer uniquement `apiBaseUrl`.
 */
export const APP_CONFIG = Object.freeze({
  apiBaseUrl: "http://localhost:8001",
  apiPrefix: "/api/v1",
  defaultRoute: "dashboard",
  appName: "HAUQE Certif",
  requestTimeoutMs: 15000,
});
