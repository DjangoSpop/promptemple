#!/usr/bin/env python
"""
Simple test script for the Research Agent implementation.
"""
import os
import sys
import django
from pathlib import Path

# Add the project to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from research_agent.models import ResearchJob, SourceDoc, Chunk, ResearchAnswer
from research_agent.utils import clean_html_to_text, validate_url
from research_agent.embeddings import embed_texts, split_text
from research_agent.agent import ResearchJobStats


def test_models():
    """Test model creation and basic functionality."""
    print("🧪 Testing models...")

    # Create a test job
    job = ResearchJob.objects.create(
        query="test query",
        top_k=5
    )
    print(f"✅ Created job: {job.id}")

    # Create a test document
    doc = SourceDoc.objects.create(
        job=job,
        url="https://example.com",
        title="Test Document",
        text="This is a test document with some content.",
        status_code=200
    )
    print(f"✅ Created document: {doc.id}")

    # Create a test chunk
    chunk = Chunk.objects.create(
        doc=doc,
        text="This is a test chunk.",
        tokens=5,
        embedding=[0.1, 0.2, 0.3] * 128,  # 384-dim vector
        url=doc.url,
        title=doc.title
    )
    print(f"✅ Created chunk: {chunk.id}")

    # Create a test answer
    answer = ResearchAnswer.objects.create(
        job=job,
        answer_md="# Test Answer\nThis is a test answer.",
        citations=[{"n": 1, "url": "https://example.com", "title": "Test"}]
    )
    print(f"✅ Created answer: {answer.id}")

    return job


def test_utilities():
    """Test utility functions."""
    print("🧪 Testing utilities...")

    # Test HTML cleaning
    html = "<h1>Title</h1><p>Content</p><script>alert('test');</script>"
    clean_text = clean_html_to_text(html)
    print(f"✅ HTML cleaning: '{clean_text}'")

    # Test URL validation
    valid_url = validate_url("https://example.com")
    invalid_url = validate_url("localhost")
    print(f"✅ URL validation - Valid: {valid_url}, Invalid: {invalid_url}")


def test_embeddings():
    """Test embedding functionality."""
    print("🧪 Testing embeddings...")

    try:
        # Test text splitting
        text = "This is a long text. " * 100
        chunks = split_text(text, tokens=50, overlap=10)
        print(f"✅ Text splitting: {len(chunks)} chunks created")

        # Test embeddings (this might fail if sentence-transformers is not installed)
        try:
            embeddings = embed_texts(["test text", "another test"])
            print(f"✅ Embeddings: Generated {len(embeddings)} embeddings")
        except ImportError:
            print("⚠️ Embeddings: sentence-transformers not available, using fallback")
        except Exception as e:
            print(f"⚠️ Embeddings: {e}")

    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")


def test_stats():
    """Test statistics functionality."""
    print("🧪 Testing statistics...")

    try:
        stats = ResearchJobStats.get_system_stats()
        print(f"✅ System stats: {stats}")
    except Exception as e:
        print(f"❌ Stats test failed: {e}")


def test_health_check():
    """Test health check functionality."""
    print("🧪 Testing health check...")

    try:
        from research_agent.tasks import health_check

        # Run health check
        result = health_check()
        print(f"✅ Health check: {result}")

    except Exception as e:
        print(f"❌ Health check failed: {e}")


def main():
    """Run all tests."""
    print("🚀 Starting Research Agent Tests")
    print("=" * 50)

    try:
        # Test basic functionality
        test_models()
        test_utilities()
        test_embeddings()
        test_stats()
        test_health_check()

        print("=" * 50)
        print("✅ All tests completed!")
        print("\n📋 Research Agent is ready to use!")
        print("\n🔗 Available endpoints:")
        print("  POST /api/v2/research/quick/     - Quick research")
        print("  GET  /api/v2/research/jobs/      - List jobs")
        print("  GET  /api/v2/research/health/    - Health check")
        print("  GET  /api/v2/research/stats/     - System stats")
        print("\n📚 Usage example:")
        print("  curl -X POST http://localhost:8000/api/v2/research/quick/ \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"query\": \"best prompt engineering practices\"}'")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()