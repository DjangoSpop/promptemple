import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'promptcraft.settings.development'
import django
django.setup()
from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cursor.fetchall()]
for t in tables:
    if 'template' in t.lower() or 'chat' in t.lower() or 'extract' in t.lower():
        cursor.execute(f"PRAGMA table_info({t})")
        cols = [r[1] for r in cursor.fetchall()]
        print(f"  {t}: {cols}")
