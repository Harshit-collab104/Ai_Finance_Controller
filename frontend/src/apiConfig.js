/**
 * Resilient Multi-Host API Fetch Helper
 * Automatically tries 127.0.0.1:8000, localhost:8000, and current hostname:8000
 * to ensure CORS / IPv4 / IPv6 host differences never block API calls in the browser.
 */
export async function apiFetch(endpoint, options = {}) {
  const currentHost = window.location.hostname || '127.0.0.1';
  
  const hostCandidates = Array.from(new Set([
    `http://127.0.0.1:8000${endpoint}`,
    `http://localhost:8000${endpoint}`,
    `http://${currentHost}:8000${endpoint}`
  ]));

  let lastError = null;

  for (const url of hostCandidates) {
    try {
      const res = await fetch(url, options);
      if (res.ok) {
        return res;
      }
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error(`Unable to connect to backend at ${endpoint}`);
}
