#!/usr/bin/env python3
import os
import django
import sys

# Add the project directory to Python path
sys.path.insert(0, '/home/lakshaydahiya/Downloads/excellence/vscode/projectmanagement')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.urls import get_resolver
from django.test import RequestFactory
from django.urls.resolvers import URLPattern, URLResolver
from rest_framework.test import APIRequestFactory

def print_url_patterns(patterns, prefix=''):
    """Recursively print URL patterns"""
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            print(f"{prefix}{pattern.pattern} -> RESOLVER")
            if hasattr(pattern, 'url_patterns'):
                print_url_patterns(pattern.url_patterns, prefix + '  ')
        elif isinstance(pattern, URLPattern):
            view_name = getattr(pattern.callback, '__name__', str(pattern.callback))
            print(f"{prefix}{pattern.pattern} -> {view_name}")

def test_url_resolution():
    """Test actual URL resolution for our problematic endpoint"""
    from django.urls import resolve
    from django.test import RequestFactory
    
    factory = RequestFactory()
    
    # Test URLs that should hit BoardViewSet
    test_urls = [
        '/api/v1/projects/123e4567-e89b-12d3-a456-426614174000/boards/',
        '/api/v1/projects/00000000-0000-0000-0000-000000000000/boards/',
    ]
    
    print("=== URL RESOLUTION TEST ===")
    for url in test_urls:
        try:
            print(f"\nTesting URL: {url}")
            resolver_match = resolve(url)
            print(f"  View Function: {resolver_match.func}")
            print(f"  View Name: {resolver_match.view_name}")
            print(f"  URL Name: {resolver_match.url_name}")
            print(f"  Kwargs: {resolver_match.kwargs}")
            print(f"  Args: {resolver_match.args}")
            
            # Check if it's a viewset
            if hasattr(resolver_match.func, 'cls'):
                viewset_class = resolver_match.func.cls
                print(f"  ViewSet Class: {viewset_class}")
                print(f"  ViewSet Actions: {getattr(resolver_match.func, 'actions', 'No actions')}")
                
        except Exception as e:
            print(f"  ERROR: {e}")

def check_router_registration():
    """Check how the routers are registering URLs"""
    from projects.urls import router, projects_router, boards_router, columns_router
    
    print("\n=== ROUTER REGISTRATION ===")
    
    print("Main router patterns:")
    for pattern in router.urls:
        print(f"  {pattern.pattern} -> {pattern.callback}")
    
    print("\nProjects router patterns:")
    for pattern in projects_router.urls:
        print(f"  {pattern.pattern} -> {pattern.callback}")
        
    print("\nBoards router patterns:")
    for pattern in boards_router.urls:
        print(f"  {pattern.pattern} -> {pattern.callback}")

if __name__ == '__main__':
    print("=== DJANGO URL PATTERNS ===")
    resolver = get_resolver()
    print_url_patterns(resolver.url_patterns)
    
    test_url_resolution()
    check_router_registration()
