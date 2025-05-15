import axios from 'axios';

// Configure base URL for API requests
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default configuration
const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false  // Default to no credentials for CORS
});

// Add a request interceptor to include the authorization token
axiosInstance.interceptors.request.use(
  (config) => {
    // Log request in development
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[API Request] ${config.method?.toUpperCase() || 'GET'} ${config.url}`, { 
        headers: config.headers, 
        data: config.data 
      });
    }
    
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      
      // Only use credentials for authenticated endpoints that need cookies
      // This helps prevent CORS preflight issues
      if (config.url && (
        config.url.includes('/auth/jwt/') || 
        config.url.includes('/users/me')
      )) {
        config.withCredentials = true;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle token refresh
axiosInstance.interceptors.response.use(
  (response) => {
    // Log response in development
    if (process.env.NODE_ENV !== 'production') {
      console.log(`[API Response] ${response.status} ${response.config.url}`, { 
        data: response.data 
      });
    }
    return response;
  },
  async (error) => {
    // Log errors in development
    if (process.env.NODE_ENV !== 'production') {
      console.error('[API Error]', { 
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        url: error.config?.url
      });
    }
    
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried to refresh the token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
        
        const response = await axiosInstance.post('/auth/jwt/refresh/', { refresh: refreshToken });
        localStorage.setItem('access_token', response.data.access);
        
        // Update the original request with the new token
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        return axiosInstance(originalRequest);
      } catch (err) {
        // If refresh fails, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance;
