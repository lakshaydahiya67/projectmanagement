"""
Custom middleware for the Project Management application.
"""

class ServiceWorkerMiddleware:
    """
    Middleware to add Service-Worker-Allowed header for service worker registration.
    
    This fixes the error: "The path of the provided scope ('/') is not under the max scope allowed ('/static/js/')"
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        print("ServiceWorkerMiddleware initialized")

    def __call__(self, request):
        # Store the path for debugging
        path = request.path
        
        # Get the response from the next middleware/view
        response = self.get_response(request)
        
        # Check if this is a request for the service worker script
        if '/static/js/auth-service-worker.js' in path:
            # Add the Service-Worker-Allowed header to allow the service worker to control the entire origin
            response['Service-Worker-Allowed'] = '/'
            print(f"Added Service-Worker-Allowed header for {path}")
        
        return response
