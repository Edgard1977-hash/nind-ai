// Empty string means "same origin" (nginx or the CRA dev proxy). Never fall back to a hosted preview URL.
export function getBackendUrl() {
  const raw = (process.env.REACT_APP_BACKEND_URL || "").trim();
  return raw.replace(/\/$/, "");
}

export const BACKEND_URL = getBackendUrl();
export const API = `${BACKEND_URL}/api`;
