#!/usr/bin/env python
"""
Debug the exact URL patterns being generated
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.urls import get_resolver

def debug_exact_patterns():
    print("Debugging exact URL patterns...")
    
    try:
        # Get the main URL resolver
        resolver = get_resolver()
        print(f"Main resolver: {resolver}")
        
        # Look specifically for API patterns
        for pattern in resolver.url_patterns:
            pattern_str = str(pattern.pattern)
            print(f"Top level pattern: {pattern_str}")
            
            if 'api/v1/' in pattern_str and hasattr(pattern, 'url_patterns'):
                print(f"  Found API v1 patterns:")
                for api_pattern in pattern.url_patterns:
                    api_pattern_str = str(api_pattern.pattern)
                    print(f"    {api_pattern_str}")
                    
                    if 'projects/' in api_pattern_str and hasattr(api_pattern, 'url_patterns'):
                        print(f"      Found projects patterns:")
                        for proj_pattern in api_pattern.url_patterns:
                            proj_pattern_str = str(proj_pattern.pattern)
                            print(f"        {proj_pattern_str}")
                            if hasattr(proj_pattern, 'callback') and hasattr(proj_pattern.callback, 'cls'):
                                print(f"          -> {proj_pattern.callback.cls.__name__}")
                                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_exact_patterns()
