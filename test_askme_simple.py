#!/usr/bin/env python
"""
Simple test script for Ask-Me system basic functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.ai_services.models import AskMeSession, AskMeQuestion
from django.urls import reverse


def test_models():
    """Test the database models"""
    print("🗄️  Testing Database Models")
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
        print(f"   Session spec: {session.spec}")

        # Test model methods
        print("\n2. Testing model methods...")

        question.mark_answered("test answer")
        completion = session.get_completion_percentage()

        print(f"✅ Model methods working:")
        print(f"   Question answered: {question.is_answered}")
        print(f"   Answer: {question.answer}")
        print(f"   Session spec after answer: {session.spec}")
        print(f"   Completion: {completion:.1%}")

        # Test question serialization
        print("\n3. Testing question serialization...")
        question_dict = question.to_dict()
        print(f"✅ Question serialization:")
        print(f"   Dict keys: {list(question_dict.keys())}")

        # Clean up
        session.delete()
        print("\n✅ Cleanup completed")

        print("\n🎯 Database models are working correctly!")
        return {"success": True}

    except Exception as e:
        print(f"\n❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_urls():
    """Test URL configuration"""
    print("\n🌐 Testing URL Configuration")
    print("=" * 50)

    try:
        # Test URL reversing
        print("1. Testing URL reversal...")

        urls = {
            'start': 'ai_services_v2:askme-start',
            'answer': 'ai_services_v2:askme-answer',
            'finalize': 'ai_services_v2:askme-finalize',
            'stream': 'ai_services_v2:askme-stream',
            'sessions': 'ai_services_v2:askme-sessions-list',
        }

        resolved_urls = {}
        for name, pattern in urls.items():
            try:
                url = reverse(pattern)
                resolved_urls[name] = url
                print(f"✅ {name}: {url}")
            except Exception as e:
                print(f"❌ {name}: Failed to reverse - {e}")
                return {"success": False, "error": f"URL {name} failed: {e}"}

        print(f"\n✅ All URLs resolved successfully!")
        return {"success": True, "urls": resolved_urls}

    except Exception as e:
        print(f"\n❌ URL test failed: {e}")
        return {"success": False, "error": str(e)}


def test_service_import():
    """Test service import and basic initialization"""
    print("\n🔧 Testing Service Import")
    print("=" * 50)

    try:
        print("1. Testing service imports...")

        # Test imports
        from apps.ai_services.askme_service import AskMeService, QuestionSpec, PlannerResult, ComposerResult
        print("✅ Service classes imported successfully")

        # Test dataclass creation
        print("\n2. Testing dataclass creation...")

        question_spec = QuestionSpec(
            qid="test",
            title="Test Question",
            help_text="Test help",
            kind="short_text",
            options=[],
            variable="test_var",
            required=True,
            suggested=""
        )
        print(f"✅ QuestionSpec created: {question_spec.title}")

        planner_result = PlannerResult(
            questions=[question_spec],
            good_enough_to_run=False,
            metadata={}
        )
        print(f"✅ PlannerResult created with {len(planner_result.questions)} questions")

        composer_result = ComposerResult(
            prompt="Test prompt",
            metadata={}
        )
        print(f"✅ ComposerResult created: {composer_result.prompt[:20]}...")

        print("\n🎯 Service imports and basic structures working!")
        return {"success": True}

    except Exception as e:
        print(f"\n❌ Service import test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def test_view_imports():
    """Test view imports"""
    print("\n📡 Testing View Imports")
    print("=" * 50)

    try:
        print("1. Testing view imports...")

        from apps.ai_services.askme_views import (
            AskMeStartView, AskMeAnswerView, AskMeFinalizeView, AskMeStreamView,
            askme_start_api, askme_answer_api, askme_finalize_api, askme_stream_api
        )
        print("✅ All view classes and functions imported successfully")

        print("\n2. Testing serializer imports...")
        from apps.ai_services.serializers import (
            AskMeSessionSerializer, AskMeQuestionSerializer,
            AskMeStartRequestSerializer, AskMeStartResponseSerializer
        )
        print("✅ All serializers imported successfully")

        print("\n🎯 View imports working correctly!")
        return {"success": True}

    except Exception as e:
        print(f"\n❌ View import test failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def main():
    """Run all basic tests"""
    print("🚀 Ask-Me System Basic Test Suite")
    print("=" * 60)

    results = {}

    # Test models
    print("\n📋 Phase 1: Model Testing")
    results['models'] = test_models()

    # Test URLs
    print("\n📋 Phase 2: URL Testing")
    results['urls'] = test_urls()

    # Test service imports
    print("\n📋 Phase 3: Service Import Testing")
    results['service'] = test_service_import()

    # Test view imports
    print("\n📋 Phase 4: View Import Testing")
    results['views'] = test_view_imports()

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

    print("\n" + ("🎉 ALL BASIC TESTS PASSED!" if all_passed else "❌ SOME TESTS FAILED"))

    if all_passed:
        print("\n🎯 Next Steps:")
        print("1. Set up proper API keys for DeepSeek/OpenAI")
        print("2. Test the full async workflow")
        print("3. Test the API endpoints with real requests")
        print("4. Integrate with frontend")

    print("=" * 60)

    return results


if __name__ == "__main__":
    main()