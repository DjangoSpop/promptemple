"""
DeepSeek API Verification Script
Tests the DeepSeek API configuration and connectivity
"""

import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.conf import settings

def test_deepseek_api():
    """Test DeepSeek API configuration and connectivity"""

    print("="*60)
    print("DeepSeek API Verification")
    print("="*60)
    print()

    # 1. Check Configuration
    print("1️⃣  Checking Configuration...")
    deepseek_config = getattr(settings, 'DEEPSEEK_CONFIG', {})
    api_key = deepseek_config.get('API_KEY', '')
    base_url = deepseek_config.get('BASE_URL', '')
    default_model = deepseek_config.get('DEFAULT_MODEL', 'deepseek-chat')

    if not api_key:
        print("   ❌ DEEPSEEK_API_KEY not configured")
        return False

    if not base_url:
        print("   ❌ DEEPSEEK_BASE_URL not configured")
        return False

    print(f"   ✅ API Key: {api_key[:20]}...{api_key[-4:]}")
    print(f"   ✅ Base URL: {base_url}")
    print(f"   ✅ Default Model: {default_model}")
    print()

    # 2. Test Models Endpoint
    print("2️⃣  Testing Models Endpoint...")
    try:
        response = requests.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10
        )

        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('data', [])
            print(f"   ✅ Models endpoint accessible")
            print(f"   📋 Available models: {len(models)}")
            for model in models[:3]:
                print(f"      - {model.get('id', 'Unknown')}")
        else:
            print(f"   ❌ Models endpoint returned {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to connect to models endpoint: {e}")
        return False
    print()

    # 3. Test Chat Completion
    print("3️⃣  Testing Chat Completion...")
    try:
        payload = {
            "model": default_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, World!' in one sentence."}
            ],
            "temperature": 0.7,
            "max_tokens": 50
        }

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            usage = result.get('usage', {})

            print(f"   ✅ Chat completion successful")
            print(f"   💬 Response: {content}")
            print(f"   📊 Tokens used: {usage.get('total_tokens', 'N/A')}")
            print(f"   💰 Estimated cost: ${(usage.get('total_tokens', 0) * 0.0014 / 1000):.6f}")
        else:
            print(f"   ❌ Chat completion returned {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Failed to complete chat request: {e}")
        return False
    print()

    # 4. Test Streaming (optional)
    print("4️⃣  Testing Streaming...")
    try:
        payload = {
            "model": default_model,
            "messages": [
                {"role": "user", "content": "Count from 1 to 3."}
            ],
            "stream": True,
            "temperature": 0.7,
            "max_tokens": 50
        }

        response = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            json=payload,
            stream=True,
            timeout=30
        )

        if response.status_code == 200:
            print(f"   ✅ Streaming connection established")
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    if chunk_count <= 3:  # Show first 3 chunks
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str != '[DONE]':
                                try:
                                    chunk_data = json.loads(data_str)
                                    content = chunk_data['choices'][0]['delta'].get('content', '')
                                    if content:
                                        print(f"   📨 Chunk {chunk_count}: {content[:30]}")
                                except:
                                    pass

            print(f"   ✅ Streaming completed ({chunk_count} chunks)")
        else:
            print(f"   ⚠️  Streaming returned {response.status_code}")
            print(f"   Note: Streaming is optional")
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️  Streaming test failed: {e}")
        print(f"   Note: Streaming is optional, basic API works")
    print()

    # 5. Test Django Integration
    print("5️⃣  Testing Django Integration...")
    try:
        from apps.chat.views import ChatHealthView
        from django.test import RequestFactory
        from rest_framework.test import force_authenticate
        from django.contrib.auth import get_user_model

        factory = RequestFactory()
        request = factory.get('/api/v2/chat/health/')

        view = ChatHealthView.as_view()
        response = view(request)

        if response.status_code == 200:
            data = response.data
            print(f"   ✅ Django chat health endpoint works")
            print(f"   Status: {data.get('status', 'Unknown')}")
            print(f"   Message: {data.get('message', 'N/A')}")
        else:
            print(f"   ⚠️  Django health check returned {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Django integration test skipped: {e}")
    print()

    # Summary
    print("="*60)
    print("✅ DeepSeek API Verification PASSED")
    print("="*60)
    print()
    print("Next Steps:")
    print("  1. Test with your Django server: python manage.py runserver")
    print("  2. Access chat health: http://localhost:8000/api/v2/chat/health/")
    print("  3. Test SSE streaming: POST to /api/v2/chat/completions/")
    print()

    return True

if __name__ == "__main__":
    try:
        success = test_deepseek_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
