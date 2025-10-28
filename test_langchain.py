# test_langchain.py - Verify LangChain installation
import sys
import traceback

def test_langchain_imports():
    """Test that all LangChain components can be imported"""
    try:
        print("🔍 Testing LangChain imports...")
        
        # Core imports
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.runnables import RunnablePassthrough
        print("✅ LangChain core imports successful!")
        
        # OpenAI integration
        from langchain_openai import ChatOpenAI
        print("✅ LangChain OpenAI imports successful!")
        
        # Community features
        from langchain_community.vectorstores import FAISS
        print("✅ LangChain community imports successful!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return False

def test_langchain_chain():
    """Test that LangChain chains can be created"""
    try:
        print("\n🔍 Testing LangChain chain creation...")
        
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # Create a simple chain
        prompt = ChatPromptTemplate.from_template("Say hello to {name}")
        model = ChatOpenAI(api_key="test-key", base_url="https://api.openai.com/v1")
        parser = StrOutputParser()
        
        # Chain components together
        chain = prompt | model | parser
        print("✅ LangChain chain created successfully!")
        
        # Test chain compilation
        compiled_chain = chain.with_config({"run_name": "test_chain"})
        print("✅ LangChain chain compilation successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Chain creation error: {e}")
        traceback.print_exc()
        return False

def test_pydantic_compatibility():
    """Test Pydantic v2 compatibility"""
    try:
        print("\n🔍 Testing Pydantic v2 compatibility...")
        
        import pydantic
        print(f"📦 Pydantic version: {pydantic.VERSION}")
        
        if pydantic.VERSION < "2.0.0":
            print("⚠️  Warning: Pydantic v1 detected. LangChain 0.3+ requires Pydantic v2")
            return False
        
        # Test BaseModel v2
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            name: str = Field(description="Test field")
            value: int = Field(default=42)
        
        test_instance = TestModel(name="test")
        print(f"✅ Pydantic v2 BaseModel works: {test_instance}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pydantic compatibility error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all LangChain tests"""
    print("🚀 LangChain Installation Verification\n")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_langchain_imports),
        ("Chain Creation Test", test_langchain_chain),
        ("Pydantic Compatibility Test", test_pydantic_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        result = test_func()
        results.append((test_name, result))
        print("-" * 30)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! LangChain is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the installation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)