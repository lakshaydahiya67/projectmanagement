class ActivityLogMiddleware:
    """
    Middleware to capture user's IP address for activity logging
    and store it in the request object
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Get the client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        # Add it to the request object for later use
        request.client_ip = ip
        
        response = self.get_response(request)
        return response 