#!/usr/bin/env python3
"""
SSE Chat Setup & Testing Automation
===================================

This script helps automate the setup and testing of the SSE chat implementation.

Features:
- Check system dependencies
- Validate configuration
- Extract JWT token from database
- Run comprehensive tests
- Generate reports

Usage:
    python setup_sse_testing.py [--extract-token] [--run-tests] [--full-setup]
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

class SSESetupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.manage_py = self.project_root / "manage.py"
        
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            'django',
            'djangorestframework',
            'channels',
            'httpx',
            'aiohttp',
            'django-cors-headers'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} (missing)")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("   Run: pip install -r requirements.txt")
            return False
        
        print("✅ All dependencies installed")
        return True
    
    def check_configuration(self):
        """Check if SSE configuration is properly set."""
        print("\n🔧 Checking configuration...")
        
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("❌ .env file not found")
            return False
        
        required_vars = [
            'ZAI_API_TOKEN',
            'ZAI_API_BASE',
            'SECRET_KEY'
        ]
        
        env_content = env_file.read_text()
        missing_vars = []
        
        for var in required_vars:
            if f"{var}=" not in env_content:
                missing_vars.append(var)
            else:
                print(f"   ✅ {var}")
        
        if missing_vars:
            print(f"   ❌ Missing variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ Configuration complete")
        return True
    
    def check_database(self):
        """Check if database is accessible and has required tables."""
        print("\n💾 Checking database...")
        
        try:
            result = subprocess.run([
                sys.executable, str(self.manage_py), "check", "--database"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Database check passed")
                return True
            else:
                print(f"❌ Database check failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Database check error: {e}")
            return False
    
    def extract_jwt_token(self, username=None):
        """Extract JWT token for testing."""
        print("\n🔑 Extracting JWT token...")
        
        if not username:
            # Try to find a user
            try:
                result = subprocess.run([
                    sys.executable, str(self.manage_py), "shell", "-c",
                    "from django.contrib.auth.models import User; "
                    "user = User.objects.filter(is_active=True).first(); "
                    "print(user.username if user else 'NO_USER')"
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode == 0:
                    username = result.stdout.strip()
                    if username == "NO_USER":
                        print("❌ No active users found in database")
                        print("   Create a user with: python manage.py createsuperuser")
                        return None
                else:
                    print(f"❌ Failed to find user: {result.stderr}")
                    return None
                    
            except Exception as e:
                print(f"❌ Error finding user: {e}")
                return None
        
        # Generate JWT token
        try:
            script = f"""
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import AccessToken
import json

try:
    user = User.objects.get(username='{username}')
    token = AccessToken.for_user(user)
    print(json.dumps({{'token': str(token), 'user_id': str(user.id), 'username': user.username}}))
except User.DoesNotExist:
    print(json.dumps({{'error': 'User not found'}}))
except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"""
            
            result = subprocess.run([
                sys.executable, str(self.manage_py), "shell", "-c", script
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout.strip())
                    if 'error' in data:
                        print(f"❌ Token generation failed: {data['error']}")
                        return None
                    else:
                        print(f"✅ JWT token generated for user: {data['username']}")
                        return data['token']
                except json.JSONDecodeError:
                    print(f"❌ Failed to parse token response: {result.stdout}")
                    return None
            else:
                print(f"❌ Token generation failed: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Token extraction error: {e}")
            return None
    
    def start_server(self):
        """Start Django development server."""
        print("\n🚀 Starting Django server...")
        
        try:
            # Check if server is already running
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            
            if result == 0:
                print("✅ Server already running on localhost:8000")
                return True
            
            # Start server in background
            process = subprocess.Popen([
                sys.executable, str(self.manage_py), "runserver", "8000"
            ], cwd=self.project_root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait a moment for server to start
            import time
            time.sleep(3)
            
            # Check if server started
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 8000))
            sock.close()
            
            if result == 0:
                print("✅ Server started successfully on localhost:8000")
                return True
            else:
                print("❌ Server failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Server start error: {e}")
            return False
    
    def run_tests(self, jwt_token):
        """Run SSE tests with the provided JWT token."""
        print("\n🧪 Running SSE tests...")
        
        env = os.environ.copy()
        env['JWT_TOKEN'] = jwt_token
        env['BASE_URL'] = 'http://localhost:8000'
        
        try:
            result = subprocess.run([
                sys.executable, str(self.project_root / "test_sse_production.py")
            ], env=env, cwd=self.project_root)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            return False
    
    def generate_report(self):
        """Generate a setup and test report."""
        print("\n📋 Generating system report...")
        
        report = {
            "timestamp": "2025-09-07",
            "python_version": sys.version,
            "project_root": str(self.project_root),
            "checks": {}
        }
        
        # Run all checks
        report["checks"]["dependencies"] = self.check_dependencies()
        report["checks"]["configuration"] = self.check_configuration()
        report["checks"]["database"] = self.check_database()
        
        # Save report
        report_file = self.project_root / "sse_setup_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Report saved to: {report_file}")
        return report

def main():
    parser = argparse.ArgumentParser(description="SSE Chat Setup & Testing")
    parser.add_argument('--extract-token', action='store_true', help='Extract JWT token for testing')
    parser.add_argument('--run-tests', action='store_true', help='Run comprehensive tests')
    parser.add_argument('--full-setup', action='store_true', help='Run complete setup and testing')
    parser.add_argument('--username', help='Username for JWT token extraction')
    parser.add_argument('--start-server', action='store_true', help='Start Django development server')
    
    args = parser.parse_args()
    
    setup_manager = SSESetupManager()
    
    if args.full_setup:
        print("🚀 Running full SSE setup and testing...")
        print("=" * 60)
        
        # Generate report
        report = setup_manager.generate_report()
        
        # Check if all systems are ready
        all_checks_passed = all(report["checks"].values())
        
        if not all_checks_passed:
            print("\n❌ System checks failed. Please fix the issues above.")
            sys.exit(1)
        
        # Extract token
        jwt_token = setup_manager.extract_jwt_token(args.username)
        if not jwt_token:
            print("\n❌ Failed to extract JWT token")
            sys.exit(1)
        
        # Start server if needed
        if args.start_server:
            server_ok = setup_manager.start_server()
            if not server_ok:
                print("\n❌ Failed to start server")
                sys.exit(1)
        
        # Run tests
        tests_passed = setup_manager.run_tests(jwt_token)
        
        print("\n" + "=" * 60)
        if tests_passed:
            print("🎉 Full setup and testing completed successfully!")
            print("✅ SSE chat implementation is ready for production")
        else:
            print("❌ Tests failed. Please check the implementation.")
            sys.exit(1)
    
    elif args.extract_token:
        token = setup_manager.extract_jwt_token(args.username)
        if token:
            print(f"\n🔑 JWT Token: {token}")
            print("\nTo use this token for testing:")
            print(f"export JWT_TOKEN='{token}'")
            print("python test_sse_production.py")
    
    elif args.run_tests:
        jwt_token = os.getenv('JWT_TOKEN')
        if not jwt_token:
            print("❌ JWT_TOKEN environment variable not set")
            print("   Use --extract-token to get a token first")
            sys.exit(1)
        
        tests_passed = setup_manager.run_tests(jwt_token)
        sys.exit(0 if tests_passed else 1)
    
    elif args.start_server:
        setup_manager.start_server()
    
    else:
        # Default: run system checks
        setup_manager.generate_report()

if __name__ == "__main__":
    main()