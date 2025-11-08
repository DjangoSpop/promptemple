#!/usr/bin/env python
"""
Test script for Ask-Me API endpoints
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.urls import reverse


def test_askme_endpoints():
    """Test Ask-Me API endpoints without authentication"""
    print("🧪 Testing Ask-Me API Endpoints")
    print("=" * 50)

    client = Client()

    try:
        # Test 1: Start a new session
        print("1. Testing /askme/start/ endpoint...")

        start_url = reverse('ai_services_v2:askme-start')
        print(f"   URL: {start_url}")

        start_data = {
            'intent': 'Create an email to invite partners to an AI webinar'
        }

        response = client.post(
            start_url,
            data=json.dumps(start_data),
            content_type='application/json'
        )

        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.content.decode()[:200]}...")

        if response.status_code == 200:
            print("✅ Start endpoint working!")
            response_data = json.loads(response.content)
            session_id = response_data.get('session_id')

            # Test 2: Answer a question (if questions were generated)
            if response_data.get('questions'):
                print("\n2. Testing /askme/answer/ endpoint...")

                answer_url = reverse('ai_services_v2:askme-answer')
                first_question = response_data['questions'][0]

                answer_data = {
                    'session_id': session_id,
                    'qid': first_question['qid'],
                    'value': 'business executives'
                }

                answer_response = client.post(
                    answer_url,
                    data=json.dumps(answer_data),
                    content_type='application/json'
                )

                print(f"   Status: {answer_response.status_code}")
                print(f"   Response: {answer_response.content.decode()[:200]}...")

                if answer_response.status_code == 200:
                    print("✅ Answer endpoint working!")
                else:
                    print(f"❌ Answer endpoint failed: {answer_response.status_code}")

            # Test 3: Finalize session
            print("\n3. Testing /askme/finalize/ endpoint...")

            finalize_url = reverse('ai_services_v2:askme-finalize')
            finalize_data = {
                'session_id': session_id
            }

            finalize_response = client.post(
                finalize_url,
                data=json.dumps(finalize_data),
                content_type='application/json'
            )

            print(f"   Status: {finalize_response.status_code}")
            print(f"   Response: {finalize_response.content.decode()[:200]}...")

            if finalize_response.status_code == 200:
                print("✅ Finalize endpoint working!")
            else:
                print(f"❌ Finalize endpoint failed: {finalize_response.status_code}")

            # Test 4: Session list
            print("\n4. Testing /askme/sessions/ endpoint...")

            sessions_url = reverse('ai_services_v2:askme-sessions-list')
            sessions_response = client.get(sessions_url)

            print(f"   Status: {sessions_response.status_code}")
            print(f"   Response length: {len(sessions_response.content)}")

            if sessions_response.status_code == 200:
                print("✅ Sessions list endpoint working!")
                sessions_data = json.loads(sessions_response.content)
                print(f"   Found {len(sessions_data)} sessions")
            else:
                print(f"❌ Sessions endpoint failed: {sessions_response.status_code}")

        else:
            print(f"❌ Start endpoint failed: {response.status_code}")
            print(f"   Error: {response.content.decode()}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("🎯 API Test Complete")


if __name__ == "__main__":
    test_askme_endpoints()