// API Base URL - required in production, defaults to localhost in development
const API_BASE_URL = (() => {
  const url = process.env.NEXT_PUBLIC_API_URL;
  
  // In production, API URL must be set
  if (process.env.NODE_ENV === 'production' && !url) {
    console.error('[API] NEXT_PUBLIC_API_URL is not configured. API calls will fail.');
  }
  
  return url || 'http://localhost:8000/api';
})();

interface ApiError {
  message: string;
  detail?: string;
  [key: string]: any;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
    
    // Warn if API URL is not configured in production
    if (process.env.NODE_ENV === 'production' && !process.env.NEXT_PUBLIC_API_URL) {
      console.warn('[API Client] NEXT_PUBLIC_API_URL is not set. Using default:', this.baseURL);
    }
    
    // Log API URL in development
    if (process.env.NODE_ENV === 'development') {
      console.log('[API Client] Initialized with base URL:', this.baseURL);
    }
  }

  private async request<T = any>(
    endpoint: string,
    options: RequestInit & { params?: Record<string, string> } = {}
  ): Promise<T> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Handle query parameters
    let url = `${this.baseURL}${endpoint}`;
    if (options.params) {
      const searchParams = new URLSearchParams(options.params);
      url += `?${searchParams.toString()}`;
    }

    // Remove params from options before passing to fetch
    const { params, ...fetchOptions } = options;

    try {
      // Log request details in development
      if (process.env.NODE_ENV === 'development') {
        console.log('[API Request]', {
          method: fetchOptions.method || 'GET',
          url,
          headers: Object.keys(headers),
        });
      }

      const response = await fetch(url, {
        ...fetchOptions,
        headers,
      });

      // Handle 401 Unauthorized - token expired
      if (response.status === 401) {
        const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null;
        
        if (refreshToken) {
          try {
            // Try to refresh the token
            const refreshResponse = await fetch(`${this.baseURL}/v1/auth/refresh/`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshResponse.ok) {
              const data = await refreshResponse.json();
              if (data.access_token) {
                localStorage.setItem('auth_token', data.access_token);
                if (data.refresh_token) {
                  localStorage.setItem('refresh_token', data.refresh_token);
                }
                // Retry the original request with new token
                headers['Authorization'] = `Bearer ${data.access_token}`;
                const retryResponse = await fetch(url, {
                  ...options,
                  headers,
                });
                
                if (!retryResponse.ok) {
                  throw await this.handleError(retryResponse);
                }
                
                return await retryResponse.json();
              }
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            if (typeof window !== 'undefined') {
              localStorage.removeItem('auth_token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('user');
              
              // Show notification and redirect
              if (window.location.pathname !== '/login') {
                window.location.href = '/login?expired=true';
              }
            }
            throw new Error('Session expired. Please login again.');
          }
        } else {
          // No refresh token, clear everything
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            
            if (window.location.pathname !== '/login') {
              window.location.href = '/login?expired=true';
            }
          }
          throw new Error('Session expired. Please login again.');
        }
      }

      if (!response.ok) {
        throw await this.handleError(response);
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return {} as T;
    } catch (error) {
      // Enhanced error handling for network errors
      if (error instanceof TypeError && error.message === 'Failed to fetch') {
        // Network error - provide more helpful message
        const errorMessage = `Network error: Unable to connect to ${this.baseURL}. Please check if the backend server is running.`;
        
        if (process.env.NODE_ENV === 'development') {
            console.error('[API Error]', {
            url,
            baseURL: this.baseURL,
            error: error.message,
            suggestion: errorMessage,
            });
        }
        
        throw new Error(errorMessage);
      }
      
      if (error instanceof Error) {
        // Log error details in development
        if (process.env.NODE_ENV === 'development') {
          // Skip logging empty object errors which might be confusing
          if (Object.keys(error).length > 0 || error.message) {
            console.error('[API Error]', {
                url,
                error: error.message,
                stack: error.stack,
            });
          }
        }
        throw error;
      }
      
      throw new Error('An unexpected error occurred');
    }
  }

  private async handleError(response: Response): Promise<Error> {
    let errorMessage = `Request failed with status ${response.status}`;
    
    try {
      const text = await response.text();
      if (text) {
        try {
          const errorData = JSON.parse(text);
          errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
        } catch {
          // Not JSON, use text directly if it's short
          if (text.length < 500) {
            errorMessage = text;
          }
        }
      }
    } catch {
      // If reading response fails, use status text
      errorMessage = response.statusText || errorMessage;
    }
    
    console.error(`[API Error] Status ${response.status}: ${errorMessage}`);
    return new Error(errorMessage);
  }

  async get<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  }

  async post<T = any>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T = any>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T = any>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T = any>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'DELETE',
    });
  }

  async postBlob(endpoint: string, data?: any, options?: RequestInit): Promise<Blob> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options?.headers,
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${this.baseURL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      method: 'POST',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
      const text = await response.text();
      try {
        const errorData = JSON.parse(text);
        throw new Error(errorData.error || errorData.message || `Export failed: ${response.status}`);
      } catch {
        throw new Error(`Export failed: ${response.status}`);
      }
    }

    return await response.blob();
  }
}

export const api = new ApiClient();



