#!/usr/bin/env python
"""
Test what HTTP methods are allowed on the board endpoint
"""
import requests

BASE_URL = "http://localhost:8001/api/v1"

def test_board_endpoint_methods():
    print("Testing board endpoint HTTP methods...")
    
    # Use a fake project ID to test
    test_project_id = "00000000-0000-0000-0000-000000000000"
    endpoint = f"{BASE_URL}/projects/{test_project_id}/boards/"
    
    try:
        # OPTIONS request to see allowed methods
        response = requests.options(endpoint)
        print(f"OPTIONS request status: {response.status_code}")
        
        if 'Allow' in response.headers:
            print(f"Allowed methods: {response.headers['Allow']}")
        else:
            print("No Allow header found")
            
        print(f"Response headers: {dict(response.headers)}")
        
        # Also try to see if the endpoint exists at all
        response = requests.get(endpoint)
        print(f"GET request status: {response.status_code}")
        print(f"GET response: {response.text[:200]}")
        
    except Exception as e:
        print(f"Error testing endpoint: {e}")

if __name__ == "__main__":
    test_board_endpoint_methods()
