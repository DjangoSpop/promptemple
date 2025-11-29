"""
Script to create test users for frontend testing
"""
from django.contrib.auth import get_user_model

User = get_user_model()

# Create test users
test_users = [
    {
        'username': 'testuser',
        'email': 'testuser@prompttemple.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'TestUser123!'
    },
    {
        'username': 'demouser',
        'email': 'demo@prompttemple.com',
        'first_name': 'Demo',
        'last_name': 'User',
        'password': 'DemoUser123!'
    },
    {
        'username': 'premiumuser',
        'email': 'premium@prompttemple.com',
        'first_name': 'Premium',
        'last_name': 'User',
        'password': 'Premium123!',
        'is_premium': True
    }
]

for user_data in test_users:
    password = user_data.pop('password')
    user, created = User.objects.get_or_create(
        username=user_data['username'],
        defaults=user_data
    )
    if created:
        user.set_password(password)
        user.save()
        print(f'✅ Created user: {user.username} ({user.email})')
    else:
        print(f'ℹ️  User already exists: {user.username} ({user.email})')

print('\n🎉 Test users setup complete!')
print('\nTest Credentials:')
print('==================')
print('1. testuser / TestUser123!')
print('2. demouser / DemoUser123!')
print('3. premiumuser / Premium123!')
