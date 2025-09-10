"""
Django management command for ingesting prompts from markdown files
Usage: python manage.py ingest_prompts --source <path> --type <md|json|directory>
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import logging
from apps.templates.services.md_ingestion_service import MarkdownIngestionManager


class Command(BaseCommand):
    """Management command for ingesting prompts from various sources"""
    
    help = 'Ingest prompts from markdown files or JSON into the database'
    
    def add_arguments(self, parser):
        """Define command arguments"""
        parser.add_argument(
            '--source',
            type=str,
            required=True,
            help='Path to the source file or directory'
        )
        
        parser.add_argument(
            '--type',
            choices=['md', 'json', 'directory'],
            default='md',
            help='Type of source: md (single markdown file), json (JSON file), directory (all MD files in directory)'
        )
        
        parser.add_argument(
            '--pattern',
            type=str,
            default='*.md',
            help='File pattern for directory ingestion (default: *.md)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for database operations (default: 100)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without actually saving to database'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        parser.add_argument(
            '--author',
            type=str,
            default='system',
            help='Username for the template author (default: system)'
        )
    
    def handle(self, *args, **options):
        """Execute the command"""
        
        # Set up logging
        if options['verbose']:
            logging.basicConfig(level=logging.INFO)
        
        # Validate source path
        source_path = options['source']
        if not os.path.exists(source_path):
            raise CommandError(f"Source path does not exist: {source_path}")
        
        # Initialize ingestion manager
        manager = MarkdownIngestionManager()
        
        # Handle dry run
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No data will be saved to database')
            )
            return self._perform_dry_run(manager, options)
        
        # Perform actual ingestion
        self.stdout.write(f"Starting ingestion from: {source_path}")
        self.stdout.write(f"Ingestion type: {options['type']}")
        
        try:
            if options['type'] == 'md':
                result = manager.ingest_from_file(source_path)
            elif options['type'] == 'json':
                result = manager.ingest_from_json(source_path)
            elif options['type'] == 'directory':
                result = manager.ingest_from_directory(
                    source_path, 
                    pattern=options['pattern']
                )
            else:
                raise CommandError(f"Unknown ingestion type: {options['type']}")
            
            # Display results
            self._display_results(result, options)
            
        except Exception as e:
            raise CommandError(f"Ingestion failed: {str(e)}")
    
    def _perform_dry_run(self, manager, options):
        """Perform a dry run to analyze source without saving"""
        source_path = options['source']
        
        try:
            if options['type'] == 'md':
                # Extract prompts but don't save
                prompts = manager.extractor.extract_prompts_from_md(source_path)
                self._display_dry_run_results(prompts, source_path)
                
            elif options['type'] == 'json':
                import json
                with open(source_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                prompts = manager._convert_json_to_prompts(data)
                self._display_dry_run_results(prompts, source_path)
                
            elif options['type'] == 'directory':
                from pathlib import Path
                directory = Path(source_path)
                md_files = list(directory.glob(options['pattern']))
                
                total_prompts = 0
                for md_file in md_files:
                    prompts = manager.extractor.extract_prompts_from_md(str(md_file))
                    total_prompts += len(prompts)
                    self.stdout.write(f"  {md_file.name}: {len(prompts)} prompts")
                
                self.stdout.write(
                    self.style.SUCCESS(f"Total prompts found: {total_prompts} across {len(md_files)} files")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Dry run failed: {str(e)}")
            )
    
    def _display_dry_run_results(self, prompts, source_path):
        """Display results from dry run"""
        self.stdout.write(f"\nDry run analysis for: {source_path}")
        self.stdout.write(f"Prompts found: {len(prompts)}")
        
        if prompts:
            # Show categories
            categories = {}
            for prompt in prompts:
                cat = prompt.get('category', 'Unknown')
                categories[cat] = categories.get(cat, 0) + 1
            
            self.stdout.write("\nCategories found:")
            for category, count in categories.items():
                self.stdout.write(f"  {category}: {count} prompts")
            
            # Show sample prompt
            sample = prompts[0]
            self.stdout.write(f"\nSample prompt:")
            self.stdout.write(f"  Title: {sample.get('title', 'N/A')}")
            self.stdout.write(f"  Category: {sample.get('category', 'N/A')}")
            self.stdout.write(f"  Variables: {len(sample.get('variables', []))}")
            self.stdout.write(f"  Tags: {', '.join(sample.get('tags', []))}")
    
    def _display_results(self, result, options):
        """Display ingestion results"""
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f"✅ {result['message']}")
            )
            
            # Display detailed stats
            stats = result.get('stats', {})
            if stats:
                self.stdout.write("\n📊 Ingestion Statistics:")
                self.stdout.write(f"  Total processed: {stats.get('total_processed', 0)}")
                self.stdout.write(f"  Successfully created: {stats.get('successfully_created', 0)}")
                self.stdout.write(f"  Skipped duplicates: {stats.get('skipped_duplicates', 0)}")
                self.stdout.write(f"  Errors: {stats.get('errors', 0)}")
                self.stdout.write(f"  Categories created: {stats.get('categories_created', 0)}")
                self.stdout.write(f"  Fields created: {stats.get('fields_created', 0)}")
            
            # Display file-specific results for directory ingestion
            if 'files' in result:
                self.stdout.write("\n📁 File Processing Results:")
                for file_info in result['files']:
                    if file_info['success']:
                        self.stdout.write(
                            f"  ✅ {file_info['file']}: {file_info.get('prompts_extracted', 0)} prompts"
                        )
                    else:
                        self.stdout.write(
                            f"  ❌ {file_info['file']}: {file_info.get('error', 'Unknown error')}"
                        )
            
            # Performance summary
            prompts_extracted = result.get('prompts_extracted', 0)
            if prompts_extracted > 0:
                success_rate = (stats.get('successfully_created', 0) / prompts_extracted) * 100
                self.stdout.write(f"\n🎯 Success Rate: {success_rate:.1f}%")
                
                if stats.get('successfully_created', 0) > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"🚀 Successfully added {stats.get('successfully_created', 0)} new prompts to the database!"
                        )
                    )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ {result['message']}")
            )
            
            # Show error details if available
            if 'stats' in result and result['stats'].get('errors', 0) > 0:
                self.stdout.write(f"Number of errors: {result['stats']['errors']}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


# Example usage in command line:
"""
# Ingest single markdown file
python manage.py ingest_prompts --source PROMPT_GOLDMINE_100K.md --type md --verbose

# Ingest JSON file
python manage.py ingest_prompts --source top-1000-prompts-library.json --type json

# Ingest all markdown files in directory
python manage.py ingest_prompts --source . --type directory --pattern "*.md"

# Dry run to see what would be imported
python manage.py ingest_prompts --source . --type directory --dry-run

# Ingest with custom batch size
python manage.py ingest_prompts --source prompts/ --type directory --batch-size 50
"""