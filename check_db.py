#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "promptcraft.settings")
django.setup()

from django.db import connection

# Check template tables
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%template%'")
template_tables = [row[0] for row in cursor.fetchall()]
print("Template tables:", template_tables)

# Check the column info for templates
if 'templates' in template_tables:
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'templates' 
        AND column_name = 'author_id'
    """)
    author_col_info = cursor.fetchall()
    print("Author column info:", author_col_info)
    
    # Also check all columns
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'templates' 
        ORDER BY ordinal_position
    """)
    all_cols = cursor.fetchall()
    print("All columns in templates table:", all_cols)
else:
    print("templates table not found")
