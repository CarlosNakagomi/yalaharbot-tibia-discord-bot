const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
export const API_BASE_URL = configuredBaseUrl.replace(/\/$/, '');

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export function apiFetch(path, options = {}) {
  return fetch(apiUrl(path), { ...options, credentials: 'include' });
}
