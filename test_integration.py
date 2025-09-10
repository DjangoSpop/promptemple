#!/usr/bin/env python
"""
Comprehensive setup and testing script for PromptCraft WebSocket and AI integration
Tests all components: Sentry, WebSocket, LangChain, Search, and Daphne
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(message: str, color: str = Colors.WHITE):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.END}")

def print_header(title: str):
    """Print section header"""
    print_colored(f"\n{'='*60}", Colors.CYAN)
    print_colored(f"{title.center(60)}", Colors.BOLD + Colors.CYAN)
    print_colored(f"{'='*60}", Colors.CYAN)

def print_step(step: str, status: str = "INFO"):
    """Print step with status"""
    color = Colors.GREEN if status == "SUCCESS" else Colors.RED if status == "ERROR" else Colors.YELLOW
    print_colored(f"[{status}] {step}", color)

class SystemChecker:
    """Check system requirements and dependencies"""
    
    def __init__(self):
        self.results = {}
        
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        print_step("Checking Python version...")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            print_step(f"Python {version.major}.{version.minor}.{version.micro} - Compatible", "SUCCESS")
            self.results['python'] = True
            return True
        else:
            print_step(f"Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+", "ERROR")
            self.results['python'] = False
            return False
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if required packages are installed"""
        print_step("Checking Python dependencies...")
        
        dependencies = {
            'django': 'Django',
            'channels': 'Django Channels',
            'daphne': 'Daphne ASGI Server',
            'redis': 'Redis Python Client',
            'sentry_sdk': 'Sentry SDK',
            'langchain': 'LangChain',
            'openai': 'OpenAI Python Client',
        }
        
        results = {}
        for package, name in dependencies.items():
            try:
                __import__(package)
                print_step(f"{name} - Available", "SUCCESS")
                results[package] = True
            except ImportError:
                print_step(f"{name} - Missing", "ERROR")
                results[package] = False
        
        self.results['dependencies'] = results
        return results
    
    def check_redis_connection(self) -> bool:
        """Check if Redis is available and connectable"""
        print_step("Checking Redis connection...")
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            r.ping()
            print_step("Redis - Connected", "SUCCESS")
            self.results['redis'] = True
            return True
        except Exception as e:
            print_step(f"Redis - Connection failed: {e}", "ERROR")
            self.results['redis'] = False
            return False
    
    def check_django_setup(self) -> bool:
        """Check Django configuration"""
        print_step("Checking Django configuration...")
        
        try:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")
            import django
            django.setup()
            
            from django.conf import settings
            
            # Check critical settings
            checks = {
                'SECRET_KEY': bool(settings.SECRET_KEY),
                'DATABASES': bool(settings.DATABASES),
                'INSTALLED_APPS': 'channels' in settings.INSTALLED_APPS,
                'CHANNEL_LAYERS': hasattr(settings, 'CHANNEL_LAYERS'),
                'ASGI_APPLICATION': hasattr(settings, 'ASGI_APPLICATION')
            }
            
            all_good = True
            for setting, status in checks.items():
                if status:
                    print_step(f"Django {setting} - Configured", "SUCCESS")
                else:
                    print_step(f"Django {setting} - Missing/Invalid", "ERROR")
                    all_good = False
            
            self.results['django'] = all_good
            return all_good
            
        except Exception as e:
            print_step(f"Django configuration error: {e}", "ERROR")
            self.results['django'] = False
            return False

class WebSocketTester:
    """Test WebSocket functionality"""
    
    def __init__(self):
        self.results = {}
    
    async def test_websocket_connection(self, url: str, test_name: str) -> bool:
        """Test WebSocket connection and basic communication"""
        try:
            import websockets
            
            print_step(f"Testing WebSocket: {test_name}")
            
            async with websockets.connect(url, timeout=10) as websocket:
                # Send ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                
                if data.get("type") == "pong":
                    print_step(f"WebSocket {test_name} - Connection successful", "SUCCESS")
                    return True
                else:
                    print_step(f"WebSocket {test_name} - Unexpected response: {data}", "ERROR")
                    return False
                    
        except Exception as e:
            print_step(f"WebSocket {test_name} - Failed: {e}", "ERROR")
            return False
    
    async def run_websocket_tests(self, base_url: str = "ws://localhost:8000") -> Dict[str, bool]:
        """Run comprehensive WebSocket tests"""
        print_step("Starting WebSocket tests...")
        
        tests = {
            "prompt_chat": f"{base_url}/ws/chat/test/",
            "ai_processing": f"{base_url}/ws/ai/process/test/",
            "search": f"{base_url}/ws/search/test/",
        }
        
        results = {}
        for test_name, url in tests.items():
            try:
                result = await self.test_websocket_connection(url, test_name)
                results[test_name] = result
            except Exception as e:
                print_step(f"WebSocket test {test_name} failed: {e}", "ERROR")
                results[test_name] = False
        
        self.results = results
        return results

class SearchTester:
    """Test search functionality"""
    
    def __init__(self):
        self.results = {}
    
    def test_search_service(self) -> bool:
        """Test search service functionality"""
        print_step("Testing search service...")
        
        try:
            # Set up Django
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")
            import django
            django.setup()
            
            from apps.templates.search_services import search_service
            
            # Test basic search
            results, metrics = search_service.search_prompts(
                query="test prompt",
                max_results=5
            )
            
            print_step(f"Search returned {len(results)} results in {metrics.get('total_time_ms', 0)}ms", "SUCCESS")
            
            # Test intent-based search
            intent_results = search_service.search_by_intent("general", max_results=3)
            print_step(f"Intent search returned {len(intent_results)} results", "SUCCESS")
            
            # Test featured prompts
            featured = search_service.get_featured_prompts(max_results=3)
            print_step(f"Featured prompts: {len(featured)} results", "SUCCESS")
            
            self.results['search_service'] = True
            return True
            
        except Exception as e:
            print_step(f"Search service test failed: {e}", "ERROR")
            self.results['search_service'] = False
            return False

class LangChainTester:
    """Test LangChain integration"""
    
    def __init__(self):
        self.results = {}
    
    async def test_langchain_service(self) -> bool:
        """Test LangChain optimization service"""
        print_step("Testing LangChain service...")
        
        try:
            # Set up Django
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")
            import django
            django.setup()
            
            from apps.templates.langchain_services import LangChainOptimizationService
            
            service = LangChainOptimizationService()
            
            # Test intent processing
            intent_result = await service.process_intent("Write a professional email")
            print_step(f"Intent processing successful: {intent_result.get('category', 'unknown')}", "SUCCESS")
            
            # Test response generation
            response = await service.generate_response("Hello, can you help me?")
            print_step(f"Response generation successful: {len(response.get('content', ''))} chars", "SUCCESS")
            
            self.results['langchain'] = True
            return True
            
        except Exception as e:
            print_step(f"LangChain service test failed: {e}", "ERROR")
            self.results['langchain'] = False
            return False

class ServerTester:
    """Test server deployment"""
    
    def __init__(self):
        self.server_process = None
        self.results = {}
    
    def start_test_server(self) -> bool:
        """Start Daphne server for testing"""
        print_step("Starting test server...")
        
        try:
            # Start Daphne server
            cmd = [
                "daphne",
                "--bind", "127.0.0.1",
                "--port", "8000",
                "--verbosity", "1",
                "promptcraft.asgi:application"
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd()
            )
            
            # Wait for server to start
            time.sleep(3)
            
            if self.server_process.poll() is None:
                print_step("Test server started successfully", "SUCCESS")
                return True
            else:
                print_step("Test server failed to start", "ERROR")
                return False
                
        except Exception as e:
            print_step(f"Failed to start test server: {e}", "ERROR")
            return False
    
    def stop_test_server(self):
        """Stop test server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            print_step("Test server stopped", "SUCCESS")

def install_dependencies():
    """Install missing dependencies"""
    print_header("INSTALLING DEPENDENCIES")
    
    print_step("Installing required packages...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print_step("Dependencies installed successfully", "SUCCESS")
        return True
    except Exception as e:
        print_step(f"Failed to install dependencies: {e}", "ERROR")
        return False

async def run_comprehensive_tests():
    """Run all tests comprehensively"""
    print_header("PROMPTCRAFT SYSTEM INTEGRATION TEST")
    
    print_colored("This script will test all components of the PromptCraft system:", Colors.CYAN)
    print_colored("• System requirements and dependencies", Colors.WHITE)
    print_colored("• Django configuration", Colors.WHITE)
    print_colored("• Redis connectivity", Colors.WHITE)
    print_colored("• WebSocket functionality", Colors.WHITE)
    print_colored("• Search services", Colors.WHITE)
    print_colored("• LangChain integration", Colors.WHITE)
    print_colored("• Daphne ASGI server", Colors.WHITE)
    
    # System checks
    print_header("SYSTEM REQUIREMENTS CHECK")
    checker = SystemChecker()
    
    python_ok = checker.check_python_version()
    deps_ok = all(checker.check_dependencies().values())
    redis_ok = checker.check_redis_connection()
    django_ok = checker.check_django_setup()
    
    if not python_ok:
        print_step("Python version incompatible. Please upgrade to Python 3.8+", "ERROR")
        return False
    
    if not deps_ok:
        install_choice = input(f"\n{Colors.YELLOW}Some dependencies are missing. Install now? (y/N): {Colors.END}")
        if install_choice.lower() == 'y':
            if not install_dependencies():
                return False
        else:
            print_step("Cannot proceed without required dependencies", "ERROR")
            return False
    
    if not redis_ok:
        print_step("Redis not available. WebSocket features may be limited.", "WARNING")
    
    if not django_ok:
        print_step("Django configuration issues detected", "ERROR")
        return False
    
    # Search service tests
    print_header("SEARCH SERVICE TESTS")
    search_tester = SearchTester()
    search_ok = search_tester.test_search_service()
    
    # LangChain tests
    print_header("LANGCHAIN INTEGRATION TESTS")
    langchain_tester = LangChainTester()
    langchain_ok = await langchain_tester.test_langchain_service()
    
    # Server and WebSocket tests
    print_header("SERVER AND WEBSOCKET TESTS")
    server_tester = ServerTester()
    
    server_started = server_tester.start_test_server()
    if server_started:
        # Wait a bit more for server to be ready
        await asyncio.sleep(2)
        
        # Test WebSocket connections
        ws_tester = WebSocketTester()
        ws_results = await ws_tester.run_websocket_tests()
        
        server_tester.stop_test_server()
        ws_ok = all(ws_results.values())
    else:
        ws_ok = False
    
    # Final report
    print_header("TEST SUMMARY")
    
    all_tests = {
        "Python Version": python_ok,
        "Dependencies": deps_ok,
        "Redis Connection": redis_ok,
        "Django Configuration": django_ok,
        "Search Service": search_ok,
        "LangChain Integration": langchain_ok,
        "Server Startup": server_started,
        "WebSocket Functionality": ws_ok,
    }
    
    passed = sum(all_tests.values())
    total = len(all_tests)
    
    for test_name, result in all_tests.items():
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print_colored(f"  {test_name:.<30} {status}", color)
    
    print_colored(f"\nOverall: {passed}/{total} tests passed", 
                 Colors.GREEN if passed == total else Colors.YELLOW)
    
    if passed == total:
        print_colored("\n🎉 All systems operational! PromptCraft is ready for deployment.", Colors.GREEN + Colors.BOLD)
        print_colored("\nNext steps:", Colors.CYAN)
        print_colored("1. Set environment variables for production (SENTRY_DSN, API keys)", Colors.WHITE)
        print_colored("2. Configure SSL certificates if needed", Colors.WHITE)
        print_colored("3. Run: ./run_daphne.ps1 -Environment production", Colors.WHITE)
        print_colored("4. Monitor logs in the 'logs' directory", Colors.WHITE)
    else:
        print_colored(f"\n⚠️  {total - passed} tests failed. Please fix issues before deployment.", Colors.YELLOW + Colors.BOLD)
    
    return passed == total

def main():
    """Main execution function"""
    try:
        # Check if we're in the right directory
        if not Path("promptcraft/settings.py").exists():
            print_step("Please run this script from the project root directory", "ERROR")
            sys.exit(1)
        
        # Run tests
        success = asyncio.run(run_comprehensive_tests())
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print_colored("\n\nTest interrupted by user", Colors.YELLOW)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\nUnexpected error: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()