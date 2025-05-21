// Authentication functions
const API_BASE_URL = '/api/v1';

// Register the auth service worker for intercepting network requests
if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
        try {
            const registration = await navigator.serviceWorker.register('/static/js/auth-service-worker.js', {
                scope: '/'
            });
            console.log('Auth Service Worker registered with scope:', registration.scope);
            
            // Store the registration for later use
            window.__AUTH_SERVICE_WORKER__ = registration;
            
            // Check if there's a controller (active service worker)
            if (navigator.serviceWorker.controller) {
                console.log('Auth Service Worker is already controlling this page');
            } else {
                console.log('Auth Service Worker is not yet controlling this page');
            }
        } catch (error) {
            console.error('Auth Service Worker registration failed:', error);
        }
    });
}

// Helper function to get a cookie by name
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Get CSRF token for AJAX requests
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken') || '';
}

// Check if user is authenticated
function isAuthenticated() {
    // Get the current timestamp
    const now = Math.floor(Date.now() / 1000);
    
    // Check if there's a recent logout
    const logoutTimestamp = getCookie('logout_timestamp');
    if (logoutTimestamp && (now - parseInt(logoutTimestamp)) < 300) { // 5 minutes
        console.log('Recent logout detected, considering as not authenticated');
        return false;
    }
    
    // Get token from localStorage
    const localToken = localStorage.getItem('access_token');
    if (localToken) {
        try {
            // Try to parse the JWT to check if it's expired
            const payload = JSON.parse(atob(localToken.split('.')[1]));
            if (payload.exp && payload.exp > now) {
                return true;
            }
        } catch (e) {
            console.warn('Error parsing token:', e);
        }
    }
    
    // Check cookie for token
    const cookieToken = getCookie('access_token');
    if (cookieToken) {
        try {
            const payload = JSON.parse(atob(cookieToken.split('.')[1]));
            if (payload.exp && payload.exp > now) {
                return true;
            }
        } catch (e) {
            console.warn('Error parsing cookie token:', e);
        }
    }
    
    // Check sessionStorage
    if (window.sessionStorage) {
        const sessionToken = sessionStorage.getItem('access_token');
        if (sessionToken) {
            try {
                const payload = JSON.parse(atob(sessionToken.split('.')[1]));
                if (payload.exp && payload.exp > now) {
                    return true;
                }
            } catch (e) {
                console.warn('Error parsing session token:', e);
            }
        }
    }
    
    // No valid token found
    return false;
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login/';
        return false;
    }
    return true;
}

// Fetch API wrapper with authentication
async function fetchAPI(url, options = {}) {
    if (!options.headers) {
        options.headers = {};
    }
    
    // Always include credentials to send cookies with every request
    options.credentials = 'same-origin';
    
    // Add authorization header if token exists
    const token = localStorage.getItem('access_token');
    if (token) {
        options.headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Add CSRF token for non-GET requests
    if (options.method && options.method !== 'GET') {
        options.headers['X-CSRFToken'] = getCsrfToken();
    }
    
    // Add content type for POST/PUT/PATCH requests
    if (['POST', 'PUT', 'PATCH'].includes(options.method)) {
        if (!options.headers['Content-Type'] && !(options.body instanceof FormData)) {
            options.headers['Content-Type'] = 'application/json';
        }
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}${url}`, options);
        
        // Handle 401 Unauthorized - token might be expired
        if (response.status === 401) {
            // Try to refresh token
            const refreshed = await refreshToken();
            if (refreshed) {
                // Retry the request with new token
                const token = localStorage.getItem('access_token');
                options.headers['Authorization'] = `Bearer ${token}`;
                return fetch(`${API_BASE_URL}${url}`, options);
            } else {
                // Redirect to login if refresh fails
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login/';
                return null;
            }
        }
        
        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Refresh token
async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/jwt/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            return true;
        } else {
            return false;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
        return false;
    }
}

// Login function
async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/jwt/create/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
            credentials: 'same-origin' // Include cookies in the request
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Store tokens in localStorage for JavaScript access
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            
            // Also store access token in cookie for middleware access
            // Set cookie to expire when the token expires (typically 1 hour)
            document.cookie = `access_token=${data.access}; path=/; max-age=3600; SameSite=Lax`;
            
            // Also store in session to have multiple fallback mechanisms
            if (window.sessionStorage) {
                sessionStorage.setItem('access_token', data.access);
            }
            
            console.log('Login successful, JWT token stored');
            return true;
        } else {
            const errorData = await response.json();
            console.error('Login error response:', errorData);
            throw new Error(errorData.detail || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
}

// Register function
async function register(userData) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/users/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(userData)
        });

        if (!response.ok) {
            const errorData = await response.json();
            let errorMessage = 'Registration failed';
            
            // Format error messages from the API
            if (errorData) {
                const errors = Object.entries(errorData)
                    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
                    .join('\n');
                errorMessage = errors || errorMessage;
            }
            
            throw new Error(errorMessage);
        }

        return await response.json();
    } catch (error) {
        console.error('Registration error:', error);
        throw error;
    }
}

// Request password reset function
async function requestPasswordReset(email) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/users/reset_password/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ email })
        });

        // For security reasons, the API always returns 204 No Content
        // whether the email exists or not to prevent user enumeration
        if (response.status === 204 || response.ok) {
            return true;
        }

        const errorData = await response.json();
        let errorMessage = 'Failed to send password reset email';
        
        // Format error messages from the API
        if (errorData) {
            const errors = Object.entries(errorData)
                .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
                .join('\n');
            errorMessage = errors || errorMessage;
        }
        
        throw new Error(errorMessage);
    } catch (error) {
        console.error('Password reset request error:', error);
        throw error;
    }
}

// Confirm password reset function
async function confirmPasswordReset(uid, token, newPassword, reNewPassword) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/users/reset_password_confirm/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                uid,
                token,
                new_password: newPassword,
                re_new_password: reNewPassword
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            let errorMessage = 'Password reset failed';
            
            // Format error messages from the API
            if (errorData) {
                const errors = Object.entries(errorData)
                    .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(' ') : messages}`)
                    .join('\n');
                errorMessage = errors || errorMessage;
            }
            
            throw new Error(errorMessage);
        }

        return true;
    } catch (error) {
        console.error('Password reset confirmation error:', error);
        throw error;
    }
}

// Logout function
async function logout() {
    try {
        console.log('Starting logout process...');
        
        // Get the refresh token to blacklist on the server before clearing storage
        const refreshToken = localStorage.getItem('refresh_token');
        const accessToken = localStorage.getItem('access_token');
        
        // Keep track of whether we successfully communicated with the server
        let serverNotified = false;
        
        // First attempt to notify the server about logout BEFORE clearing local storage
        // This gives us the best chance of successfully blacklisting the token
        if (refreshToken) {
            try {
                console.log('Attempting to blacklist token on server...');
                // Get CSRF token from cookies
                const csrftoken = getCookie('csrftoken') || '';
                
                // Set headers with the X-Requested-With header to identify as AJAX
                const headers = {
                    'Content-Type': 'application/json',
                    'Authorization': accessToken ? `Bearer ${accessToken}` : '',
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                };
                
                // Send the refresh token to the server for blacklisting
                // Add a custom header to indicate this is a logout request
                headers['X-Force-Logout'] = 'true';
                headers['X-Logout-Timestamp'] = Date.now().toString();
                
                const response = await fetch(`${API_BASE_URL}/auth/token/logout/`, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify({ 
                        refresh: refreshToken,
                        token_type: 'refresh',
                        force_logout: true,
                        timestamp: Date.now()
                    }),
                    credentials: 'include',  // Include cookies
                    cache: 'no-store',       // Prevent caching
                    mode: 'same-origin'      // Same origin for security
                });
                
                if (response.ok) {
                    console.log('Token successfully blacklisted on server');
                    serverNotified = true;
                } else {
                    console.warn('Failed to blacklist token on server:', await response.text());
                }
            } catch (e) {
                console.error('Error blacklisting token:', e);
            }
        }
        
        // Now clear all client-side storage
        console.log('Clearing all client-side storage...');
        
        // Clear localStorage
        localStorage.clear();
        
        // Clear sessionStorage
        if (window.sessionStorage) {
            sessionStorage.clear();
        }
        
        // Clear ALL cookies with all possible paths and domains
        const cookiesToClear = ['access_token', 'refresh_token', 'csrftoken', 'sessionid', 'jwt', 'token'];
        const pathsToClear = ['/', '/api/', '/api/v1/', '/auth/', '/dashboard/', '/admin/'];
        const domains = [window.location.hostname, '', null, undefined, 'localhost', '127.0.0.1'];
        const sameSiteOptions = ['Lax', 'Strict', 'None'];
        
        // Systematically clear all cookies with all possible combinations
        for (const cookie of cookiesToClear) {
            for (const path of pathsToClear) {
                // Try with different domains
                for (const domain of domains) {
                    if (domain) {
                        // Try different SameSite options
                        for (const sameSite of sameSiteOptions) {
                            // With secure flag
                            document.cookie = `${cookie}=; path=${path}; domain=${domain}; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=${sameSite}; Secure`;
                            // Without secure flag
                            document.cookie = `${cookie}=; path=${path}; domain=${domain}; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=${sameSite}`;
                        }
                    } else {
                        // Without domain
                        document.cookie = `${cookie}=; path=${path}; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`;
                        document.cookie = `${cookie}=; path=${path}; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Strict`;
                        document.cookie = `${cookie}=; path=${path}; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=None; Secure`;
                    }
                }
                
                // Also try with max-age=0
                document.cookie = `${cookie}=; path=${path}; max-age=0`;
            }
            
            // Also try clearing without path specification
            document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
            document.cookie = `${cookie}=; max-age=0`;
        }
        
        console.log('All client-side storage cleared');
        
        // If we haven't notified the server yet, try again with a clean slate
        // This is a backup in case the first attempt failed
        if (!serverNotified && refreshToken) {
            try {
                console.log('Making second attempt to blacklist token...');
                
                // Create a new fetch request without any auth headers since we've cleared them
                const response = await fetch(`${API_BASE_URL}/auth/token/logout/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ 
                        refresh: refreshToken,
                        token_type: 'refresh',
                        force_logout: true
                    }),
                    credentials: 'omit',  // Don't send cookies
                    cache: 'no-store'
                });
                
                if (response.ok) {
                    console.log('Token successfully blacklisted on second attempt');
                } else {
                    console.warn('Failed to blacklist token on second attempt');
                }
            } catch (e) {
                console.error('Error on second blacklist attempt:', e);
            }
        }
        
        // Add a delay to ensure all async operations have completed
        await new Promise(resolve => setTimeout(resolve, 300));
        
        console.log('Logout complete, redirecting to login page...');
        
        // Generate a unique timestamp for cache busting
        const timestamp = new Date().getTime();
        
        // Use multiple techniques to ensure the browser doesn't use cached pages
        // 1. Set cache control headers via meta tags
        const meta1 = document.createElement('meta');
        meta1.httpEquiv = 'Cache-Control';
        meta1.content = 'no-cache, no-store, must-revalidate';
        document.head.appendChild(meta1);
        
        const meta2 = document.createElement('meta');
        meta2.httpEquiv = 'Pragma';
        meta2.content = 'no-cache';
        document.head.appendChild(meta2);
        
        const meta3 = document.createElement('meta');
        meta3.httpEquiv = 'Expires';
        meta3.content = '0';
        document.head.appendChild(meta3);
        
        // Set a logout flag in sessionStorage to help prevent redirection loops
        // This is a backup mechanism in case cookies aren't properly cleared
        try {
            window.sessionStorage.setItem('force_logout', 'true');
            window.sessionStorage.setItem('logout_timestamp', timestamp.toString());
        } catch (e) {
            console.error('Failed to set sessionStorage logout flag:', e);
        }
        
        // Create multiple special iframes to help clear cookies from all domains and paths
        // This is a more aggressive approach to ensure cookies are cleared
        const paths = ['/', '/api/v1/', '/auth/', '/dashboard/'];
        
        for (const path of paths) {
            const clearFrame = document.createElement('iframe');
            clearFrame.style.display = 'none';
            clearFrame.src = `${path}api/v1/auth/token/logout/?iframe=true&t=${timestamp}&path=${encodeURIComponent(path)}`;
            document.body.appendChild(clearFrame);
        }
        
        // Implement a more aggressive approach to clearing Authorization headers
        // This completely replaces the fetch and XMLHttpRequest APIs to ensure no Authorization headers are sent
        try {
            // 1. Create a global flag indicating logout has occurred
            window.__AUTH_CLEARED__ = true;
            
            // 2. Replace fetch API completely
            const originalFetch = window.fetch;
            window.fetch = function(url, options = {}) {
                // Always create a new headers object to avoid modifying the original
                let newOptions = {...options};
                let newHeaders = new Headers();
                
                // Copy all headers except Authorization
                if (options.headers) {
                    if (options.headers instanceof Headers) {
                        for (let [key, value] of options.headers.entries()) {
                            if (key.toLowerCase() !== 'authorization') {
                                newHeaders.append(key, value);
                            }
                        }
                    } else if (typeof options.headers === 'object') {
                        for (let key in options.headers) {
                            if (key.toLowerCase() !== 'authorization') {
                                newHeaders.append(key, options.headers[key]);
                            }
                        }
                    }
                }
                
                // Add a custom header to indicate this is a post-logout request
                newHeaders.append('X-Auth-Cleared', 'true');
                newHeaders.append('X-Logout-Timestamp', Date.now().toString());
                
                newOptions.headers = newHeaders;
                console.log('Intercepted fetch request, removed Authorization header');
                return originalFetch(url, newOptions);
            };
            
            // 3. Replace XMLHttpRequest open and setRequestHeader methods
            const originalXHROpen = XMLHttpRequest.prototype.open;
            const originalXHRSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
            
            XMLHttpRequest.prototype.open = function() {
                this.__requestHeaders = {};
                return originalXHROpen.apply(this, arguments);
            };
            
            XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
                if (header.toLowerCase() === 'authorization') {
                    console.log('Blocked Authorization header in XMLHttpRequest');
                    return;
                }
                this.__requestHeaders[header] = value;
                return originalXHRSetRequestHeader.call(this, header, value);
            };
            
            console.log('Successfully patched all HTTP request methods to block Authorization headers');
        } catch (e) {
            console.error('Error while patching fetch/XHR:', e);
        }
        
        // Also add a special cookie-clearing script
        const clearScript = document.createElement('script');
        clearScript.textContent = `
            // Force clear all cookies
            const cookieNames = ['access_token', 'refresh_token', 'csrftoken', 'sessionid', 'jwt', 'token'];
            const paths = ['/', '/api/', '/api/v1/', '/auth/', '/dashboard/', '/admin/', ''];
            
            for (const name of cookieNames) {
                for (const path of paths) {
                    document.cookie = name + '=; path=' + path + '; expires=Thu, 01 Jan 1970 00:00:00 GMT; max-age=0';
                }
                // Also try without path
                document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; max-age=0';
            }
            
            // Set logout indicators in sessionStorage and localStorage
            try {
                // Set logout indicators
                sessionStorage.setItem('force_logout', 'true');
                localStorage.setItem('force_logout', 'true');
                sessionStorage.setItem('logout_timestamp', '${timestamp}');
                localStorage.setItem('logout_timestamp', '${timestamp}');
                
                // Explicitly remove any auth tokens or headers
                sessionStorage.removeItem('access_token');
                localStorage.removeItem('access_token');
                sessionStorage.removeItem('refresh_token');
                localStorage.removeItem('refresh_token');
                sessionStorage.removeItem('auth_header');
                localStorage.removeItem('auth_header');
                sessionStorage.removeItem('Authorization');
                localStorage.removeItem('Authorization');
                
                // Also try to clear any other potential auth-related items
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    if (key && (key.includes('token') || key.includes('auth') || key.includes('jwt'))) {
                        localStorage.removeItem(key);
                    }
                }
                
                for (let i = 0; i < sessionStorage.length; i++) {
                    const key = sessionStorage.key(i);
                    if (key && (key.includes('token') || key.includes('auth') || key.includes('jwt'))) {
                        sessionStorage.removeItem(key);
                    }
                }
            } catch(e) {}
            
            // Also patch the XMLHttpRequest to remove Authorization headers
            if (window.XMLHttpRequest) {
                const originalOpen = XMLHttpRequest.prototype.open;
                const originalSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
                
                XMLHttpRequest.prototype.open = function() {
                    this._requestHeaders = {};
                    return originalOpen.apply(this, arguments);
                };
                
                XMLHttpRequest.prototype.setRequestHeader = function(header, value) {
                    // Skip Authorization headers after logout
                    if (header.toLowerCase() === 'authorization') {
                        return;
                    }
                    this._requestHeaders[header] = value;
                    return originalSetRequestHeader.apply(this, arguments);
                };
            }
        `;
        document.body.appendChild(clearScript);
        
        console.log('Added cookie-clearing iframes and script');
        
        // Wait a bit longer to ensure all async operations complete
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Notify the service worker about logout
        if (navigator.serviceWorker && navigator.serviceWorker.controller) {
            try {
                // Send a message to the service worker to notify about logout
                navigator.serviceWorker.controller.postMessage({
                    type: 'LOGOUT',
                    timestamp: Date.now()
                });
                console.log('Notified service worker about logout');
            } catch (e) {
                console.error('Error notifying service worker:', e);
            }
        } else {
            console.warn('No active service worker to notify about logout');
        }
        
        // Force a complete page reload before redirecting
        // This is crucial to clear any cached state
        try {
            // Create a form that will POST to a special logout-complete endpoint
            // This is more reliable than just changing location
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = '/api/v1/auth/complete-logout/';
            form.style.display = 'none';
            
            // Add timestamp as hidden field
            const timestampField = document.createElement('input');
            timestampField.type = 'hidden';
            timestampField.name = 'timestamp';
            timestampField.value = timestamp.toString();
            form.appendChild(timestampField);
            
            // Add CSRF token if available
            const csrftoken = getCookie('csrftoken');
            if (csrftoken) {
                const csrfField = document.createElement('input');
                csrfField.type = 'hidden';
                csrfField.name = 'csrfmiddlewaretoken';
                csrfField.value = csrftoken;
                form.appendChild(csrfField);
            }
            
            // Add the form to the document and submit it
            document.body.appendChild(form);
            
            // Set a fallback redirect in case the form submission fails
            setTimeout(() => {
                // Use window.location.replace with cache-busting parameters
                const params = new URLSearchParams();
                params.append('forcedlogout', 'true');
                params.append('t', timestamp.toString());
                params.append('nocache', Math.random().toString());
                
                window.location.replace(`/login/?${params.toString()}`);
            }, 1000);
            
            // Submit the form
            form.submit();
        } catch (e) {
            console.error('Error during redirect:', e);
            // Direct redirect as fallback with multiple cache-busting parameters
            const params = new URLSearchParams();
            params.append('error', 'true');
            params.append('t', timestamp.toString());
            params.append('r', Math.random().toString());
            window.location.href = `/login/?${params.toString()}`;
        }
    } catch (error) {
        console.error('Unexpected error during logout:', error);
        // Ensure we still redirect even if there's an error
        const errorTimestamp = new Date().getTime();
        window.location.replace(`/login/?error=${errorTimestamp}`);
    }
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Show notification
function showNotification(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.classList.add('alert', `alert-${type}`, 'alert-dismissible', 'fade', 'show');
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find messages container or create one
    let messagesContainer = document.querySelector('.messages');
    if (!messagesContainer) {
        messagesContainer = document.createElement('div');
        messagesContainer.classList.add('messages');
        document.querySelector('main').prepend(messagesContainer);
    }
    
    messagesContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

// Global app object to expose utility functions to all templates
const app = {
    isAuthenticated,
    requireAuth,
    fetchAPI,
    refreshToken,
    login,
    register,
    logout,
    requestPasswordReset,
    confirmPasswordReset,
    formatDate,
    showNotification,
    getCsrfToken
};

// Make app available globally
window.app = app;

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any common functionality here
});

// Note: app is already exported above
// No need for a second export