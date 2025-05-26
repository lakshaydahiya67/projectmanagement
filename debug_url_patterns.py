#!/usr/bin/env python
"""
Debug URL patterns for the projects app
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'projectmanagement.settings')
django.setup()

from django.urls import reverse, get_resolver
from rest_framework.test import APIClient
from projects.urls import router, projects_router, boards_router, columns_router

def debug_url_patterns():
    print("Debugging URL patterns...")
    
    print("\n=== Router configurations ===")
    print(f"Main router: {router}")
    print(f"Main router URLs: {[pattern.name for pattern in router.get_urls()]}")
    
    print(f"\nProjects router: {projects_router}")
    print(f"Projects router URLs: {[pattern.name for pattern in projects_router.get_urls()]}")
    
    print(f"\nBoards router: {boards_router}")
    print(f"Boards router URLs: {[pattern.name for pattern in boards_router.get_urls()]}")
    
    print(f"\nColumns router: {columns_router}")
    print(f"Columns router URLs: {[pattern.name for pattern in columns_router.get_urls()]}")
    
    # Test URL generation
    print("\n=== Testing URL generation ===")
    try:
        test_project_id = "00000000-0000-0000-0000-000000000000"
        
        # Try to reverse the board list URL
        board_list_url = projects_router.get_urls()
        print(f"Board URLs in projects_router: {[str(pattern.pattern) for pattern in board_list_url if 'board' in str(pattern.pattern)]}")
        
    except Exception as e:
        print(f"Error generating URLs: {e}")
        
    # Check the exact registered viewsets
    print("\n=== Registered viewsets ===")
    for registry in projects_router.registry:
        print(f"Prefix: {registry[0]}, Viewset: {registry[1]}, Basename: {registry[2]}")

if __name__ == "__main__":
    debug_url_patterns()
