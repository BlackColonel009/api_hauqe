import { APP_CONFIG } from "./config.js";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${APP_CONFIG.apiBaseUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) throw new Error(`Erreur API ${response.status}`);
  if (response.status === 204) return null;
  return response.json();
}
