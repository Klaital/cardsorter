import { OpenAPI } from '../generated/api';

/**
 * Configure the generated API client
 * Call this early in your app initialization
 */
export function configureApiClient(baseUrl: string, token?: string) {
  OpenAPI.BASE = baseUrl;
  OpenAPI.TOKEN = token;
  // Include credentials for CORS requests
  OpenAPI.WITH_CREDENTIALS = true;
}

/**
 * Update the authentication token
 * Call this after login/logout
 */
export function setApiToken(token: string | undefined) {
  OpenAPI.TOKEN = token;
}
