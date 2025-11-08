#!/usr/bin/env python
"""
Quick test for Ask-Me API endpoint
"""

import requests
import json

def test_askme_start():
    """Test the /askme/start/ endpoint"""
    print("🧪 Testing Ask-Me Start Endpoint")
    print("=" * 40)

    url = "http://127.0.0.1:8000/api/v2/ai/askme/start/"

    data = {
        "intent": "Create an email to invite partners to an AI webinar"
    }

    try:
        print(f"📤 POST {url}")
        print(f"📊 Data: {data}")

        response = requests.post(url, json=data, timeout=30)

        print(f"📈 Status: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS!")
            print(f"📝 Session ID: {result.get('session_id')}")
            print(f"❓ Questions: {len(result.get('questions', []))}")
            print(f"🎯 Good enough: {result.get('good_enough_to_run')}")

            if result.get('questions'):
                print("\n📋 Generated Questions:")
                for i, q in enumerate(result['questions'][:3]):  # Show first 3
                    print(f"  {i+1}. {q.get('title')}")
                    print(f"     Variable: {q.get('variable')}")
                    print(f"     Kind: {q.get('kind')}")

            return result
        else:
            print("❌ FAILED!")
            print(f"📄 Response: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_askme_debug():
    """Test the debug endpoint"""
    print("\n🔧 Testing Ask-Me Debug Endpoint")
    print("=" * 40)

    url = "http://127.0.0.1:8000/api/v2/ai/askme/debug/"

    try:
        response = requests.get(url, timeout=10)
        print(f"📈 Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ DEBUG SUCCESS!")
            print(f"📝 Message: {result.get('message')}")
            print(f"🔐 Permissions: {result.get('permissions_working')}")
            return True
        else:
            print("❌ DEBUG FAILED!")
            print(f"📄 Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ask-Me Quick Test")
    print("=" * 50)

    # Test debug endpoint first
    debug_ok = test_askme_debug()

    if debug_ok:
        # Test main functionality
        result = test_askme_start()

        if result:
            print(f"\n🎉 SUCCESS! Ask-Me system is working!")
        else:
            print(f"\n❌ Ask-Me start failed")
    else:
        print(f"\n❌ Debug endpoint failed - check server")

    print("=" * 50)