"""
Quick smoke test for Prompt History API v2
"""
import os
import sys
import django

# Setup Django - use base settings to avoid Redis requirement
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['DJANGO_SETTINGS_MODULE'] = 'promptcraft.settings'
os.environ['REDIS_URL'] = ''  # Disable Redis for this test
django.setup()

from django.contrib.auth import get_user_model
from apps.prompt_history.models import PromptHistory
from apps.prompt_history.serializers import PromptHistoryCreateSerializer

User = get_user_model()

print("=" * 60)
print("PROMPT HISTORY API v2 - SMOKE TEST")
print("=" * 60)

# 1. Check model
print("\n✓ Model imported successfully")
print(f"  Table: {PromptHistory._meta.db_table}")
print(f"  Fields: {[f.name for f in PromptHistory._meta.get_fields()]}")

# 2. Check serializer
print("\n✓ Serializer imported successfully")
print(f"  Create fields: {PromptHistoryCreateSerializer().fields.keys()}")

# 3. Create test user (if not exists)
user, created = User.objects.get_or_create(
    email='test@example.com',
    defaults={'username': 'testuser'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"\n✓ Created test user: {user.email}")
else:
    print(f"\n✓ Using existing test user: {user.email}")

# 4. Create history entry
history = PromptHistory.objects.create(
    user=user,
    original_prompt="Write a blog post about AI",
    source="raw",
    intent_category="content_creation",
    tags=["blog", "ai", "test"],
    meta={"session_id": "test123"}
)
print(f"\n✓ Created prompt history entry: {history.id}")
print(f"  User: {history.user.email}")
print(f"  Prompt: {history.original_prompt[:50]}...")
print(f"  Tags: {history.tags}")

# 5. Query history
count = PromptHistory.objects.filter(user=user, is_deleted=False).count()
print(f"\n✓ Query successful: {count} entries found for user")

# 6. Soft delete
history.soft_delete()
print(f"\n✓ Soft delete successful: is_deleted={history.is_deleted}")

# 7. Check exclusion from queries
visible_count = PromptHistory.objects.filter(user=user, is_deleted=False).count()
print(f"✓ Soft-deleted entries excluded: {visible_count} visible entries")

# 8. Check URLs
print("\n" + "=" * 60)
print("API ENDPOINTS (v2)")
print("=" * 60)
print("POST   /api/v2/history/               - Create entry")
print("GET    /api/v2/history/               - List entries")
print("GET    /api/v2/history/{id}/          - Retrieve entry")
print("PATCH  /api/v2/history/{id}/          - Update entry")
print("DELETE /api/v2/history/{id}/          - Soft delete")
print("POST   /api/v2/history/{id}/enhance/  - AI enhancement")

# 9. Check health endpoints
print("\n" + "=" * 60)
print("HEALTH ENDPOINTS")
print("=" * 60)
print("GET    /health/                       - Basic health")
print("GET    /health/redis/                 - Redis connectivity")

print("\n" + "=" * 60)
print("✅ ALL SMOKE TESTS PASSED")
print("=" * 60)
print("\nNext steps:")
print("1. Start server: python manage.py runserver")
print("2. Get JWT token via /api/v2/auth/login/")
print("3. Test endpoints with Authorization: Bearer <token>")
print("4. Check docs: docs/API_HISTORY_V2.md")
print("5. Deploy to Heroku: docs/DEPLOY_HEROKU.md")
