#!/usr/bin/env python
"""
Test API endpoint directly with requests to check authentication
"""
import os
import sys
import django
import requests
from pprint import pprint

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
django.setup()

from django.conf import settings

# Test token from the failed request
test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU3MzU2ODI4LCJpYXQiOjE3NTcyNzA0MjgsImp0aSI6ImJjMTUzY2Q0MmY3ZjRjMDI5MTRiOWYyMTNmYjA4NjYzIiwidXNlcl9pZCI6IjFhMDA1YTViLTdlYTgtNDMzZC04ZGRmLWU2NzY2ODlmMTFkZSJ9.6usiGIA65JxRzio8MltXe8nT1OWsWeukEa_qmYX8kAw"

def test_api_endpoints():
    """Test various API endpoints to debug authentication"""
    print("=== API Authentication Test ===")
    
    base_url = "http://127.0.0.1:8000"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {test_token}"
    }
    
    # Test endpoints
    endpoints = [
        ("/api/v2/chat/completions/", "POST", {"messages": [{"role": "user", "content": "Hello"}]}),
        ("/api/v2/chat/health/", "GET", None),
        ("/api/auth/users/me/", "GET", None),
    ]
    
    for endpoint, method, payload in endpoints:
        print(f"\n--- Testing {method} {endpoint} ---")
        
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(f"{base_url}{endpoint}", headers=headers, json=payload, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"Response: {response_json}")
            except:
                print(f"Response Text: {response.text[:500]}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test without authentication
    print(f"\n--- Testing without authentication ---")
    try:
        response = requests.get(f"{base_url}/api/v2/chat/health/", timeout=10)
        print(f"Health endpoint without auth - Status: {response.status_code}")
        try:
            print(f"Response: {response.json()}")
        except:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()