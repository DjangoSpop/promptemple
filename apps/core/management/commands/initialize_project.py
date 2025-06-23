from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
import os
from pathlib import Path
import logging
import subprocess
import sys

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize the PromptCraft project with necessary setup steps'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset the database and start fresh'
        )
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Create sample data after initialization'
        )
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Create a default admin user'
        )
        
    def handle(self, *args, **options):
        reset = options['reset']
        create_sample_data = options['sample_data']
        create_admin = options['admin']
        
        self.stdout.write(self.style.SUCCESS('Starting PromptCraft project initialization...'))
        
        # Ensure required directories exist
        self.ensure_directories()
        
        # Reset database if requested
        if reset:
            self.reset_database()
        
        # Run migrations
        self.run_migrations()
        
        # Create admin user if requested
        if create_admin:
            self.create_admin_user()
        
        # Load initial data
        self.load_initial_data()
        
        # Create sample data if requested
        if create_sample_data:
            self.create_sample_data()
        
        self.stdout.write(self.style.SUCCESS('PromptCraft project initialization completed successfully!'))
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        self.stdout.write('Creating required directories...')
        
        # Get base directory
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        
        # Create media directories
        media_dir = base_dir / 'media'
        media_dir.mkdir(exist_ok=True)
        
        # Create logs directory
        logs_dir = base_dir / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # Create static directory
        static_dir = base_dir / 'static'
        static_dir.mkdir(exist_ok=True)
        
        self.stdout.write(self.style.SUCCESS('Required directories created'))
    
    def reset_database(self):
        """Reset the database"""
        self.stdout.write('Resetting database...')
        
        try:
            # Find all migration files
            base_dir = Path(__file__).resolve().parent.parent.parent
            apps_dir = base_dir
            
            # List of apps to reset
            app_names = ['ai_services', 'analytics', 'core', 'gamification', 'templates', 'users']
            
            # Remove sqlite database if it exists
            db_path = Path(__file__).resolve().parent.parent.parent.parent / 'db.sqlite3'
            if db_path.exists():
                db_path.unlink()
                self.stdout.write(self.style.SUCCESS('SQLite database deleted'))
                
            # Create fake migrations
            management_commands = [
                ['python', 'manage.py', 'migrate', 'admin', 'zero', '--fake'],
                ['python', 'manage.py', 'migrate', 'auth', 'zero', '--fake'],
                ['python', 'manage.py', 'migrate', 'contenttypes', 'zero', '--fake'],
                ['python', 'manage.py', 'migrate', 'sessions', 'zero', '--fake'],
                ['python', 'manage.py', 'migrate', 'rest_framework', 'zero', '--fake'],
            ]
            
            # Reset each app's migrations
            for app in app_names:
                management_commands.append(['python', 'manage.py', 'migrate', f'apps.{app}', 'zero', '--fake'])
            
            # Run the commands
            for cmd in management_commands:
                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError:
                    # Ignore errors for non-existent migrations
                    pass
                
            self.stdout.write(self.style.SUCCESS('Database reset completed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error resetting database: {e}'))
            raise
    
    def run_migrations(self):
        """Run database migrations"""
        self.stdout.write('Running database migrations...')
        
        try:
            subprocess.run(['python', 'manage.py', 'makemigrations'], check=True)
            subprocess.run(['python', 'manage.py', 'migrate'], check=True)
            self.stdout.write(self.style.SUCCESS('Migrations completed successfully'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error running migrations: {e}'))
            raise
    
    def create_admin_user(self):
        """Create a default admin user if it doesn't exist"""
        self.stdout.write('Creating admin user...')
        
        username = 'admin'
        email = 'admin@example.com'
        password = get_random_string(12)
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Admin user {username} already exists'))
        else:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user created with username: {username} and password: {password}'))
            self.stdout.write(self.style.WARNING('Please change the admin password after first login!'))
    
    def load_initial_data(self):
        """Load initial data fixtures"""
        self.stdout.write('Loading initial data...')
        
        # List of fixtures to load
        fixtures = [
            'ai_providers',
            'ai_models',
            'template_categories'
        ]
        
        try:
            for fixture in fixtures:
                fixture_path = f'apps/core/fixtures/{fixture}.json'
                if os.path.exists(fixture_path):
                    subprocess.run(['python', 'manage.py', 'loaddata', fixture_path], check=True)
                    self.stdout.write(self.style.SUCCESS(f'Loaded fixture: {fixture}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Fixture not found: {fixture}'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error loading fixtures: {e}'))
    
    def create_sample_data(self):
        """Create sample data for the application"""
        self.stdout.write('Creating sample data...')
        
        try:
            # Call the create_sample_data command
            subprocess.run(['python', 'manage.py', 'create_sample_data'], check=True)
            self.stdout.write(self.style.SUCCESS('Sample data created successfully'))
        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample data: {e}'))
            raise
