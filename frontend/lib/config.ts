/**
 * Runtime configuration for the frontend
 * 
 * This module provides access to runtime configuration that is injected
 * by the server at runtime (not at build time). This allows the same
 * Docker image to work on different hosts/IPs without rebuilding.
 */

// Type definitions for runtime config
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      apiUrl: string;
    };
  }
}

/**
 * Get the API URL at runtime from the server-injected config
 * 
 * Priority:
 * 1. Server-injected runtime config (window.__RUNTIME_CONFIG__)
 * 2. Build-time NEXT_PUBLIC_API_URL (backwards compatibility)
 * 3. Default fallback (http://localhost:8000)
 * 
 * @returns The API URL to use for backend requests
 */
export function getApiUrl(): string {
  // Client-side: use the server-injected config
  if (typeof window !== 'undefined' && window.__RUNTIME_CONFIG__?.apiUrl) {
    return window.__RUNTIME_CONFIG__.apiUrl;
  }
  
  // Build-time fallback (backwards compatibility)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Default fallback for development
  return 'http://localhost:8000';
}

/**
 * Configuration object with helper methods
 */
export const config = {
  getApiUrl,
};
