import { createContext, useState, useEffect, useCallback } from 'react';
import axios from '../utils/axios';
import jwt_decode from 'jwt-decode';
import { useNavigate } from 'react-router-dom';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Use useCallback to fix the dependency warning
  const checkUserLoggedIn = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const decoded = jwt_decode(token);
        const currentTime = Date.now() / 1000;

        if (decoded.exp < currentTime) {
          // Token expired
          await refreshToken();
        } else {
          setUser(decoded);
        }
      }
    } catch (err) {
      console.error('Error checking auth:', err);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkUserLoggedIn();
  }, [checkUserLoggedIn]);

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) throw new Error('No refresh token');

      const response = await axios.post('/auth/jwt/refresh/', {
        refresh: refreshToken
      });

      localStorage.setItem('access_token', response.data.access);
      const decoded = jwt_decode(response.data.access);
      setUser(decoded);
      
      return response.data.access;
    } catch (err) {
      console.error('Error refreshing token:', err);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      navigate('/login');
      throw err;
    }
  };

  const login = async (email, password) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/auth/jwt/create/', {
        email,
        password
      });
      
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      
      const decoded = jwt_decode(response.data.access);
      setUser(decoded);
      
      return decoded;
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      
      // Create specific instance for registration request with explicit CORS settings
      const registerAxios = axios.create({
        baseURL: process.env.REACT_APP_API_URL,
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: false
      });
      
      // Format data according to backend expectations
      const formattedData = {
        username: userData.username,
        email: userData.email,
        password: userData.password,
        re_password: userData.password_confirm || userData.password, // Djoser uses re_password
        first_name: userData.first_name || '',
        last_name: userData.last_name || ''
      };
      
      // Debug logging
      console.log('Sending registration request to:', '/auth/users/');
      console.log('Registration data:', formattedData);
      
      // Use auth/users/ endpoint which is provided by djoser
      const response = await registerAxios.post('/auth/users/', formattedData);
      
      console.log('Registration successful:', response.data);
      
      // Return the response, but don't auto-login since some setups require email verification
      return response.data;
    } catch (err) {
      console.error('Registration error:', err);
      
      if (process.env.NODE_ENV !== 'production') {
        // In development, log the full error details
        console.error('Error details:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status,
          headers: err.response?.headers,
          request: {
            url: err.config?.url,
            method: err.config?.method,
            data: err.config?.data,
            headers: err.config?.headers
          }
        });
      }
      
      // Extract detailed error messages from response
      let errorMessage = 'Registration failed';
      
      if (err.response?.data) {
        // Format error messages from different possible formats
        if (typeof err.response.data === 'object') {
          errorMessage = Object.entries(err.response.data)
            .map(([key, value]) => {
              // Handle array or string value
              const errorValue = Array.isArray(value) ? value.join(', ') : value;
              return `${key}: ${errorValue}`;
            })
            .join('; ');
        } else if (typeof err.response.data === 'string') {
          errorMessage = err.response.data;
        }
      }
      
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    navigate('/login');
  };

  const resetPassword = async (email) => {
    try {
      setLoading(true);
      setError(null);
      
      // Use a dedicated axios instance without auth headers for password reset
      const resetAxios = axios.create({
        baseURL: process.env.REACT_APP_API_URL,
        headers: {
          'Content-Type': 'application/json',
        },
        withCredentials: false
      });
      
      console.log('Sending password reset request for:', email);
      
      await resetAxios.post('/auth/users/reset_password/', { email });
      
      console.log('Password reset request successful');
      return true;
    } catch (err) {
      console.error('Password reset error:', err);
      
      // In development, log more details
      if (process.env.NODE_ENV !== 'production') {
        console.error('Error details:', {
          message: err.message,
          response: err.response?.data,
          status: err.response?.status
        });
      }
      
      // Djoser doesn't tell us if the email exists, but we show a success message anyway
      // This is a security feature to prevent email enumeration
      if (err.response?.status === 400) {
        return true; // Return success even if email doesn't exist
      }
      
      setError(err.response?.data?.detail || 'Password reset request failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      error,
      login,
      register,
      logout,
      refreshToken,
      resetPassword,
      isAuthenticated: !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
