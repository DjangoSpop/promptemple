# fix_missing_table.py
"""
Script to manually create the missing template_extraction_rules table
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.db import connection

def create_template_extraction_rules_table():
    """Manually create the template_extraction_rules table"""
    
    with connection.cursor() as cursor:
        # Create the table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_extraction_rules (
                id TEXT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                rule_type VARCHAR(20) NOT NULL,
                rule_config TEXT NOT NULL,
                minimum_confidence REAL NOT NULL,
                auto_approve_threshold REAL NOT NULL,
                is_active BOOLEAN NOT NULL,
                priority INTEGER NOT NULL,
                total_extractions INTEGER NOT NULL,
                successful_extractions INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        print("✅ Created template_extraction_rules table")
        
        # Check if table exists and is accessible
        cursor.execute("SELECT COUNT(*) FROM template_extraction_rules")
        count = cursor.fetchone()[0]
        print(f"✅ Table accessible, current count: {count}")

if __name__ == '__main__':
    create_template_extraction_rules_table()