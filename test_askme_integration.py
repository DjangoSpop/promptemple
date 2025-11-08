#!/usr/bin/env python
"""
Test script for Ask-Me system integration
"""

import os
import sys
import django
import asyncio
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.ai_services.models import AskMeSession, AskMeQuestion
from apps.ai_services.askme_service import get_askme_service


async def test_askme_flow():
    """Test the complete Ask-Me flow"""
    print("🧪 Testing Ask-Me Prompt Builder Integration")
    print("=" * 50)

    try:
        # 1. Test service initialization
        print("1. Testing service initialization...")
        service = get_askme_service()
        print("✅ Service initialized successfully")

        # 2. Test session creation
        print("\n2. Testing session creation...")
        intent = "Create an email to invite our partners to a webinar on AI security"

        session = AskMeSession.objects.create(intent=intent)
        session.initialize_spec()
        print(f"✅ Session created: {session.id}")
        print(f"   Intent: {intent}")
        print(f"   Initial spec: {session.spec}")

        # 3. Test planner
        print("\n3. Testing Planner...")
        planner_result = await service.plan_questions(intent, session.spec)
        print(f"✅ Planner generated {len(planner_result.questions)} questions")
        print(f"   Good enough to run: {planner_result.good_enough_to_run}")

        for i, question in enumerate(planner_result.questions):
            print(f"   Q{i+1}: {question.title}")
            print(f"      Variable: {question.variable}")
            print(f"      Kind: {question.kind}")
            if question.options:
                print(f"      Options: {question.options}")

        # 4. Simulate answering questions
        print("\n4. Testing question answering...")
        if planner_result.questions:
            # Answer first question (usually audience)
            first_q = planner_result.questions[0]
            test_answer = "business executives"

            # Create the question in DB
            question_obj = AskMeQuestion.objects.create(
                session=session,
                qid=first_q.qid,
                title=first_q.title,
                help_text=first_q.help_text,
                variable=first_q.variable,
                kind=first_q.kind,
                options=first_q.options,
                is_required=first_q.required,
                suggested_answer=first_q.suggested
            )

            # Mark as answered
            question_obj.mark_answered(test_answer)
            print(f"✅ Answered question: {first_q.title}")
            print(f"   Answer: {test_answer}")
            print(f"   Updated spec: {session.spec}")

            # Plan next questions
            next_planner_result = await service.plan_questions(intent, session.spec)
            print(f"✅ Next planning generated {len(next_planner_result.questions)} questions")

        # 5. Test composer with current spec
        print("\n5. Testing Composer...")
        composer_result = await service.compose_prompt(session.spec)
        print("✅ Composer generated final prompt:")
        print("─" * 40)
        print(composer_result.prompt)
        print("─" * 40)

        # 6. Test session completion
        print("\n6. Testing session completion...")
        session.final_prompt = composer_result.prompt
        session.is_complete = True
        session.save()
        print(f"✅ Session marked as complete")
        print(f"   Completion percentage: {session.get_completion_percentage():.1%}")

        print("\n🎉 All tests passed! Ask-Me system is working correctly.")

        return {
            "success": True,
            "session_id": str(session.id),
            "questions_generated": len(planner_result.questions),
            "final_prompt_length": len(composer_result.prompt),
            "completion_percentage": session.get_completion_percentage()
        }

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_api_endpoints():
    """Test the API endpoints"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)

    try:
        from django.test import Client
        from django.urls import reverse

        client = Client()

        # Test /askme/start endpoint structure
        print("1. Testing endpoint URLs...")

        # Check if URLs are properly configured
        from django.urls import resolve

        start_url = reverse('ai_services_v2:askme-start')
        answer_url = reverse('ai_services_v2:askme-answer')
        finalize_url = reverse('ai_services_v2:askme-finalize')
        stream_url = reverse('ai_services_v2:askme-stream')

        print(f"✅ URLs configured:")
        print(f"   Start: {start_url}")
        print(f"   Answer: {answer_url}")
        print(f"   Finalize: {finalize_url}")
        print(f"   Stream: {stream_url}")

        print("\n🎯 API endpoints are properly configured!")

        return {"success": True, "endpoints_configured": True}

    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        return {"success": False, "error": str(e)}


def test_models():
    """Test the database models"""
    print("\n🗄️  Testing Database Models")
    print("=" * 50)

    try:
        # Test model creation
        print("1. Testing model creation...")

        session = AskMeSession.objects.create(
            intent="Test intent for model validation"
        )
        session.initialize_spec()

        question = AskMeQuestion.objects.create(
            session=session,
            qid="test_q1",
            title="Test Question",
            variable="test_var",
            kind="short_text"
        )

        print(f"✅ Models created successfully:")
        print(f"   Session ID: {session.id}")
        print(f"   Question ID: {question.id}")

        # Test model methods
        print("\n2. Testing model methods...")

        question.mark_answered("test answer")
        completion = session.get_completion_percentage()

        print(f"✅ Model methods working:")
        print(f"   Question answered: {question.is_answered}")
        print(f"   Completion: {completion:.1%}")

        # Clean up
        session.delete()

        print("\n🎯 Database models are working correctly!")

        return {"success": True}

    except Exception as e:
        print(f"\n❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def main():
    """Run all tests"""
    print("🚀 Ask-Me System Integration Test Suite")
    print("=" * 60)

    results = {}

    # Test models first
    print("\n📋 Phase 1: Model Testing")
    results['models'] = test_models()

    # Test API endpoints
    print("\n📋 Phase 2: API Testing")
    results['api'] = await test_api_endpoints()

    # Test full flow
    print("\n📋 Phase 3: Integration Testing")
    results['integration'] = await test_askme_flow()

    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)

    all_passed = all(result.get('success', False) for result in results.values())

    for test_name, result in results.items():
        status = "✅ PASS" if result.get('success') else "❌ FAIL"
        print(f"{test_name.upper()}: {status}")
        if not result.get('success') and 'error' in result:
            print(f"  Error: {result['error']}")

    print("\n" + ("🎉 ALL TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(main())