#!/usr/bin/env python
"""
Create development users for testing
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_dev_users():
    """Create development users with known passwords"""
    
    dev_users = [
        {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'test123',
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True
        },
        {
            'username': 'developer',
            'email': 'dev@promptcraft.app',
            'password': 'dev123',
            'first_name': 'Developer',
            'last_name': 'User',
            'is_active': True
        }
    ]
    
    for user_data in dev_users:
        username = user_data['username']
        email = user_data['email']
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            # Update the password to a known one
            user.set_password(user_data['password'])
            user.email = email
            user.first_name = user_data['first_name']
            user.last_name = user_data['last_name']
            user.is_active = True
            user.save()
            print(f"✅ Updated existing user: {username} with password: {user_data['password']}")
        else:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            user.is_active = True
            user.save()
            print(f"✅ Created new user: {username} with password: {user_data['password']}")

def list_all_users():
    """List all users with their basic info"""
    print("\n" + "="*50)
    print("All users in the database:")
    print("="*50)
    
    users = User.objects.all().order_by('username')
    for user in users:
        print(f"👤 {user.username} ({user.email}) - Active: {user.is_active}")
    
    print(f"\nTotal users: {users.count()}")

if __name__ == "__main__":
    print("Creating/updating development users...")
    create_dev_users()
    list_all_users()
    
    print("\n" + "="*50)
    print("🎯 Test these credentials in your frontend:")
    print("Username: testuser, Password: test123")
    print("Username: developer, Password: dev123") 
    print("Username: admin, Password: admin123")
    print("="*50)