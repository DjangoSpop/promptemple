/**
 * PromptCraft API Client Configuration and Utilities
 * 
 * This file provides a complete, production-ready API client setup
 * for frontend applications integrating with the PromptCraft backend.
 * 
 * Usage:
 * - Copy this file to your frontend project
 * - Configure BASE_URL and environment variables
 * - Import and use the apiClient instance throughout your app
 * 
 * Example:
 * ```typescript
 * import { apiClient } from './api/client';
 * 
 * const data = await apiClient.get('/api/v2/templates/');
 * ```
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
  AxiosError,
} from 'axios';

/**
 * API Configuration
 */
export const API_CONFIG = {
  development: {
    baseURL: 'http://127.0.0.1:8000',
    timeout: 30000,
    retryAttempts: 3,
    retryDelay: 1000,
  },
  production: {
    baseURL: 'https://www.prompt-temple.com',
    timeout: 30000,
    retryAttempts: 2,
    retryDelay: 1000,
  },
};

/**
 * Get API configuration based on current environment
 */
export function getAPIConfig() {
  const env = process.env.NODE_ENV === 'production' ? 'production' : 'development';
  const envConfig = API_CONFIG[env as keyof typeof API_CONFIG];
  
  // Allow override via environment variable
  if (process.env.REACT_APP_API_URL) {
    envConfig.baseURL = process.env.REACT_APP_API_URL;
  }
  
  return envConfig;
}

/**
 * Custom Error Class for API Errors
 */
export class APIError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string,
    public response?: any
  ) {
    super(message);
    this.name = 'APIError';
  }

  static from(error: any): APIError {
    if (error instanceof APIError) {
      return error;
    }

    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;
      const code = data?.code || `HTTP_${status}`;
      const message = data?.detail || data?.error || error.message;

      return new APIError(status, code, message, data);
    }

    if (error.request) {
      // Request made but no response
      return new APIError(0, 'NO_RESPONSE', 'No response from server', error);
    }

    // Request setup error
    return new APIError(0, 'REQUEST_ERROR', error.message, error);
  }
}

/**
 * Retry interceptor for handling transient failures
 */
function retryInterceptor(error: AxiosError, config: InternalAxiosRequestConfig): Promise<AxiosResponse> {
  const maxRetries = 3;
  const baseDelay = 1000;

  // @ts-ignore - Add custom properties to config for retry tracking
  const retryCount = config._retryCount || 0;

  // Don't retry if max retries exceeded
  if (retryCount >= maxRetries) {
    return Promise.reject(error);
  }

  // Don't retry client errors (4xx) except 429 (rate limit)
  if (error.response?.status && error.response.status >= 400 && error.response.status < 500) {
    if (error.response.status !== 429) {
      return Promise.reject(error);
    }
  }

  // Exponential backoff: 1s, 2s, 4s
  const delay = baseDelay * Math.pow(2, retryCount);

  // @ts-ignore
  config._retryCount = retryCount + 1;

  return new Promise(resolve => {
    setTimeout(() => {
      resolve(axios(config));
    }, delay);
  });
}

/**
 * Main API Client Class
 */
export class PromptCraftAPIClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshPromise: Promise<string> | null = null;

  constructor(config?: Partial<typeof API_CONFIG.development>) {
    const apiConfig = getAPIConfig();
    const finalConfig = { ...apiConfig, ...config };

    this.client = axios.create({
      baseURL: finalConfig.baseURL,
      timeout: finalConfig.timeout,
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Name': 'PromptCraft-Frontend',
        'X-Client-Version': '1.0.0',
      },
    });

    // Request interceptor: Add token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        if (this.accessToken && !config.url?.includes('/auth/login')) {
          config.headers.Authorization = `Bearer ${this.accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(APIError.from(error))
    );

    // Response interceptor: Handle refresh and errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

        // Handle 401 - Token expired, try refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const newAccessToken = await this.refreshAccessToken();
            this.accessToken = newAccessToken;
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed - clear tokens and redirect to login
            this.logout();
            this.notifyAuthError();
            return Promise.reject(refreshError);
          }
        }

        // Retry transient errors
        if (error.response?.status === 503 || error.response?.status === 429 || !error.response) {
          return retryInterceptor(error, originalRequest);
        }

        return Promise.reject(APIError.from(error));
      }
    );

    // Load tokens from storage
    this.loadTokens();
  }

  /**
   * Set access token
   */
  setAccessToken(token: string) {
    this.accessToken = token;
    localStorage.setItem('accessToken', token);
  }

  /**
   * Set refresh token
   */
  setRefreshToken(token: string) {
    this.refreshToken = token;
    // Don't store in localStorage - only in memory or httpOnly cookie
  }

  /**
   * Load tokens from storage
   */
  private loadTokens() {
    this.accessToken = localStorage.getItem('accessToken');
  }

  /**
   * Refresh access token
   */
  private async refreshAccessToken(): Promise<string> {
    // Prevent multiple refresh requests
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = (async () => {
      if (!this.refreshToken) {
        throw new Error('No refresh token available');
      }

      try {
        const response = await this.client.post('/api/v2/auth/refresh/', {
          refresh: this.refreshToken,
        });

        const newAccessToken = response.data.access;
        this.accessToken = newAccessToken;
        localStorage.setItem('accessToken', newAccessToken);

        this.refreshPromise = null;
        return newAccessToken;
      } catch (error) {
        this.refreshPromise = null;
        throw error;
      }
    })();

    return this.refreshPromise;
  }

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<{ access: string; refresh: string }> {
    try {
      const response = await this.client.post('/api/v2/auth/login/', {
        email,
        password,
      });

      this.setAccessToken(response.data.access);
      this.setRefreshToken(response.data.refresh);

      return response.data;
    } catch (error) {
      throw APIError.from(error);
    }
  }

  /**
   * Register new user
   */
  async register(
    email: string,
    password: string,
    firstName: string,
    lastName: string
  ): Promise<{ access: string; refresh: string }> {
    try {
      const response = await this.client.post('/api/v2/auth/register/', {
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      });

      this.setAccessToken(response.data.access);
      this.setRefreshToken(response.data.refresh);

      return response.data;
    } catch (error) {
      throw APIError.from(error);
    }
  }

  /**
   * Logout
   */
  logout() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('accessToken');
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return this.accessToken;
  }

  /**
   * Notify that authentication has failed (override in your app)
   */
  private notifyAuthError() {
    // Emit event or dispatch Redux action to redirect to login
    window.dispatchEvent(new CustomEvent('auth-error'));
  }

  /**
   * GET request
   */
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get<T>(url, config);
    return response.data;
  }

  /**
   * POST request
   */
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post<T>(url, data, config);
    return response.data;
  }

  /**
   * PUT request
   */
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put<T>(url, data, config);
    return response.data;
  }

  /**
   * PATCH request
   */
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.patch<T>(url, data, config);
    return response.data;
  }

  /**
   * DELETE request
   */
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete<T>(url, config);
    return response.data;
  }
}

/**
 * Global API Client Instance
 * Use this throughout your application
 */
export const apiClient = new PromptCraftAPIClient();

/**
 * React Hook: useAPI
 * 
 * Usage:
 * ```typescript
 * const { data, loading, error } = useAPI('/api/v2/templates/', 'GET');
 * ```
 */
export function useAPI<T = any>(
  url: string,
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' = 'GET',
  options?: {
    body?: any;
    skip?: boolean;
    dependencies?: any[];
    onSuccess?: (data: T) => void;
    onError?: (error: APIError) => void;
  }
) {
  const [data, setData] = React.useState<T | null>(null);
  const [loading, setLoading] = React.useState(!options?.skip);
  const [error, setError] = React.useState<APIError | null>(null);

  React.useEffect(() => {
    if (options?.skip) {
      return;
    }

    const executeRequest = async () => {
      try {
        setLoading(true);
        setError(null);

        let result;
        switch (method) {
          case 'GET':
            result = await apiClient.get<T>(url);
            break;
          case 'POST':
            result = await apiClient.post<T>(url, options?.body);
            break;
          case 'PUT':
            result = await apiClient.put<T>(url, options?.body);
            break;
          case 'PATCH':
            result = await apiClient.patch<T>(url, options?.body);
            break;
          case 'DELETE':
            result = await apiClient.delete<T>(url);
            break;
          default:
            throw new Error(`Unsupported method: ${method}`);
        }

        setData(result);
        options?.onSuccess?.(result);
      } catch (err) {
        const apiError = err instanceof APIError ? err : APIError.from(err);
        setError(apiError);
        options?.onError?.(apiError);
      } finally {
        setLoading(false);
      }
    };

    executeRequest();
  }, options?.dependencies || [url, method]);

  const refetch = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      let result;
      switch (method) {
        case 'GET':
          result = await apiClient.get<T>(url);
          break;
        case 'POST':
          result = await apiClient.post<T>(url, options?.body);
          break;
        case 'PUT':
          result = await apiClient.put<T>(url, options?.body);
          break;
        case 'PATCH':
          result = await apiClient.patch<T>(url, options?.body);
          break;
        case 'DELETE':
          result = await apiClient.delete<T>(url);
          break;
        default:
          throw new Error(`Unsupported method: ${method}`);
      }

      setData(result);
      options?.onSuccess?.(result);
    } catch (err) {
      const apiError = err instanceof APIError ? err : APIError.from(err);
      setError(apiError);
      options?.onError?.(apiError);
    } finally {
      setLoading(false);
    }
  }, [url, method, options?.body]);

  return { data, loading, error, refetch };
}

/**
 * Type Definitions for Common API Responses
 */

export interface Template {
  id: number;
  title: string;
  description: string;
  template_content: string;
  category: number;
  featured: boolean;
  trending: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateCategory {
  id: number;
  name: string;
  description: string;
  icon?: string;
}

export interface AssistantThread {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  messages_count: number;
}

export interface DashboardData {
  user_metrics: {
    total_users: number;
    active_today: number;
    new_today: number;
  };
  template_metrics: {
    total_templates: number;
    used_today: number;
    trending: Template[];
  };
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
}
