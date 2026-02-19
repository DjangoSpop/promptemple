"""Create missing chat tables directly, then mark migration as applied."""
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'promptcraft.settings.development'
import django
django.setup()

from django.db import connection

cursor = connection.cursor()

# Check which tables we need
needed = ['chat_sessions', 'chat_messages', 'extracted_templates']
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
existing = {r[0] for r in cursor.fetchall()}

for table in needed:
    if table in existing:
        print(f"  {table}: already exists")
    else:
        print(f"  {table}: MISSING - will create")

# Create chat_sessions
if 'chat_sessions' not in existing:
    cursor.execute("""
    CREATE TABLE "chat_sessions" (
        "id" char(32) NOT NULL PRIMARY KEY,
        "title" varchar(200) NOT NULL,
        "ai_model" varchar(50) NOT NULL DEFAULT 'deepseek-chat',
        "model_provider" varchar(50) NOT NULL DEFAULT 'deepseek',
        "session_metadata" text NOT NULL DEFAULT '{}',
        "is_active" bool NOT NULL DEFAULT 1,
        "total_messages" integer unsigned NOT NULL DEFAULT 0,
        "total_tokens_used" integer unsigned NOT NULL DEFAULT 0,
        "total_cost" decimal NOT NULL DEFAULT 0,
        "extracted_templates_count" integer unsigned NOT NULL DEFAULT 0,
        "templates_approved" integer unsigned NOT NULL DEFAULT 0,
        "created_at" datetime NOT NULL,
        "updated_at" datetime NOT NULL,
        "user_id" char(32) NOT NULL REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED
    )
    """)
    print("  Created chat_sessions")

# Create chat_messages
if 'chat_messages' not in existing:
    cursor.execute("""
    CREATE TABLE "chat_messages" (
        "id" char(32) NOT NULL PRIMARY KEY,
        "role" varchar(20) NOT NULL,
        "content" text NOT NULL,
        "original_content" text NOT NULL DEFAULT '',
        "model_used" varchar(50) NOT NULL DEFAULT '',
        "tokens_used" integer unsigned NOT NULL DEFAULT 0,
        "response_time_ms" integer unsigned NOT NULL DEFAULT 0,
        "estimated_cost" decimal NOT NULL DEFAULT 0,
        "contains_templates" bool NOT NULL DEFAULT 0,
        "templates_extracted" bool NOT NULL DEFAULT 0,
        "extraction_processed" bool NOT NULL DEFAULT 0,
        "langchain_analyzed" bool NOT NULL DEFAULT 0,
        "analysis_score" real NOT NULL DEFAULT 0.0,
        "template_quality_score" real NOT NULL DEFAULT 0.0,
        "message_metadata" text NOT NULL DEFAULT '{}',
        "created_at" datetime NOT NULL,
        "session_id" char(32) NOT NULL REFERENCES "chat_sessions" ("id") DEFERRABLE INITIALLY DEFERRED
    )
    """)
    cursor.execute('CREATE INDEX "chat_messages_session_created" ON "chat_messages" ("session_id", "created_at")')
    cursor.execute('CREATE INDEX "chat_messages_role_created" ON "chat_messages" ("role", "created_at")')
    cursor.execute('CREATE INDEX "chat_messages_templates" ON "chat_messages" ("contains_templates", "templates_extracted")')
    print("  Created chat_messages with indexes")

# Create extracted_templates
if 'extracted_templates' not in existing:
    cursor.execute("""
    CREATE TABLE "extracted_templates" (
        "id" char(32) NOT NULL PRIMARY KEY,
        "title" varchar(200) NOT NULL,
        "description" text NOT NULL,
        "template_content" text NOT NULL,
        "category_suggestion" varchar(100) NOT NULL DEFAULT '',
        "extraction_method" varchar(50) NOT NULL DEFAULT 'langchain',
        "confidence_score" real NOT NULL,
        "quality_rating" varchar(20) NOT NULL DEFAULT 'medium',
        "langchain_analysis" text NOT NULL DEFAULT '{}',
        "keywords_extracted" text NOT NULL DEFAULT '[]',
        "use_cases" text NOT NULL DEFAULT '[]',
        "status" varchar(20) NOT NULL DEFAULT 'pending',
        "auto_approved" bool NOT NULL DEFAULT 0,
        "review_notes" text NOT NULL DEFAULT '',
        "reviewed_at" datetime NULL,
        "created_at" datetime NOT NULL,
        "updated_at" datetime NOT NULL,
        "published_template_id" char(32) NULL UNIQUE REFERENCES "templates" ("id") DEFERRABLE INITIALLY DEFERRED,
        "reviewed_by_id" char(32) NULL REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED,
        "source_message_id" char(32) NOT NULL REFERENCES "chat_messages" ("id") DEFERRABLE INITIALLY DEFERRED,
        "user_id" char(32) NOT NULL REFERENCES "users" ("id") DEFERRABLE INITIALLY DEFERRED
    )
    """)
    cursor.execute('CREATE INDEX "extracted_templates_user_status" ON "extracted_templates" ("user_id", "status")')
    cursor.execute('CREATE INDEX "extracted_templates_status_created" ON "extracted_templates" ("status", "created_at")')
    cursor.execute('CREATE INDEX "extracted_templates_score_quality" ON "extracted_templates" ("confidence_score", "quality_rating")')
    print("  Created extracted_templates with indexes")

# Mark migration as applied
from django.db.migrations.recorder import MigrationRecorder
recorder = MigrationRecorder(connection)
if not recorder.migration_qs.filter(app='chat', name='0001_initial').exists():
    recorder.record_applied('chat', '0001_initial')
    print("  Marked chat.0001_initial as applied")
else:
    print("  chat.0001_initial already recorded")

print("\nDone! Chat tables are ready.")
