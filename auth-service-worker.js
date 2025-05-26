// Service Worker to intercept and modify network requests
// This ensures Authorization headers are completely blocked after logout
// and properly added for authenticated requests

const LOGOUT_FLAG_KEY = 'auth_cleared';
const LOGOUT_TIMESTAMP_KEY = 'logout_timestamp';
const AUTH_TOKEN_KEY = 'auth_token';
const MAX_LOGOUT_AGE = 5 * 60 * 1000; // 5 minutes in milliseconds

// Endpoints that should NEVER have authentication headers automatically added
// This prevents authentication bypass on login/registration endpoints
// Updated to match actual API v1 endpoint patterns used in the Django application
const AUTH_BYPASS_ENDPOINTS = [
  // Djoser authentication endpoints (versioned API)
  '/api/v1/auth/users/',                      // User registration
  '/api/v1/auth/users/activation/',           // Account activation
  '/api/v1/auth/users/resend_activation/',    // Resend activation
  '/api/v1/auth/users/reset_password/',       // Password reset request
  '/api/v1/auth/users/reset_password_confirm/', // Password reset confirm
  '/api/v1/auth/users/set_password/',         // Set new password
  '/api/v1/auth/users/set_username/',         // Set new username
  
  // Custom JWT endpoints (versioned API)
  '/api/v1/auth/jwt/create/',                 // Login/JWT token creation
  '/api/v1/auth/jwt/refresh/',                // Token refresh
  '/api/v1/auth/jwt/verify/',                 // Token verification
  '/api/v1/auth/jwt/blacklist/',              // Token blacklist
  
  // Public endpoints that bypass authentication
  '/api/v1/public/password-reset/',           // Public password reset
  
  // Legacy patterns for backward compatibility
  '/api/auth/users/',
  '/api/auth/jwt/create/',
  '/api/auth/jwt/refresh/',
  '/api/auth/jwt/verify/',
  '/api/auth/token/refresh/',
  '/api/auth/token/verify/',
  '/api/auth/password/reset/',
  '/api/auth/password/reset/confirm/',
  '/api/users/create/',
  '/api/users/register/',
  '/api/registration/',
  '/api/login/',
  '/api/logout/',
  '/api/token/',
  '/api/refresh-token/',
  '/api/verify-token/'
];

// Function to check if a URL should bypass authentication injection
function shouldBypassAuthInjection(url) {
  try {
    const urlObj = new URL(url);
    const pathname = urlObj.pathname;
    
    return AUTH_BYPASS_ENDPOINTS.some(endpoint => {
      // Exact match or starts with the endpoint path
      return pathname === endpoint || pathname.startsWith(endpoint);
    });
  } catch (error) {
    console.warn('Invalid URL for auth bypass check:', url);
    return false;
  }
}

// Install event - cache critical resources
self.addEventListener('install', (event) => {
  console.log('Auth Service Worker installed');
  self.skipWaiting(); // Activate immediately
});

// Activate event - claim clients and clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Auth Service Worker activated');
  event.waitUntil(self.clients.claim());
});

// Listen for messages from the main thread
self.addEventListener('message', (event) => {
  console.log('Auth Service Worker received message:', event.data.type);
  
  if (event.data.type === 'SET_AUTH_TOKEN') {
    // Store the token in IndexedDB for use in fetch events
    storeAuthToken(event.data.token);
  } else if (event.data.type === 'CLEAR_AUTH_TOKEN') {
    // Clear the token from IndexedDB
    clearAuthToken();
  }
});

// Store auth token in IndexedDB
async function storeAuthToken(token) {
  try {
    const db = await openAuthDatabase();
    const transaction = db.transaction(['flags'], 'readwrite');
    const store = transaction.objectStore('flags');
    
    store.put({ key: AUTH_TOKEN_KEY, value: token });
    console.log('Auth token stored in service worker');
  } catch (error) {
    console.error('Failed to store auth token:', error);
  }
}

// Clear auth token from IndexedDB
async function clearAuthToken() {
  try {
    const db = await openAuthDatabase();
    const transaction = db.transaction(['flags'], 'readwrite');
    const store = transaction.objectStore('flags');
    
    store.delete(AUTH_TOKEN_KEY);
    console.log('Auth token cleared from service worker');
  } catch (error) {
    console.error('Failed to clear auth token:', error);
  }
}

// Helper function to open the auth database
function openAuthDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('auth_state', 1);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('flags')) {
        db.createObjectStore('flags', { keyPath: 'key' });
      }
    };
    
    request.onsuccess = (event) => resolve(event.target.result);
    request.onerror = (event) => reject(event.target.error);
  });
}

// Helper to check if a request should have its Authorization header removed
async function shouldRemoveAuthHeader() {
  try {
    // Check for logout flag in IndexedDB
    const db = await openAuthDatabase();
    
    const transaction = db.transaction(['flags'], 'readonly');
    const store = transaction.objectStore('flags');
    
    // Check for logout flag
    const logoutFlag = await new Promise((resolve) => {
      const request = store.get(LOGOUT_FLAG_KEY);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });
    
    if (logoutFlag && logoutFlag.value === true) {
      return true;
    }
    
    // Check for logout timestamp
    const logoutTimestamp = await new Promise((resolve) => {
      const request = store.get(LOGOUT_TIMESTAMP_KEY);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });
    
    if (logoutTimestamp && logoutTimestamp.value) {
      const now = Date.now();
      const timestamp = parseInt(logoutTimestamp.value, 10);
      
      // If the timestamp is recent (within MAX_LOGOUT_AGE), remove auth headers
      if (!isNaN(timestamp) && now - timestamp < MAX_LOGOUT_AGE) {
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error('Error checking logout state:', error);
    return false;
  }
}

// Helper function to get the stored auth token
async function getStoredAuthToken() {
  try {
    const db = await openAuthDatabase();
    const transaction = db.transaction(['flags'], 'readonly');
    const store = transaction.objectStore('flags');
    
    const token = await new Promise((resolve) => {
      const request = store.get(AUTH_TOKEN_KEY);
      request.onsuccess = () => resolve(request.result && request.result.value);
      request.onerror = () => resolve(null);
    });
    
    return token;
  } catch (error) {
    console.error('Error getting stored auth token:', error);
    return null;
  }
}

// Helper function to remove the Authorization header from a Headers object
function removeAuthorizationHeader(headers) {
  const newHeaders = new Headers(headers);
  newHeaders.delete('Authorization');
  newHeaders.delete('X-CSRFToken');
  return newHeaders;
}

// Intercept all fetch requests
self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  // Only intercept API requests
  if (request.url.includes('/api/')) {
    event.respondWith(
      (async () => {
        try {
          // Check if we should remove auth headers due to logout
          const shouldRemove = await shouldRemoveAuthHeader();
          
          // Check if we should remove auth headers due to logout
          if (shouldRemove) {
            // Clone the request and remove the Authorization header
            const newRequest = new Request(request.url, {
              method: request.method,
              headers: removeAuthorizationHeader(request.headers),
              body: request.method !== 'GET' && request.method !== 'HEAD' ? await request.clone().arrayBuffer() : undefined,
              mode: request.mode,
              credentials: request.credentials,
              cache: request.cache,
              redirect: request.redirect,
              referrer: request.referrer,
              integrity: request.integrity
            });
            
            console.log('Auth Service Worker: Removed Authorization header from request to', request.url);
            return fetch(newRequest);
          }
          
          // Check if this endpoint should bypass automatic auth injection
          if (shouldBypassAuthInjection(request.url)) {
            console.log('Auth Service Worker: Bypassing auth injection for', request.url);
            return fetch(request);
          }
          
          // Check if we need to add the auth token
          // This is especially important for requests that might not have the token
          const hasAuthHeader = request.headers.has('Authorization');
          
          if (!hasAuthHeader) {
            // Try to get the stored token
            const token = await getStoredAuthToken();
            
            if (token) {
              // Clone the request and add the Authorization header
              const newHeaders = new Headers(request.headers);
              newHeaders.set('Authorization', `Bearer ${token}`);
              
              const newRequest = new Request(request.url, {
                method: request.method,
                headers: newHeaders,
                body: request.method !== 'GET' && request.method !== 'HEAD' ? await request.clone().arrayBuffer() : undefined,
                mode: request.mode,
                credentials: request.credentials,
                cache: request.cache,
                redirect: request.redirect,
                referrer: request.referrer,
                integrity: request.integrity
              });
              
              console.log('Auth Service Worker: Added Authorization header to request to', request.url);
              return fetch(newRequest);
            }
          }
          
          // Otherwise, just pass through the original request
          return fetch(request);
        } catch (error) {
          console.error('Error in fetch handler:', error);
          return fetch(request);
        }
      })()
    );
  }
});

// Listen for messages from the client
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'LOGOUT') {
    // Store the logout flag in IndexedDB
    const timestamp = event.data.timestamp || Date.now();
    
    // Open the database
    const request = indexedDB.open('auth_state', 1);
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('flags')) {
        db.createObjectStore('flags', { keyPath: 'key' });
      }
    };
    
    request.onsuccess = (event) => {
      const db = event.target.result;
      
      const transaction = db.transaction(['flags'], 'readwrite');
      const store = transaction.objectStore('flags');
      
      // Set the logout flag
      store.put({ key: LOGOUT_FLAG_KEY, value: true });
      
      // Set the logout timestamp
      store.put({ key: LOGOUT_TIMESTAMP_KEY, value: timestamp });
      
      console.log('Auth Service Worker: Logout flag set at timestamp', timestamp);
      
      // Respond to the client
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: true, timestamp: timestamp });
      }
    };
    
    request.onerror = (error) => {
      console.error('Error storing logout flag:', error);
      
      // Respond to the client with error
      if (event.ports && event.ports[0]) {
        event.ports[0].postMessage({ success: false, error: error.toString() });
      }
    };
  }
});
