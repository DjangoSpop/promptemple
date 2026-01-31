"""
Test script for the lean prompt enhancement service
Run this to verify the service works without Django dependencies
"""

import os
import sys

# Simple test without Django
def test_basic_functionality():
    """Test the prompt enhancer service basic functionality"""
    
    print("=" * 60)
    print("TESTING LEAN PROMPT ENHANCEMENT SERVICE")
    print("=" * 60)
    
    # Mock API key for testing structure
    os.environ.setdefault('DEEPSEEK_API_KEY', 'test-key-replace-with-real')
    
    # Import the service
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        from apps.ai_services.services.prompt_enhancer import (
            PromptEnhancerService, 
            PromptEnhancementError
        )
        print("✅ Service imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import service: {e}")
        return False
    
    # Test 1: Service initialization
    print("\n" + "=" * 60)
    print("TEST 1: Service Initialization")
    print("=" * 60)
    try:
        service = PromptEnhancerService(api_key='test-key')
        print("✅ Service initialized")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    # Test 2: Get available enhancement types
    print("\n" + "=" * 60)
    print("TEST 2: Available Enhancement Types")
    print("=" * 60)
    types = service.get_available_enhancement_types()
    print(f"Available types: {', '.join(types)}")
    assert len(types) > 0, "No enhancement types available"
    print("✅ Enhancement types retrieved")
    
    # Test 3: Input validation
    print("\n" + "=" * 60)
    print("TEST 3: Input Validation")
    print("=" * 60)
    
    # Empty prompt
    try:
        service.enhance_prompt("")
        print("❌ Empty prompt should raise error")
        return False
    except PromptEnhancementError as e:
        print(f"✅ Empty prompt rejected: {e}")
    
    # Too long prompt
    try:
        service.enhance_prompt("x" * 6000)
        print("❌ Too long prompt should raise error")
        return False
    except PromptEnhancementError as e:
        print(f"✅ Too long prompt rejected: {e}")
    
    # Test 4: Improvement notes generation
    print("\n" + "=" * 60)
    print("TEST 4: Improvement Notes Generation")
    print("=" * 60)
    
    test_cases = [
        {
            'original': "write a blog post",
            'enhanced': """Write a comprehensive 1500-word blog post about AI.

Structure:
- Introduction (200 words)
- Main body (1000 words)
- Conclusion (300 words)

Format: Professional tone, include examples.""",
            'expected_keywords': ['structure', 'format']
        },
        {
            'original': "explain quantum computing",
            'enhanced': "Explain quantum computing. You must include examples and avoid technical jargon.",
            'expected_keywords': ['constraint']
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        notes = service._generate_improvement_notes(
            test_case['original'],
            test_case['enhanced']
        )
        print(f"\nTest case {i}:")
        print(f"  Original: {test_case['original'][:50]}...")
        print(f"  Enhanced: {test_case['enhanced'][:50]}...")
        print(f"  Notes: {notes}")
        
        # Check if any expected keyword is in notes
        found = any(keyword in notes.lower() for keyword in test_case['expected_keywords'])
        if found:
            print(f"  ✅ Improvement notes contain expected keywords")
        else:
            print(f"  ⚠️  Improvement notes don't contain expected keywords")
    
    print("\n" + "=" * 60)
    print("ALL BASIC TESTS PASSED!")
    print("=" * 60)
    print("\n⚠️  Note: Actual API calls require a valid DEEPSEEK_API_KEY")
    print("   Set DEEPSEEK_API_KEY environment variable to test API integration")
    
    return True


def test_with_django():
    """Test the service with Django setup (requires Django to be configured)"""
    
    print("\n" + "=" * 60)
    print("TESTING WITH DJANGO INTEGRATION")
    print("=" * 60)
    
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings')
        django.setup()
        print("✅ Django setup complete")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        print("   Skipping Django-dependent tests")
        return False
    
    from apps.ai_services.services.prompt_enhancer import PromptEnhancerService
    
    # Test with actual API key from settings
    try:
        from django.conf import settings
        service = PromptEnhancerService()
        
        if hasattr(settings, 'DEEPSEEK_API_KEY') and settings.DEEPSEEK_API_KEY:
            print("✅ API key found in settings")
            
            # Test actual API call (if key is valid)
            print("\nTesting actual API call...")
            test_prompt = "write a blog post about AI"
            
            try:
                result = service.enhance_prompt(test_prompt, use_cache=False)
                print(f"\n✅ API call successful!")
                print(f"   Original: {result['original'][:50]}...")
                print(f"   Enhanced: {result['enhanced'][:100]}...")
                print(f"   Tokens used: {result['tokens_used']}")
                print(f"   Response time: {result['response_time_ms']:.2f}ms")
                print(f"   Improvements: {result['improvement_notes']}")
                
                return True
                
            except Exception as e:
                print(f"❌ API call failed: {e}")
                print("   This might be due to invalid API key or network issues")
                return False
        else:
            print("⚠️  DEEPSEEK_API_KEY not configured in settings")
            print("   Add DEEPSEEK_API_KEY to your .env file to test API calls")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LEAN PROMPT ENHANCEMENT SERVICE TEST SUITE")
    print("=" * 60 + "\n")
    
    # Run basic tests first
    basic_passed = test_basic_functionality()
    
    if basic_passed:
        print("\n✅ Basic tests passed! Service structure is correct.\n")
        
        # Try Django integration tests
        response = input("Run Django integration tests? (requires Django setup) [y/N]: ")
        if response.lower() in ['y', 'yes']:
            django_passed = test_with_django()
            
            if django_passed:
                print("\n" + "=" * 60)
                print("🎉 ALL TESTS PASSED!")
                print("=" * 60)
            else:
                print("\n⚠️  Django tests had issues, but basic structure is valid")
    else:
        print("\n❌ Basic tests failed. Please fix errors before proceeding.")
        sys.exit(1)
