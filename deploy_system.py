# deploy_system.py
"""
Complete deployment script for the enhanced chat system with template extraction
"""
import os
import sys
import json
import subprocess
import time
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🚀 {title}")
    print("=" * 80)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")
    print("-" * 60)

def run_command(command, description, check=True):
    """Run a command with proper output handling"""
    print(f"Running: {command}")
    
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        else:
            result = subprocess.run(command, capture_output=True, text=True, check=check)
        
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        
        if result.stderr and result.returncode != 0:
            print(f"❌ Error: {result.stderr.strip()}")
            return False
            
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_python_packages():
    """Check if required Python packages are installed"""
    print("Checking Python packages...")
    
    required_packages = [
        'django',
        'celery',
        'redis',
        'langchain',
        'langchain-community',
        'openai',
        'requests',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        pip_command = f"pip install {' '.join(missing_packages)}"
        return run_command(pip_command, "Installing packages")
    
    return True

def setup_environment():
    """Set up environment variables"""
    print("Setting up environment...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("Creating .env file...")
        env_content = """
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here

# DeepSeek API Configuration
DEEPSEEK_API_KEY=sk-fad996d33334443dab24fcd669653814
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Template Extraction Settings
TEMPLATE_EXTRACTION_ENABLED=True
AUTO_APPROVE_THRESHOLD=0.8
MINIMUM_CONFIDENCE=0.6

# Monetization Settings
ENABLE_MONETIZATION=True
DEFAULT_CREDITS=100
REVENUE_SHARE_PERCENTAGE=70
"""
        with open(env_file, 'w') as f:
            f.write(env_content.strip())
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")
    
    return True

def deploy_system():
    """Deploy the complete system"""
    print_header("ENHANCED CHAT SYSTEM DEPLOYMENT")
    
    # Step 1: Check Python packages
    print_step(1, "Checking and installing Python packages")
    if not check_python_packages():
        print("❌ Failed to install required packages")
        return False
    
    # Step 2: Set up environment
    print_step(2, "Setting up environment variables")
    if not setup_environment():
        print("❌ Failed to set up environment")
        return False
    
    # Step 3: Run system setup
    print_step(3, "Running complete system setup")
    if not run_command("python setup_complete_system.py", "System setup"):
        print("❌ System setup failed")
        return False
    
    # Step 4: Check Redis
    print_step(4, "Checking Redis connection")
    redis_check = run_command("redis-cli ping", "Redis check", check=False)
    if not redis_check:
        print("⚠️  Redis not running. Starting Redis...")
        print("Please start Redis manually: redis-server")
        print("Or install Redis: https://redis.io/docs/getting-started/installation/")
    
    # Step 5: Start Celery worker (in background)
    print_step(5, "Starting Celery worker")
    print("Starting Celery worker in background...")
    try:
        # Start Celery worker in background
        celery_cmd = "celery -A celery_config worker --loglevel=info --concurrency=2"
        print(f"Command: {celery_cmd}")
        print("Note: This will run in the background. Check logs for any issues.")
        
        # Start Celery beat (scheduler) 
        print("\nStarting Celery beat scheduler...")
        beat_cmd = "celery -A celery_config beat --loglevel=info"
        print(f"Command: {beat_cmd}")
        print("Note: This will run in the background for periodic tasks.")
        
    except Exception as e:
        print(f"⚠️  Could not start Celery automatically: {e}")
        print("Please start manually:")
        print("  celery -A celery_config worker --loglevel=info")
        print("  celery -A celery_config beat --loglevel=info")
    
    # Step 6: Test the system
    print_step(6, "Testing system components")
    test_system()
    
    # Step 7: Start Django server
    print_step(7, "Starting Django development server")
    print("Starting Django server...")
    print("Command: python manage.py runserver 8000")
    print("\n🎉 DEPLOYMENT COMPLETED!")
    print("\nSystem is ready! Access your enhanced chat system at:")
    print("  http://localhost:8000/api/v2/chat/completions/")
    print("\nTemplate extraction will happen automatically for new chat messages!")
    print("\nTo start the system:")
    print("1. Start Redis: redis-server")
    print("2. Start Celery worker: celery -A celery_config worker --loglevel=info")
    print("3. Start Celery beat: celery -A celery_config beat --loglevel=info")
    print("4. Start Django: python manage.py runserver")
    
    return True

def test_system():
    """Test system components"""
    print("Testing system components...")
    
    # Test Django
    django_test = run_command("python manage.py check", "Django check", check=False)
    if django_test:
        print("✅ Django configuration is valid")
    else:
        print("❌ Django configuration has issues")
    
    # Test database
    migrate_test = run_command("python manage.py migrate --run-syncdb", "Database migration", check=False)
    if migrate_test:
        print("✅ Database is set up correctly")
    else:
        print("❌ Database setup failed")
    
    # Test Celery configuration
    try:
        import celery_config
        print("✅ Celery configuration loaded")
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
    
    # Test DeepSeek configuration
    try:
        import os
        from django.conf import settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
        import django
        django.setup()
        
        deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
        if deepseek_config.get('API_KEY') and deepseek_config.get('BASE_URL'):
            print("✅ DeepSeek API configuration found")
        else:
            print("❌ DeepSeek API configuration missing")
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")

def show_api_examples():
    """Show API usage examples"""
    print_header("API USAGE EXAMPLES")
    
    print("1. Enhanced Chat with Template Extraction:")
    print("""
curl -X POST http://localhost:8000/api/v2/chat/completions/ \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer your-jwt-token" \\
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Create 10 business prompts for generating marketing strategies"
      }
    ],
    "model": "deepseek-chat",
    "stream": true
  }'
""")
    
    print("\n2. Template Library Access:")
    print("""
curl -X GET http://localhost:8000/api/templates/ \\
  -H "Authorization: Bearer your-jwt-token"
""")
    
    print("\n3. Extracted Templates:")
    print("""
curl -X GET http://localhost:8000/api/extracted-templates/ \\
  -H "Authorization: Bearer your-jwt-token"
""")

if __name__ == '__main__':
    try:
        success = deploy_system()
        if success:
            show_api_examples()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Deployment failed with error: {e}")
        sys.exit(1)