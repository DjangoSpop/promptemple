import os
import django
from django.conf import settings

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'promptcraft.settings.development')
django.setup()

from django.db import connection

def verify_database_details():
    print("🔍 Verifying Database Connection Details...")
    print("=" * 50)
    
    # Get database settings from Django
    db_settings = settings.DATABASES['default']
    
    print(f"📋 Django Configuration:")
    print(f"   Engine: {db_settings['ENGINE']}")
    print(f"   Database Name: {db_settings['NAME']}")
    print(f"   User: {db_settings['USER']}")
    print(f"   Host: {db_settings['HOST']}")
    print(f"   Port: {db_settings['PORT']}")
    print()
    
    try:
        with connection.cursor() as cursor:
            # Get PostgreSQL version and current database
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL Version: {version[:80]}...")
            
            # Get current database name
            cursor.execute("SELECT current_database();")
            current_db = cursor.fetchone()[0]
            print(f"✅ Connected to Database: {current_db}")
            
            # Get current user
            cursor.execute("SELECT current_user;")
            current_user = cursor.fetchone()[0]
            print(f"✅ Connected as User: {current_user}")
            
            # Get connection info
            cursor.execute("SELECT inet_server_addr(), inet_server_port();")
            server_info = cursor.fetchone()
            print(f"✅ Server Address: {server_info[0] or 'localhost'}")
            print(f"✅ Server Port: {server_info[1]}")
            
            # List all databases (to confirm we're on the right server)
            cursor.execute("""
                SELECT datname FROM pg_database 
                WHERE datistemplate = false 
                ORDER BY datname;
            """)
            databases = cursor.fetchall()
            print(f"\n📊 Available Databases on this Server:")
            for db in databases:
                marker = " ← CURRENT" if db[0] == current_db else ""
                print(f"   - {db[0]}{marker}")
            
            # List tables in current database
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"\n🗃️  Tables in '{current_db}' database:")
            if tables:
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("   (No tables found - database might be empty)")
            
            # Check if this matches our expected database
            expected_db = db_settings['NAME']
            if current_db == expected_db:
                print(f"\n✅ SUCCESS: Connected to the correct database '{expected_db}'")
                return True
            else:
                print(f"\n❌ WARNING: Expected database '{expected_db}', but connected to '{current_db}'")
                return False
                
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    verify_database_details()