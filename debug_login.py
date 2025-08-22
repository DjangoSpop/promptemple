#!/usr/bin/env python
"""
Debug script to test login endpoint
"""
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.serializers import UserLoginSerializer

User = get_user_model()

def test_login_endpoint():
    """Test the login endpoint"""
    base_url = "http://127.0.0.1:8000"
    login_url = f"{base_url}/api/v2/auth/login/"
    
    # Test data - these should be valid test credentials
    test_credentials = [
        {
            "username": "admin",
            "password": "admin123"
        },
        {
            "username": "test@example.com",
            "password": "testpass123"
        }
    ]
    
    print("Testing login endpoint...")
    print(f"URL: {login_url}")
    
    for creds in test_credentials:
        print(f"\nTesting credentials: {creds['username']}")
        
        try:
            response = requests.post(
                login_url,
                json=creds,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                timeout=10
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"Response Text: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")

def test_serializer_directly():
    """Test the login serializer directly"""
    print("\n" + "="*50)
    print("Testing UserLoginSerializer directly...")
    
    test_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    serializer = UserLoginSerializer(data=test_data)
    print(f"Serializer valid: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print(f"Serializer errors: {serializer.errors}")
    else:
        print(f"Validated data: {serializer.validated_data}")

def check_existing_users():
    """Check what users exist in the database"""
    print("\n" + "="*50)
    print("Checking existing users...")
    
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    for user in users[:5]:  # Show first 5 users
        print(f"- {user.username} ({user.email}) - Active: {user.is_active}")

if __name__ == "__main__":
    check_existing_users()
    test_serializer_directly()
    test_login_endpoint()