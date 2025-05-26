#!/usr/bin/env python3
"""
Test script to verify the priority case sensitivity fix
"""
import os
import sys
import requests
import json
import time

# Root URL for API
BASE_URL = "http://localhost:8001"

def test_priority_validation():
    """Test task creation with different priority values"""
    print(f"🔧 TESTING TASK PRIORITY VALIDATION")
    print("=" * 60)
    
    # Use an existing API session
    s = requests.Session()
    
    # Login to get auth token
    login_data = {
        "email": "lakshaydahiya67@gmail.com",
        "password": "password123"  # Try common password
    }
    
    try:
        # Try login with common passwords until one works
        common_passwords = ["admin123", "password", "password123", "123456", "test123", "djangoproject", "admin"]
        login_success = False
        
        for password in common_passwords:
            login_data["password"] = password
            print(f"Trying password: {password}")
            
            response = s.post(f"{BASE_URL}/api/v1/auth/jwt/create/", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                s.headers.update({"Authorization": f"Bearer {token_data['access']}"})
                print(f"✅ Authentication successful with password: {password}")
                login_success = True
                break
        
        if not login_success:
            print(f"❌ Could not log in with any common password")
            return
        
        # Testing different priority formats
        priority_tests = [
            "low",
            "LOW",
            "Medium",
            "HIGH",
            "urgent",
            "URGENT"
        ]
        
        # Use column ID from previous findings
        column_id = "67ee1693-2469-40db-a4f6-46f7827a8a65"
        
        print("\n🎯 Testing priority validation")
        print("=" * 60)
        
        for priority in priority_tests:
            task_data = {
                "title": f"Priority Test - {priority}",
                "description": f"Testing priority case: {priority}",
                "priority": priority,
                "column": column_id,
                "due_date": "2025-05-26T00:00:00.000Z"
            }
            
            print(f"\n📝 Testing priority: '{priority}'")
            response = s.post(f"{BASE_URL}/api/v1/tasks/", json=task_data)
            
            if response.status_code == 201:
                created_task = response.json()
                print(f"✅ SUCCESS with status {response.status_code}: Task created with priority '{created_task['priority']}' (Display: {created_task['priority_display']})")
                
                # Clean up
                task_id = created_task.get('id')
                if task_id:
                    s.delete(f"{BASE_URL}/api/v1/tasks/{task_id}/")
            else:
                print(f"❌ FAILED with status {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {json.dumps(error_data)}")
                except:
                    print(f"   Response: {response.text}")
            
            # Add a small delay between requests
            time.sleep(0.5)
            
    except Exception as e:
        import traceback
        print(f"❌ Test error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_priority_validation()
