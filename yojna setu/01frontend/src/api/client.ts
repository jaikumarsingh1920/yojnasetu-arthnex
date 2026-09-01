import axios from 'axios';

export const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE_URL || '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach JWT access token automatically
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('yojnasetu_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor for handling errors and session expiry
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data;

      // Extract human-readable error message from backend error object or detail
      let customMessage = 'An unexpected server error occurred.';
      if (data?.error?.message) {
        customMessage = data.error.message;
      } else if (data?.detail) {
        if (typeof data.detail === 'string') {
          customMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
          customMessage = data.detail.map((d: any) => d.msg || d.message).join('; ');
        }
      }

      error.userFriendlyMessage = customMessage;
      error.requestId = data?.error?.request_id || error.response.headers['x-request-id'];

      // Handle 401 Unauthorized session expiration
      if (status === 401) {
        const currentPath = window.location.pathname;
        if (!currentPath.includes('/login') && !currentPath.includes('/register')) {
          localStorage.removeItem('yojnasetu_access_token');
          localStorage.removeItem('yojnasetu_user');
          window.location.href = '/login?expired=1';
        }
      }
    } else if (error.request) {
      error.userFriendlyMessage = 'Network Error: Backend service is currently unavailable. Please check your internet connection or try again later.';
    }

    return Promise.reject(error);
  }
);
