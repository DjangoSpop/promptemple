"""
High-performance management command to ingest 100K+ prompts into Template model
Implements the Ingestion Agent workflow: clean, deduplicate, score, tag, and bulk insert
"""

import json
import time
import logging
import csv
import hashlib
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import concurrent.futures
from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from apps.templates.models import Template, TemplateCategory, PromptField
from apps.templates.cache_services import multi_cache

logger = logging.getLogger(__name__)
User = get_user_model()

@dataclass
class PromptData:
    """Data structure for prompt information aligned with Template model"""
    title: str
    description: str
    template_content: str
    category_name: str
    tags: List[str] = None
    required_inputs: List[str] = None
    optional_inputs: List[str] = None
    ideal_models: List[str] = None
    power_tips: List[str] = None
    complexity: str = "Medium"
    tone: str = ""
    framework: str = ""
    quality_score: float = 0.0
    popularity_score: float = 0.0
    intent_category: str = ""
    domain: str = ""
    external_id: str = ""
    subcategory: str = ""
    use_cases: List[str] = None

class Command(BaseCommand):
    help = 'Ingest large-scale prompt library (100K+ prompts) with high performance'
    
    def __init__(self):
        super().__init__()
        self.batch_size = 1000
        self.thread_pool_size = 4
        self.processed_count = 0
        self.error_count = 0
        self.start_time = None
        
    def add_arguments(self, parser):
        # Positional argument for file path
        parser.add_argument(
            'file',
            nargs='?',
            type=str,
            help='Path to the prompt data file (JSON, CSV, or JSONL)'
        )
        
        parser.add_argument(
            '--file',
            dest='file_option',
            type=str,
            help='Alternative: path to the prompt data file (use positional arg instead)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'jsonl'],
            default='auto',
            help='Format of the input file (default: auto-detect from extension)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for database operations'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            help='Number of worker threads for processing'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing template data before ingestion'
        )
        parser.add_argument(
            '--update-search-vectors',
            action='store_true',
            help='Update search vectors after ingestion'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform a dry run without saving to database'
        )
        parser.add_argument(
            '--sample-size',
            type=int,
            help='Process only a sample of the data (for testing)'
        )
        parser.add_argument(
            '--skip-duplicates',
            action='store_true',
            default=True,
            help='Skip duplicate templates (default: True)'
        )
        parser.add_argument(
            '--min-quality',
            type=float,
            default=0.0,
            help='Minimum quality score threshold (0-100)'
        )
        
    def handle(self, *args, **options):
        """Main command handler with enhanced error handling"""
        self.start_time = time.time()
        self.batch_size = options['batch_size']
        self.thread_pool_size = options['workers']
        self.min_quality = options['min_quality']
        
        try:
            self.stdout.write(
                self.style.SUCCESS('🚀 Starting 100K+ Template Ingestion Process...')
            )
            
            # Resolve file path - support both positional and --file arguments
            file_path = options.get('file') or options.get('file_option')
            if not file_path:
                raise CommandError('File path is required. Usage: python manage.py ingest_100k_prompts <file_path>')
            
            file_path = self._validate_inputs(file_path)
            
            # Auto-detect format from extension if not specified
            format_type = options['format']
            if format_type == 'auto':
                format_type = self._detect_format(file_path)
                self.stdout.write(
                    self.style.WARNING(f'📋 Auto-detected format: {format_type}')
                )
            
            # Clear existing data if requested
            if options['clear_existing'] and not options['dry_run']:
                self._clear_existing_data()
            
            # Load and process data
            self.stdout.write('📂 Loading data from file...')
            prompt_data = self._load_prompt_data(file_path, format_type)
            
            # Apply sample size if specified
            if options['sample_size']:
                prompt_data = prompt_data[:options['sample_size']]
                self.stdout.write(
                    self.style.WARNING(f'🔍 Processing sample of {len(prompt_data)} templates')
                )
            
            # Filter by quality score
            initial_count = len(prompt_data)
            prompt_data = [p for p in prompt_data if self._get_quality_score(p) >= self.min_quality]
            if len(prompt_data) < initial_count:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Filtered out {initial_count - len(prompt_data)} low-quality templates '
                        f'(quality < {self.min_quality})'
                    )
                )
            
            # Process prompts in batches
            self.stdout.write(f'⚙️  Processing {len(prompt_data)} templates in batches of {self.batch_size}...')
            self._process_prompts(prompt_data, options['dry_run'], options['skip_duplicates'])
            
            # Update search vectors if requested
            if options['update_search_vectors'] and not options['dry_run']:
                self._update_search_vectors()
            
            # Clear cache to ensure fresh data
            if not options['dry_run']:
                self._clear_cache()
            
            # Report results
            self._report_results()
            
        except CommandError as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
            raise
        except Exception as e:
            logger.exception(f"Command execution error: {e}")
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))
            raise CommandError(f"Ingestion failed: {e}")
    
    def _validate_inputs(self, file_path_arg: str) -> Path:
        """Validate command inputs with comprehensive error handling"""
        if not file_path_arg:
            raise CommandError("File path is required")
        
        file_path = Path(file_path_arg)
        
        # Handle relative paths
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        
        if not file_path.exists():
            # Try common locations
            common_locations = [
                Path.cwd() / file_path_arg,
                Path.cwd() / 'data' / file_path_arg,
                Path.cwd() / 'datasets' / file_path_arg,
            ]
            
            for location in common_locations:
                if location.exists():
                    file_path = location
                    break
            else:
                raise CommandError(
                    f"❌ File not found: {file_path}\n"
                    f"   Searched in: {[str(l) for l in common_locations]}"
                )
        
        if not file_path.is_file():
            raise CommandError(f"❌ Path is not a file: {file_path}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb == 0:
            raise CommandError(f"❌ File is empty: {file_path}")
        
        if file_size_mb > 2000:  # 2GB limit for safety
            self.stdout.write(
                self.style.WARNING(f'⚠️  Large file detected: {file_size_mb:.1f}MB - processing may take time')
            )
        
        self.stdout.write(self.style.SUCCESS(f'✅ File validated: {file_path} ({file_size_mb:.1f}MB)'))
        return file_path
    
    def _detect_format(self, file_path: Path) -> str:
        """Auto-detect file format from extension"""
        suffix = file_path.suffix.lower()
        format_map = {
            '.json': 'json',
            '.jsonl': 'jsonl',
            '.ndjson': 'jsonl',
            '.csv': 'csv',
        }
        
        detected = format_map.get(suffix, 'json')
        return detected
    
    def _clear_existing_data(self):
        """Clear existing template data with confirmation"""
        self.stdout.write('🗑️  Clearing existing templates...')
        
        try:
            with transaction.atomic():
                count = Template.objects.count()
                if count > 0:
                    Template.objects.all().delete()
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Cleared {count:,} existing templates')
                    )
                else:
                    self.stdout.write('ℹ️  No existing templates to clear')
        except Exception as e:
            logger.error(f"Error clearing existing data: {e}")
            raise CommandError(f"Failed to clear existing templates: {e}")
    
    def _load_prompt_data(self, file_path: Path, format_type: str) -> List[Dict]:
        """Load prompt data from file with comprehensive error handling"""
        self.stdout.write(f'📂 Loading data from {file_path.name}...')
        
        start_time = time.time()
        
        try:
            if format_type == 'json':
                data = self._load_json(file_path)
            elif format_type == 'csv':
                data = self._load_csv(file_path)
            elif format_type == 'jsonl':
                data = self._load_jsonl(file_path)
            else:
                raise CommandError(f"Unsupported format: {format_type}")
            
            load_time = time.time() - start_time
            
            if not data:
                raise CommandError("❌ No data found in file")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Loaded {len(data):,} records in {load_time:.2f}s'
                )
            )
            
            return data
            
        except json.JSONDecodeError as e:
            raise CommandError(f"❌ JSON parsing error: {e}")
        except Exception as e:
            logger.exception(f"Error loading data: {e}")
            raise CommandError(f"Failed to load data: {e}")
    
    def _load_json(self, file_path: Path) -> List[Dict]:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict):
                # Handle different JSON structures
                if 'prompts' in data:
                    return data['prompts']
                elif 'data' in data:
                    return data['data']
                else:
                    return [data]  # Single prompt
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Invalid JSON structure")
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            raise CommandError(f"Error loading JSON file: {e}")
    
    def _load_jsonl(self, file_path: Path) -> List[Dict]:
        """Load data from JSON Lines file"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            data.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON on line {line_num}: {e}")
                            continue
            return data
            
        except FileNotFoundError as e:
            raise CommandError(f"Error loading JSONL file: {e}")
    
    def _load_csv(self, file_path: Path) -> List[Dict]:
        """Load data from CSV file"""
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert JSON fields
                    for field in ['tags', 'keywords']:
                        if field in row and row[field]:
                            try:
                                row[field] = json.loads(row[field])
                            except json.JSONDecodeError:
                                row[field] = row[field].split(',') if row[field] else []
                    data.append(row)
            return data
            
        except FileNotFoundError as e:
            raise CommandError(f"Error loading CSV file: {e}")
    
    def _process_prompts(self, prompt_data: List[Dict], dry_run: bool = False, skip_duplicates: bool = True):
        """Process prompts in parallel batches with enhanced tracking"""
        total_count = len(prompt_data)
        self.stdout.write(f'⚙️  Processing {total_count:,} templates...')
        
        # Split data into batches
        batches = [
            prompt_data[i:i + self.batch_size]
            for i in range(0, total_count, self.batch_size)
        ]
        
        total_batches = len(batches)
        self.stdout.write(f'📦 Created {total_batches} batches')
        
        # Process batches with threading
        batch_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_pool_size) as executor:
            # Submit all batches
            futures = {
                executor.submit(self._process_batch, batch, batch_num, dry_run, skip_duplicates): batch_num
                for batch_num, batch in enumerate(batches)
            }
            
            # Wait for completion and collect results
            for future in concurrent.futures.as_completed(futures):
                batch_num = futures[future]
                try:
                    batch_count, batch_errors = future.result()
                    self.processed_count += batch_count
                    self.error_count += batch_errors
                    batch_results.append((batch_num, batch_count, batch_errors))
                    
                    # Progress update
                    progress = (sum(r[1] for r in batch_results) / total_count) * 100
                    self.stdout.write(
                        f'📊 Progress: {self.processed_count:,}/{total_count:,} '
                        f'({progress:.1f}%) | Errors: {self.error_count:,}     ',
                        ending='\r'
                    )
                    
                except Exception as e:
                    logger.error(f"Batch {batch_num} processing error: {e}")
                    self.error_count += len(batches[batch_num])
        
        self.stdout.write('')  # New line after progress
    
    def _process_batch(self, batch: List[Dict], batch_num: int, dry_run: bool, skip_duplicates: bool = True) -> tuple:
        """Process a single batch of prompts with error recovery"""
        batch_count = 0
        batch_errors = 0
        
        if dry_run:
            # Just validate data structure
            for item in batch:
                try:
                    self._parse_prompt_data(item)
                    batch_count += 1
                except Exception as e:
                    logger.warning(f"Batch {batch_num} item validation error: {e}")
                    batch_errors += 1
            return batch_count, batch_errors
        
        # Prepare template objects
        template_objects = []
        field_objects = []
        
        for item in batch:
            try:
                prompt_data = self._parse_prompt_data(item)
                
                # Check for duplicates if requested
                if skip_duplicates and self._is_duplicate(prompt_data.external_id):
                    logger.debug(f"Skipped duplicate: {prompt_data.title}")
                    batch_errors += 1
                    continue
                
                # Get or create category
                category = self._get_or_create_category(prompt_data.category_name)
                
                # Get system user for author
                system_user = self._get_system_user()
                
                # Create template object
                template_obj = Template(
                    title=prompt_data.title,
                    description=prompt_data.description,
                    category=category,
                    template_content=prompt_data.template_content,
                    author=system_user,
                    version="1.0.0",
                    tags=prompt_data.tags,
                    is_ai_generated=True,
                    ai_confidence=prompt_data.quality_score / 100.0,
                    extracted_keywords=prompt_data.tags,
                    smart_suggestions={
                        'ideal_models': prompt_data.ideal_models,
                        'power_tips': prompt_data.power_tips,
                        'complexity': prompt_data.complexity,
                        'tone': prompt_data.tone,
                        'framework': prompt_data.framework
                    },
                    usage_count=0,
                    completion_rate=0.0,
                    average_rating=0.0,
                    popularity_score=prompt_data.popularity_score,
                    is_public=True,
                    is_featured=prompt_data.quality_score > 80,
                    is_active=True,
                    localizations={},
                    external_id=prompt_data.external_id or None,
                    prompt_framework=prompt_data.framework,
                    subcategory=prompt_data.subcategory,
                    use_cases=prompt_data.use_cases or []
                )
                template_objects.append(template_obj)
                
                # Create field objects
                template_fields = self._create_template_fields(
                    template_obj, 
                    prompt_data.required_inputs, 
                    prompt_data.optional_inputs
                )
                field_objects.extend(template_fields)
                
                batch_count += 1
                
            except Exception as e:
                logger.warning(f"Batch {batch_num} item processing error: {e}")
                batch_errors += 1
        
        # Bulk insert with transaction
        if template_objects:
            try:
                with transaction.atomic():
                    # Insert templates
                    created_templates = Template.objects.bulk_create(
                        template_objects,
                        batch_size=self.batch_size,
                        ignore_conflicts=True
                    )
                    
                    # Insert fields for created templates
                    if field_objects:
                        PromptField.objects.bulk_create(
                            field_objects,
                            batch_size=self.batch_size,
                            ignore_conflicts=True
                        )
                        
            except Exception as e:
                logger.error(f"Batch {batch_num} database error: {e}")
                batch_errors += len(template_objects)
                batch_count = 0
        
        return batch_count, batch_errors
    
    def _is_duplicate(self, external_id: str) -> bool:
        """Check if template already exists by external_id"""
        if external_id:
            return Template.objects.filter(external_id=external_id).exists()
        return False
    
    def _get_or_create_category(self, category_name: str) -> TemplateCategory:
        """Get or create template category with thread-safe slug generation"""
        try:
            # Try to get existing by slug (normalized name)
            slug = self._slugify(category_name)
            category = TemplateCategory.objects.get(slug=slug)
            return category
        except TemplateCategory.DoesNotExist:
            try:
                # Try to create with get_or_create using slug for safety
                category, created = TemplateCategory.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': category_name,
                        'description': f'Templates for {category_name.lower()}',
                        'is_active': True
                    }
                )
                return category
            except Exception as e:
                logger.warning(f"Category creation error for '{category_name}': {e}")
                # Fallback: return existing category with closest match
                try:
                    return TemplateCategory.objects.filter(name__icontains=category_name).first() or \
                           TemplateCategory.objects.first()
                except:
                    # Create a generic fallback category if nothing exists
                    category, _ = TemplateCategory.objects.get_or_create(
                        name='General',
                        defaults={'slug': 'general', 'is_active': True}
                    )
                    return category
    
    def _get_system_user(self):
        """Get or create system user for templates"""
        user, created = User.objects.get_or_create(
            username='system',
            defaults={
                'email': 'system@promptemple.com',
                'is_active': False
            }
        )
        return user
    
    def _create_template_fields(self, template: Template, required_inputs: List[str], optional_inputs: List[str]) -> List[PromptField]:
        """Create PromptField objects for template"""
        fields = []
        order = 0
        
        # Required fields
        for field_name in required_inputs:
            field = PromptField(
                template=template,
                label=self._humanize_field_name(field_name),
                field_type='text',  # Default to text
                field_key=field_name,
                placeholder=f'Enter {self._humanize_field_name(field_name).lower()}',
                is_required=True,
                order=order,
                help_text=f'Provide a {self._humanize_field_name(field_name).lower()}'
            )
            fields.append(field)
            order += 1
        
        # Optional fields
        for field_name in optional_inputs:
            field = PromptField(
                template=template,
                label=self._humanize_field_name(field_name),
                field_type='text',  # Default to text
                field_key=field_name,
                placeholder=f'Enter {self._humanize_field_name(field_name).lower()} (optional)',
                is_required=False,
                order=order,
                help_text=f'Optionally provide a {self._humanize_field_name(field_name).lower()}'
            )
            fields.append(field)
            order += 1
        
        return fields
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug format"""
        text = text.lower().strip()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        return text.strip('-')
    
    def _humanize_field_name(self, field_name: str) -> str:
        """Convert snake_case to Human Readable"""
        return ' '.join(word.capitalize() for word in field_name.split('_'))
    
    def _get_quality_score(self, item: Dict) -> float:
        """Extract or calculate quality score from item"""
        # Try to get from metadata first
        metadata = item.get('metadata', {})
        if metadata and 'quality_score' in metadata:
            try:
                return float(metadata['quality_score'])
            except (ValueError, TypeError):
                pass
        
        # Fallback to direct field
        try:
            return float(item.get('quality_score', 0.0))
        except (ValueError, TypeError):
            return 0.0
    
    def _report_results(self):
        """Report ingestion results with enhanced metrics"""
        total_time = time.time() - self.start_time
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ INGESTION COMPLETED SUCCESSFULLY'))
        self.stdout.write('='*70)
        
        self.stdout.write(f'📊 Total templates processed: {self.processed_count:,}')
        self.stdout.write(f'⚠️  Errors encountered: {self.error_count:,}')
        
        # Calculate metrics
        if self.processed_count > 0:
            success_rate = ((self.processed_count - self.error_count) / self.processed_count) * 100
            self.stdout.write(f'✅ Success rate: {success_rate:.1f}%')
            
            avg_time_per_template = (total_time / self.processed_count) * 1000
            self.stdout.write(f'⏱️  Average time per template: {avg_time_per_template:.2f}ms')
            
            templates_per_second = self.processed_count / total_time
            self.stdout.write(f'⚡ Processing rate: {templates_per_second:.1f} templates/second')
        else:
            self.stdout.write('ℹ️  No templates were processed')
        
        self.stdout.write(f'⏳ Total processing time: {total_time:.2f}s ({total_time/60:.1f}m)')
        
        # Database stats
        try:
            total_in_db = Template.objects.count()
            self.stdout.write(f'💾 Total templates in database: {total_in_db:,}')
        except Exception as e:
            logger.warning(f"Could not retrieve database stats: {e}")
        
        # Performance recommendations
        if total_time > 300:  # More than 5 minutes
            self.stdout.write(
                self.style.WARNING(
                    '\n⚡ Performance tip: Consider increasing --batch-size or --workers for faster processing'
                )
            )
        
        self.stdout.write('\n' + self.style.SUCCESS('🚀 Ready for search and optimization!'))
        self.stdout.write('='*70 + '\n')
    
    def _parse_prompt_data(self, item: Dict) -> PromptData:
        """Parse and validate individual prompt data according to ingestion agent spec"""
        # Clean and normalize title - try multiple field names
        title = (
            item.get('title', '') or 
            item.get('prompt_title', '') or 
            item.get('name', '')
        ).strip()
        
        if not title:
            title = f"Untitled Template {timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        # Convert to sentence case and truncate
        title = self._normalize_title(title)
        
        # Clean description - try multiple field names
        description = (
            item.get('description', '') or 
            item.get('prompt_description', '')
        ).strip()
        description = self._normalize_description(description)
        
        # Get template content - try multiple field names
        template_content = (
            item.get('template_content', '') or 
            item.get('prompt_template', '') or 
            item.get('content', '')
        ).strip()
        if not template_content:
            template_content = description  # Use description as fallback
        
        # Normalize placeholders
        template_content = self._normalize_placeholders(template_content)
        
        # Category and domain - try multiple field names
        intent_category = (
            item.get('intent_category', '') or 
            item.get('category', '')
        ).strip()
        domain = item.get('domain', '').strip()
        category_name = domain or intent_category or 'General'
        
        # Tags - try multiple field names
        tags = item.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        tags = [self._normalize_tag(tag) for tag in tags] if tags else []
        
        # Inputs - try multiple field names
        required_inputs = item.get('required_inputs', []) or []
        optional_inputs = item.get('optional_inputs', []) or []
        
        # Validate placeholders exist in template
        all_placeholders = self._extract_placeholders(template_content)
        required_inputs = [p for p in required_inputs if p in all_placeholders] if required_inputs else []
        optional_inputs = [p for p in optional_inputs if p in all_placeholders] if optional_inputs else []
        
        # Models and tips
        ideal_models = item.get('ideal_models', []) or []
        power_tips = item.get('power_tips', []) or []
        
        # Metadata - try to extract from top level or nested
        metadata = item.get('metadata', {}) or {}
        complexity = str(metadata.get('complexity', item.get('complexity_score', 'Medium'))).title()
        tone = metadata.get('tone', item.get('tone', ''))
        framework = metadata.get('framework', item.get('prompt_framework', ''))
        
        # Quality score - try multiple sources
        try:
            quality_score = float(
                metadata.get('quality_score') or 
                item.get('quality_score') or 
                0.0
            )
            # Normalize to 0-100 scale if it's 0-1
            if quality_score > 0 and quality_score < 1:
                quality_score = quality_score * 100
        except (ValueError, TypeError):
            quality_score = 0.0
        
        # Popularity score
        try:
            popularity_score = float(item.get('popularity_score', 0.0) or 0.0)
        except (ValueError, TypeError):
            popularity_score = 0.0
        
        # External ID and subcategory
        external_id = item.get('external_id', '').strip() or None
        subcategory = item.get('subcategory', '').strip()
        use_cases = item.get('use_cases', []) or []
        
        return PromptData(
            title=title,
            description=description,
            template_content=template_content,
            category_name=category_name,
            tags=tags,
            required_inputs=required_inputs,
            optional_inputs=optional_inputs,
            ideal_models=ideal_models,
            power_tips=power_tips,
            complexity=complexity,
            tone=tone,
            framework=framework,
            quality_score=quality_score,
            popularity_score=popularity_score,
            intent_category=intent_category,
            domain=domain,
            external_id=external_id,
            subcategory=subcategory,
            use_cases=use_cases
        )
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title to sentence case and truncate for SEO"""
        if not title:
            return title
        
        # Convert to sentence case
        title = title[0].upper() + title[1:].lower() if title else title
        
        # Truncate to 65 characters for SEO
        if len(title) > 65:
            title = title[:62] + "..."
        
        return title
    
    def _normalize_description(self, description: str) -> str:
        """Normalize description for SEO (150-160 characters)"""
        if not description:
            return "A powerful template for generating high-quality content."
        
        # Remove boilerplate
        boilerplate_patterns = [
            r"^This prompt helps",
            r"^This template",
            r"^Generate",
            r"^Create"
        ]
        
        for pattern in boilerplate_patterns:
            description = re.sub(pattern, "", description, flags=re.IGNORECASE).strip()
        
        # Ensure length is 150-160 characters
        if len(description) < 150:
            description = f"This template helps {description.lower()}"
        elif len(description) > 160:
            description = description[:157] + "..."
        
        return description
    
    def _normalize_placeholders(self, content: str) -> str:
        """Normalize placeholders to {{snake_case}}"""
        # Convert various placeholder formats to {{snake_case}}
        # Handle {{Role}}, {{role}}, {{ROLE}} -> {{role}}
        def normalize_placeholder(match):
            placeholder = match.group(1)
            # Convert to snake_case
            normalized = re.sub(r'(?<!^)(?=[A-Z])', '_', placeholder).lower()
            return f"{{{{{normalized}}}}}"
        
        # Match {{anything}} patterns
        content = re.sub(r'\{\{([^}]+)\}\}', normalize_placeholder, content)
        return content
    
    def _extract_placeholders(self, content: str) -> List[str]:
        """Extract all placeholders from template content"""
        matches = re.findall(r'\{\{([^}]+)\}\}', content)
        return list(set(matches))  # Remove duplicates
    
    def _normalize_tag(self, tag: str) -> str:
        """Normalize tag to lowercase hyphen-separated format"""
        if not tag:
            return tag
        
        # Convert spaces and underscores to hyphens
        tag = re.sub(r'[\s_]+', '-', tag.lower())
        # Remove non-alphanumeric characters except hyphens
        tag = re.sub(r'[^a-z0-9-]', '', tag)
        # Remove multiple consecutive hyphens
        tag = re.sub(r'-+', '-', tag)
        # Trim hyphens from start/end
        tag = tag.strip('-')
        
        return tag
    
    def _calculate_quality_score(self, item: Dict) -> float:
        """Calculate quality score from available data or weighted signals"""
        # First, try to use existing quality_score from data
        try:
            quality_score = float(item.get('quality_score', 0) or 0)
            # Normalize to 0-100 scale if it's 0-1
            if quality_score > 0 and quality_score < 1:
                quality_score = quality_score * 100
            if quality_score > 0:
                return quality_score
        except (ValueError, TypeError):
            pass
        
        # Fallback to weighted signal calculation
        weights = {
            "role_definition": 0.20,
            "context_depth": 0.20,
            "task_precision": 0.20,
            "example_inclusion": 0.15,
            "output_control": 0.10,
            "reasoning_depth": 0.10,
            "compliance_safety": 0.05
        }
        
        # Get content from multiple possible field names
        template_content = (
            item.get('template_content', '') or 
            item.get('prompt_template', '') or 
            item.get('content', '')
        )
        required_inputs = item.get('required_inputs', []) or []
        power_tips = item.get('power_tips', []) or []
        description = item.get('description', '')
        framework = item.get('prompt_framework', '') or item.get('framework', '')
        complexity = item.get('complexity_score', 2)  # Try to get from complexity_score
        
        signals = {
            "role_definition": bool(required_inputs),
            "context_depth": len(description) > 50,
            "task_precision": "{{" in template_content or "you are a" in template_content.lower(),
            "example_inclusion": bool(power_tips),
            "output_control": bool(framework),
            "reasoning_depth": int(complexity) > 2,
            "compliance_safety": "unsafe" not in template_content.lower()
        }
        
        score = sum(weights[k] * int(signals[k]) for k in weights)
        return round(score * 100, 2)
    
    def _generate_source_hash(self, title: str, content: str) -> str:
        """Generate SHA1 hash for deduplication"""
        canonical_text = f"{title.strip().lower()}{content.strip().lower()}"
        return hashlib.sha1(canonical_text.encode('utf-8')).hexdigest()
    
    def _update_search_vectors(self):
        """Update search vectors for full-text search"""
        self.stdout.write('Updating search vectors...')
        
        start_time = time.time()
        
        # Use raw SQL for better performance
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE prompt_library 
                SET search_vector = 
                    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                    setweight(to_tsvector('english', coalesce(content, '')), 'B') ||
                    setweight(to_tsvector('english', coalesce(category, '')), 'C')
                WHERE search_vector IS NULL OR search_vector = ''
            """)
            updated_count = cursor.rowcount
        
        update_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated_count} search vectors in {update_time:.2f}s'
            )
        )
    def _clear_cache(self):
        """Clear relevant caches"""
        self.stdout.write('Clearing caches...')
        
        try:
            # Attempt to clear multi-level cache internals if present
            if hasattr(multi_cache, 'memory_cache') and hasattr(multi_cache.memory_cache, 'clear'):
                try:
                    multi_cache.memory_cache.clear()
                except Exception:
                    logger.exception("Failed to clear multi_cache.memory_cache")
            if hasattr(multi_cache, 'memory_access_order') and hasattr(multi_cache.memory_access_order, 'clear'):
                try:
                    multi_cache.memory_access_order.clear()
                except Exception:
                    logger.exception("Failed to clear multi_cache.memory_access_order")
                # Try additional common internal attributes on multi_cache
                if hasattr(multi_cache, 'clear') and callable(multi_cache.clear):
                    try:
                        multi_cache.clear()
                    except Exception:
                        logger.exception("Failed to call multi_cache.clear()")
                for attr in ('_cache', 'memory', 'lru_cache', 'cache_store'):
                    if hasattr(multi_cache, attr):
                        try:
                            attr_obj = getattr(multi_cache, attr)
                            if hasattr(attr_obj, 'clear') and callable(attr_obj.clear):
                                attr_obj.clear()
                        except Exception:
                            logger.exception(f"Failed to clear multi_cache.{attr}")
            
            # Clear specific cache keys related to prompts
            cache_keys = [
                'prompt_library_all', 
                'prompt_categories', 
                'prompt_search_results',
                'prompt_popular'
            ]
            
            # Prefer bulk delete if available, otherwise delete keys individually
            if hasattr(cache, 'delete_many'):
                try:
                    cache.delete_many(cache_keys)
                except Exception:
                    logger.exception("cache.delete_many failed, falling back to individual deletes")
                    for key in cache_keys:
                        try:
                            cache.delete(key)
                        except Exception:
                            logger.exception(f"Failed to delete cache key: {key}")
            else:
                for key in cache_keys:
                    try:
                        cache.delete(key)
                    except Exception:
                        logger.exception(f"Failed to delete cache key: {key}")
            
            self.stdout.write(self.style.SUCCESS('Caches cleared'))
        except Exception as e:
            logger.exception(f"Error while clearing caches: {e}")
            self.stdout.write(self.style.WARNING('Failed to fully clear caches; see logs for details'))
    def _report_results(self):
        """Report ingestion results"""
        total_time = time.time() - self.start_time
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('INGESTION COMPLETED'))
        total_time = time.time() - self.start_time
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('INGESTION COMPLETED'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'Total prompts processed: {self.processed_count:,}')
        self.stdout.write(f'Errors encountered: {self.error_count:,}')
        
        # Avoid division by zero
        if self.processed_count > 0:
            success_rate = ((self.processed_count - self.error_count) / self.processed_count * 100)
            self.stdout.write(f'Success rate: {success_rate:.1f}%')
            
            avg_time_per_prompt = (total_time / self.processed_count) * 1000
            self.stdout.write(f'Average time per prompt: {avg_time_per_prompt:.2f}ms')
            
            prompts_per_second = self.processed_count / total_time
            self.stdout.write(f'Processing rate: {prompts_per_second:.1f} prompts/second')
            
            # Performance recommendations
            if avg_time_per_prompt > 50:
                self.stdout.write(
                    self.style.WARNING(
                        'Performance note: Consider increasing batch size or worker threads for faster processing'
                    )
                )
        else:
            self.stdout.write('Success rate: 0%')
            
        self.stdout.write(f'Total processing time: {total_time:.2f}s')
        
        # Database stats
        total_in_db = Template.objects.count()
        self.stdout.write(f'Total templates in database: {total_in_db:,}')
        
        self.stdout.write('\n' + self.style.SUCCESS('Ready for high-performance search and optimization!'))


# Sample data generator for testing
class PromptDataGenerator:
    """Generate sample prompt data for testing"""
    
    CATEGORIES = [
        'content_creation', 'technical_writing', 'communication',
        'analysis', 'creative', 'coding', 'business', 'education'
    ]
    
    SAMPLE_PROMPTS = [
        "Write a professional email requesting a meeting with a client to discuss project updates and deliverables.",
        "Create a detailed technical documentation for a REST API including authentication methods and error handling.",
        "Generate a compelling marketing copy for a new SaaS product targeting small business owners.",
        "Analyze the key factors that contribute to employee satisfaction in remote work environments.",
        "Draft a creative story opening that hooks readers with an intriguing mystery or conflict.",
        "Write Python code to implement a binary search algorithm with proper error handling.",
        "Compose a quarterly business report highlighting key performance metrics and growth strategies.",
        "Develop a lesson plan for teaching basic programming concepts to high school students."
    ]
    
    @classmethod
    def generate_sample_file(cls, filename: str, count: int = 1000, format_type: str = 'json'):
        """Generate sample prompt data file"""
        import random
        
        data = []
        for i in range(count):
            category = random.choice(cls.CATEGORIES)
            base_prompt = random.choice(cls.SAMPLE_PROMPTS)
            
            prompt_data = {
                'title': f'Prompt {i+1}: {category.replace("_", " ").title()}',
                'content': f'{base_prompt} (Variation {i+1})',
                'category': category,
                'subcategory': f'{category}_sub_{random.randint(1, 3)}',
                'tags': random.sample(['professional', 'creative', 'technical', 'business', 'academic'], 
                                    random.randint(1, 3)),
                'keywords': random.sample(['write', 'create', 'analyze', 'develop', 'implement'], 
                                        random.randint(1, 3)),
                'intent_category': category,
                'use_case': f'Use case for {category}',
                'complexity_score': random.randint(1, 10),
                'quality_score': random.uniform(60.0, 95.0),
                'source': 'generated',
                'author': 'system'
            }
            data.append(prompt_data)
        
        # Save data
        if format_type == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif format_type == 'jsonl':
            with open(filename, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        elif format_type == 'csv':
            # Convert list fields to JSON strings for CSV
            for item in data:
                for field in ['tags', 'keywords', 'required_inputs', 'optional_inputs', 'ideal_models', 'power_tips']:
                    if field in item and isinstance(item[field], list):
                        item[field] = json.dumps(item[field])
            
            # Write CSV manually to avoid pandas dependency
            if data:
                keys = data[0].keys()
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data)
        
        print(f'Generated {count} sample prompts in {filename}')