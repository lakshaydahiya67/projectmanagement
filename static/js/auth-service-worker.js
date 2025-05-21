// Service Worker to intercept and modify network requests
// This ensures Authorization headers are completely blocked after logout

const LOGOUT_FLAG_KEY = 'auth_cleared';
const LOGOUT_TIMESTAMP_KEY = 'logout_timestamp';
const MAX_LOGOUT_AGE = 5 * 60 * 1000; // 5 minutes in milliseconds

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

// Helper to check if a request should have its Authorization header removed
async function shouldRemoveAuthHeader() {
  try {
    // Check for logout flag in IndexedDB
    const db = await new Promise((resolve, reject) => {
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
    const timestampRecord = await new Promise((resolve) => {
      const request = store.get(LOGOUT_TIMESTAMP_KEY);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });
    
    if (timestampRecord) {
      const timestamp = timestampRecord.value;
      const now = Date.now();
      if (now - timestamp < MAX_LOGOUT_AGE) {
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error('Error checking logout state:', error);
    return false;
  }
}

// Intercept all fetch requests
self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  // Only intercept same-origin requests
  if (request.url.startsWith(self.location.origin)) {
    event.respondWith(
      (async () => {
        try {
          // Check if we should remove Authorization header
          const removeAuth = await shouldRemoveAuthHeader();
          
          // If not a logout state, proceed with the original request
          if (!removeAuth) {
            return fetch(request);
          }
          
          // Clone the request to modify headers
          const newHeaders = new Headers(request.headers);
          
          // Remove Authorization header
          if (newHeaders.has('Authorization')) {
            newHeaders.delete('Authorization');
            console.log('Service Worker: Removed Authorization header');
          }
          
          // Add custom headers to indicate this is a post-logout request
          newHeaders.set('X-Auth-Cleared', 'true');
          newHeaders.set('X-Logout-Timestamp', Date.now().toString());
          
          // Create a new request with modified headers
          const modifiedRequest = new Request(request.url, {
            method: request.method,
            headers: newHeaders,
            body: request.body,
            mode: request.mode,
            credentials: request.credentials,
            cache: request.cache,
            redirect: request.redirect,
            referrer: request.referrer,
            integrity: request.integrity
          });
          
          return fetch(modifiedRequest);
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
    console.log('Service Worker: Received logout message');
    
    // Store logout state in IndexedDB
    (async () => {
      try {
        const db = await new Promise((resolve, reject) => {
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
        
        const transaction = db.transaction(['flags'], 'readwrite');
        const store = transaction.objectStore('flags');
        
        // Set logout flag
        store.put({ key: LOGOUT_FLAG_KEY, value: true });
        
        // Set logout timestamp
        store.put({ key: LOGOUT_TIMESTAMP_KEY, value: Date.now() });
        
        console.log('Service Worker: Stored logout state');
      } catch (error) {
        console.error('Error storing logout state:', error);
      }
    })();
  }
});
