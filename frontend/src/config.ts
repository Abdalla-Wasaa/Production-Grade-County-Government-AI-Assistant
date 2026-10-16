export interface PublicConfig {
  apiBaseUrl: string;
}

export function readPublicConfig(environment: { VITE_API_BASE_URL?: string }): PublicConfig {
  const value = environment.VITE_API_BASE_URL ?? '/api/v1';
  // Same-origin API paths only. No origins, credentials, queries or fragments.
  if (!/^\/api(?:\/[a-zA-Z0-9_-]+)*$/.test(value)) {
    throw new Error('Invalid public API configuration.');
  }
  return { apiBaseUrl: value };
}
