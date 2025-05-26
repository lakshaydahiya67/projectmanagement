#!/usr/bin/env python
import requests
import json
import sys

BASE_URL = 'http://127.0.0.1:8000/api/v1'
project_id = '93056c8a-c381-4da3-9eb5-471c917b8e83'

def login():
    """Get authentication token"""
    username = input("Enter your username: ")
    password = input("Enter your password: ")
    
    login_url = f"{BASE_URL}/auth/jwt/create/"
    login_data = {
        "username": username,
        "password": password
    }
    
    print(f"Logging in as {username}...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"Login failed: {response.status_code}")
        print(response.json())
        return None
    
    tokens = response.json()
    access_token = tokens.get('access')
    
    if not access_token:
        print("No access token received.")
        return None
    
    print("Login successful, access token received.")
    return access_token

def test_endpoints(token):
    """Test the previously failing endpoints"""
    headers = {
        'Authorization': f'JWT {token}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Project tasks endpoint
    print('\n1. Testing project tasks endpoint...')
    tasks_url = f'{BASE_URL}/projects/{project_id}/tasks/'
    response = requests.get(tasks_url, headers=headers)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print('Success! Tasks endpoint is working')
    else:
        print('Error response:', response.text)
    
    # Test 2: Project members endpoint
    print('\n2. Testing project members endpoint...')
    members_url = f'{BASE_URL}/projects/{project_id}/members/'
    response = requests.get(members_url, headers=headers)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print('Success! Members endpoint is working')
    else:
        print('Error response:', response.text)
    
    # Test 3: Project activity logs endpoint
    print('\n3. Testing project activity logs endpoint...')
    logs_url = f'{BASE_URL}/projects/{project_id}/activity_logs/'
    response = requests.get(logs_url, headers=headers)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print('Success! Activity logs endpoint is working')
    else:
        print('Error response:', response.text)
    
    # Test 4: Add member endpoint
    print('\n4. Testing add member endpoint...')
    add_member_url = f'{BASE_URL}/projects/{project_id}/add_member/'
    response = requests.post(add_member_url, headers=headers, json={'user': 1, 'role': 'member'})
    print(f'Status: {response.status_code}')
    print('Response:', response.text)

if __name__ == "__main__":
    token = login()
    if token:
        test_endpoints(token)
