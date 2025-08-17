// Session-based authentication functions
const API_BASE_URL = '/api/v1';

// Helper function to get a cookie by name
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
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

// Make authenticated API requests with CSRF token and session cookies
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        credentials: 'same-origin', // Include session cookies
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            ...options.headers
        }
    };

    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
            console.log('Authentication required, redirecting to login');
            window.location.href = '/login/';
            return null;
        }
        
        return response;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Simple logout function for session auth
async function logout() {
    try {
        const response = await apiRequest('/api/v1/users/logout/', {
            method: 'POST',
        });
        
        if (response && response.ok) {
            // Redirect to login page
            window.location.href = '/login/';
        }
    } catch (error) {
        console.error('Logout error:', error);
        // Redirect anyway
        window.location.href = '/login/';
    }
}

// Check if user is authenticated (simple session check)
function isAuthenticated() {
    // For session auth, we rely on server-side checks
    // This is a client-side helper that checks for session cookie
    return !!getCookie('sessionid');
}

// Login form handler
function setupLoginForm() {
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(loginForm);
            const data = {
                username: formData.get('username'),
                password: formData.get('password'),
                remember_me: formData.get('remember_me') === 'on'
            };
            
            try {
                const response = await apiRequest('/accounts/login/', {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
                
                if (response && response.ok) {
                    // Redirect to dashboard or next URL
                    const urlParams = new URLSearchParams(window.location.search);
                    const next = urlParams.get('next') || '/dashboard/';
                    window.location.href = next;
                } else {
                    // Show error message
                    const errorDiv = document.getElementById('login-error');
                    if (errorDiv) {
                        errorDiv.textContent = 'Invalid username or password';
                        errorDiv.style.display = 'block';
                    }
                }
            } catch (error) {
                console.error('Login error:', error);
                const errorDiv = document.getElementById('login-error');
                if (errorDiv) {
                    errorDiv.textContent = 'An error occurred. Please try again.';
                    errorDiv.style.display = 'block';
                }
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupLoginForm();
    
    // Setup logout buttons
    const logoutButtons = document.querySelectorAll('.logout-btn, [data-action="logout"]');
    logoutButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });
});

// Global error handler for fetch requests
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.status === 401) {
        console.log('Unauthorized request detected, redirecting to login');
        window.location.href = '/login/';
    }
});