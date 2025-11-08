#!/usr/bin/env python
"""
Debug script to test AskMe imports and basic functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_imports():
    """Test all imports step by step"""
    print("🔍 Testing AskMe Imports")
    print("=" * 40)

    try:
        print("1. Testing model imports...")
        from apps.ai_services.models import AskMeSession, AskMeQuestion
        print("✅ Models imported successfully")

        print("2. Testing service imports...")
        from apps.ai_services.askme_service import AskMeService, get_askme_service
        print("✅ Service imports successful")

        print("3. Testing service creation...")
        service = get_askme_service()
        print("✅ Service created successfully")
        print(f"   Service fallback mode: {service.planner_chain is None}")

        print("4. Testing session creation...")
        session = AskMeSession.objects.create(
            intent="Test intent for debugging"
        )
        session.initialize_spec()
        print(f"✅ Session created: {session.id}")
        print(f"   Spec: {session.spec}")

        print("5. Testing async functionality...")
        import asyncio

        async def test_planner():
            try:
                result = await service.plan_questions("Test intent", session.spec)
                return result
            except Exception as e:
                print(f"❌ Async planner failed: {e}")
                import traceback
                traceback.print_exc()
                return None

        # Run async test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            planner_result = loop.run_until_complete(test_planner())
            if planner_result:
                print(f"✅ Planner worked! Generated {len(planner_result.questions)} questions")
                for q in planner_result.questions:
                    print(f"   - {q.title}")
            else:
                print("❌ Planner returned None")
        finally:
            loop.close()

        # Clean up
        session.delete()
        print("✅ Cleanup completed")

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_view_import():
    """Test view imports"""
    print("\n📡 Testing View Imports")
    print("=" * 40)

    try:
        from apps.ai_services.askme_views import askme_start_api
        print("✅ View import successful")

        # Test basic view structure
        print("Testing view callable...")
        print(f"✅ View is callable: {callable(askme_start_api)}")

        return True

    except Exception as e:
        print(f"❌ View import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 AskMe Debug Diagnostic")
    print("=" * 50)

    imports_ok = test_imports()
    views_ok = test_view_import()

    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    print(f"Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Views: {'✅ PASS' if views_ok else '❌ FAIL'}")

    if imports_ok and views_ok:
        print("\n🎉 All components working - issue might be in request handling")
    else:
        print("\n❌ Found issues - check the errors above")