/**
 * Axios API client with JWT interceptors, auto-refresh, retry, and error handling
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { toast } from "react-hot-toast";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Extract base URL (without /api/v1) for warm-up
const BASE_URL = API_URL.replace(/\/api\/v1\/?$/, "");

let tokenUpdateCallback: ((access: string, refresh: string) => void) | null = null;
let logoutCallback: (() => void) | null = null;

export function registerAuthCallbacks(
  onTokenUpdate: (access: string, refresh: string) => void,
  onLogout: () => void
) {
  tokenUpdateCallback = onTokenUpdate;
  logoutCallback = onLogout;
}

export const api = axios.create({
  baseURL: API_URL,
  timeout: 60_000, // 60s — Render cold starts can take 30–50s
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// ─── Auto-retry with exponential backoff for cold start recovery ─────────────
let _retryCount = 0;
const MAX_RETRIES = 3;

api.interceptors.response.use(
  (response) => {
    _retryCount = 0; // Reset on success
    return response;
  },
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig & { _retryAttempt?: number };
    
    // Only retry on network errors or timeouts (cold start symptoms)
    const isRetryable =
      !error.response && // No response = network error or timeout
      (error.code === "ECONNABORTED" || error.code === "ERR_NETWORK" || error.message?.includes("timeout"));

    if (isRetryable && config && (config._retryAttempt || 0) < MAX_RETRIES) {
      config._retryAttempt = (config._retryAttempt || 0) + 1;
      const delay = Math.min(1000 * Math.pow(2, config._retryAttempt - 1), 8000);
      
      if (config._retryAttempt === 1) {
        toast.loading("Server is waking up... retrying.", { id: "cold-start" });
      }
      
      await new Promise((resolve) => setTimeout(resolve, delay));
      return api(config);
    }

    // Dismiss cold start toast if we're done retrying
    toast.dismiss("cold-start");
    
    return Promise.reject(error);
  }
);

// ─── Pre-warm the backend on app load ────────────────────────────────────────
if (typeof window !== "undefined") {
  // Fire-and-forget warm-up ping when the app loads
  fetch(`${BASE_URL}/warm`, { method: "GET" }).catch(() => {});
}

// ─── Request Interceptor — Attach access token ──────────────────────────────
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor — Handle 401, auto-refresh ────────────────────────
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

function processQueue(error: AxiosError | null, token: string | null = null) {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers["Authorization"] = `Bearer ${token}`;
          }
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem("refresh_token");
      if (!refreshToken) {
        isRefreshing = false;
        _handleLogout();
        return Promise.reject(error);
      }

      try {
        const { data } = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);

        if (originalRequest.headers) {
          originalRequest.headers["Authorization"] = `Bearer ${data.access_token}`;
        }

        if (tokenUpdateCallback) {
          tokenUpdateCallback(data.access_token, data.refresh_token);
        }

        processQueue(null, data.access_token);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        isRefreshing = false;
        _handleLogout();
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors with toasts
    const status = error.response?.status;
    const detail = (error.response?.data as { detail?: string })?.detail;

    if (status === 403) {
      toast.error("Access denied: " + (detail || "Insufficient permissions"));
    } else if (status === 422) {
      // Validation errors — handled by form components
    } else if (status === 500) {
      toast.error("Server error. Please try again later.");
    } else if (status !== 401) {
      if (detail) {
        toast.error(detail);
      }
    }

    return Promise.reject(error);
  }
);

function _handleLogout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  localStorage.removeItem("codepulse-auth");
  if (logoutCallback) {
    logoutCallback();
  }
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

export default api;
