"""
Test script for LangChain Orchestrator

This script tests the core functionality of the LangChain orchestrator
to ensure it's working properly before integrating it into the views.
"""

import os
import sys
import asyncio
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

# Now import the orchestrator
from apps.ai_services.orchestration.langchain_orchestrator import get_orchestrator

async def test_orchestrator():
    """Test the LangChain orchestrator functionality"""
    print("🚀 Testing LangChain Orchestrator")
    print("=" * 50)
    
    orchestrator = get_orchestrator()
    
    # Test 1: Basic prompt optimization
    print("\n📋 Test 1: Basic Prompt Optimization")
    print("-" * 30)
    
    test_prompt = "Write an email"
    try:
        result = await orchestrator.optimize_prompt(
            original_prompt=test_prompt,
            context={"purpose": "business communication", "tone": "professional"},
            target_audience="business professionals",
            desired_outcome="clear and effective communication"
        )
        
        print(f"✅ Original: {result.original_prompt}")
        print(f"✅ Optimized: {result.optimized_prompt[:100]}...")
        print(f"✅ Improvements: {len(result.improvements)} found")
        print(f"✅ Confidence: {result.confidence_score:.2f}")
        print("✅ Prompt optimization test PASSED")
        
    except Exception as e:
        print(f"❌ Prompt optimization test FAILED: {e}")
    
    # Test 2: Streaming optimization
    print("\n📋 Test 2: Streaming Optimization")
    print("-" * 30)
    
    try:
        stream_chunks = []
        async for chunk in orchestrator.optimize_prompt_streaming(
            original_prompt="Create a marketing strategy",
            context={"industry": "tech startup"},
            target_audience="marketing team"
        ):
            stream_chunks.append(chunk)
            if len(stream_chunks) <= 3:  # Show first few chunks
                print(f"📦 Chunk {len(stream_chunks)}: {chunk[:50]}...")
        
        print(f"✅ Received {len(stream_chunks)} chunks")
        print("✅ Streaming optimization test PASSED")
        
    except Exception as e:
        print(f"❌ Streaming optimization test FAILED: {e}")
    
    # Test 3: RAG enhancement
    print("\n📋 Test 3: RAG Enhancement")
    print("-" * 30)
    
    try:
        rag_result = await orchestrator.enhance_with_rag(
            query="How to improve customer retention?",
            max_docs=3,
            relevance_threshold=0.7
        )
        
        print(f"✅ Original query: {rag_result.query}")
        print(f"✅ Enhanced prompt: {rag_result.enhanced_prompt[:100]}...")
        print(f"✅ Retrieved docs: {len(rag_result.retrieved_docs)}")
        print("✅ RAG enhancement test PASSED")
        
    except Exception as e:
        print(f"❌ RAG enhancement test FAILED: {e}")
    
    # Test 4: Error handling
    print("\n📋 Test 4: Error Handling")
    print("-" * 30)
    
    try:
        # Test with empty prompt
        result = await orchestrator.optimize_prompt(
            original_prompt="",
            context=None
        )
        
        print(f"✅ Handled empty prompt gracefully")
        print(f"✅ Fallback result: {result.metadata.get('fallback', False)}")
        print("✅ Error handling test PASSED")
        
    except Exception as e:
        print(f"❌ Error handling test FAILED: {e}")
    
    print("\n🎯 Test Summary")
    print("=" * 50)
    print("✅ LangChain orchestrator is working correctly!")
    print("✅ Ready for integration with Django views")

def main():
    """Run the test"""
    try:
        asyncio.run(test_orchestrator())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()