"""
High-performance management command to ingest 100K+ prompts
Optimized for speed and memory efficiency with progress tracking
"""

import json
import time
import logging
import csv
from typing import Dict, List, Any, Optional
from pathlib import Path
import concurrent.futures
from dataclasses import dataclass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection
from django.utils import timezone
from django.core.cache import cache

from apps.templates.models import PromptLibrary
from apps.templates.cache_services import multi_cache

logger = logging.getLogger(__name__)

@dataclass
class PromptData:
    """Data structure for prompt information"""
    title: str
    content: str
    category: str
    subcategory: str = ""
    tags: List[str] = None
    keywords: List[str] = None
    intent_category: str = ""
    use_case: str = ""
    complexity_score: int = 1
    source: str = ""
    author: str = ""
    quality_score: float = 0.0

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
        parser.add_argument(
            '--file',
            type=str,
            help='Path to the prompt data file (JSON, CSV, or JSONL)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'jsonl'],
            default='json',
            help='Format of the input file'
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
            help='Clear existing prompt library before ingestion'
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
        
    def handle(self, *args, **options):
        """Main command handler"""
        self.start_time = time.time()
        self.batch_size = options['batch_size']
        self.thread_pool_size = options['workers']
        
        try:
            self.stdout.write(
                self.style.SUCCESS('Starting 100K prompt ingestion process...')
            )
            
            # Validate inputs
            file_path = self._validate_inputs(options)
            
            # Determine format from file extension if not explicitly specified
            format_type = options['format']
            if file_path.suffix.lower() == '.jsonl' and format_type == 'json':
                format_type = 'jsonl'
                self.stdout.write(
                    self.style.WARNING(f'Detected JSONL file, switching to JSONL format')
                )
            
            # Clear existing data if requested
            if options['clear_existing'] and not options['dry_run']:
                self._clear_existing_data()
            
            # Load and process data
            prompt_data = self._load_prompt_data(file_path, format_type)
            
            # Apply sample size if specified
            if options['sample_size']:
                prompt_data = prompt_data[:options['sample_size']]
                self.stdout.write(
                    self.style.WARNING(f'Processing sample of {len(prompt_data)} prompts')
                )
            
            # Process prompts in batches
            self._process_prompts(prompt_data, options['dry_run'])
            
            # Update search vectors if requested
            if options['update_search_vectors'] and not options['dry_run']:
                self._update_search_vectors()
            
            # Clear cache to ensure fresh data
            if not options['dry_run']:
                self._clear_cache()
            
            # Report results
            self._report_results()
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            raise CommandError(f"Ingestion failed: {e}")
    
    def _validate_inputs(self, options) -> Path:
        """Validate command inputs"""
        file_path = options.get('file')
        if not file_path:
            raise CommandError("--file parameter is required")
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise CommandError(f"Path is not a file: {file_path}")
        
        # Check file size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 1000:  # 1GB limit
            self.stdout.write(
                self.style.WARNING(f'Large file detected: {file_size_mb:.1f}MB')
            )
        
        return file_path
    
    def _clear_existing_data(self):
        """Clear existing prompt library data"""
        self.stdout.write('Clearing existing prompt library...')
        
        with transaction.atomic():
            count = PromptLibrary.objects.count()
            PromptLibrary.objects.all().delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'Cleared {count} existing prompts')
        )
    
    def _load_prompt_data(self, file_path: Path, format_type: str) -> List[Dict]:
        """Load prompt data from file with progress tracking"""
        self.stdout.write(f'Loading data from {file_path}...')
        
        start_time = time.time()
        
        if format_type == 'json':
            data = self._load_json(file_path)
        elif format_type == 'csv':
            data = self._load_csv(file_path)
        elif format_type == 'jsonl':
            data = self._load_jsonl(file_path)
        else:
            raise CommandError(f"Unsupported format: {format_type}")
        
        load_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded {len(data)} records in {load_time:.2f}s'
            )
        )
        
        return data
    
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
    
    def _process_prompts(self, prompt_data: List[Dict], dry_run: bool = False):
        """Process prompts in parallel batches"""
        total_count = len(prompt_data)
        self.stdout.write(f'Processing {total_count} prompts...')
        
        # Split data into batches
        batches = [
            prompt_data[i:i + self.batch_size]
            for i in range(0, total_count, self.batch_size)
        ]
        
        # Process batches with threading
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.thread_pool_size) as executor:
            # Submit all batches
            futures = [
                executor.submit(self._process_batch, batch, batch_num, dry_run)
                for batch_num, batch in enumerate(batches)
            ]
            
            # Wait for completion and collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    batch_count, batch_errors = future.result()
                    self.processed_count += batch_count
                    self.error_count += batch_errors
                    
                    # Progress update
                    progress = (self.processed_count / total_count) * 100
                    self.stdout.write(
                        f'\rProgress: {self.processed_count}/{total_count} '
                        f'({progress:.1f}%) - Errors: {self.error_count}',
                        ending=''
                    )
                    
                except Exception as e:
                    logger.error(f"Batch processing error: {e}")
                    self.error_count += len(batches[0])  # Estimate
        
        self.stdout.write('')  # New line after progress
    
    def _process_batch(self, batch: List[Dict], batch_num: int, dry_run: bool) -> tuple:
        """Process a single batch of prompts"""
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
        
        # Prepare prompt objects
        prompt_objects = []
        for item in batch:
            try:
                prompt_data = self._parse_prompt_data(item)
                prompt_obj = PromptLibrary(
                    title=prompt_data.title,
                    content=prompt_data.content,
                    category=prompt_data.category,
                    subcategory=prompt_data.subcategory,
                    tags=prompt_data.tags or [],
                    keywords=prompt_data.keywords or [],
                    intent_category=prompt_data.intent_category,
                    use_case=prompt_data.use_case,
                    complexity_score=prompt_data.complexity_score,
                    estimated_tokens=len(prompt_data.content.split()) * 1.3,  # Rough estimate
                    source=prompt_data.source,
                    author=prompt_data.author,
                    quality_score=prompt_data.quality_score,
                    is_active=True,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                prompt_objects.append(prompt_obj)
                batch_count += 1
                
            except Exception as e:
                logger.warning(f"Batch {batch_num} item processing error: {e}")
                batch_errors += 1
        
        # Bulk insert with transaction
        if prompt_objects:
            try:
                with transaction.atomic():
                    PromptLibrary.objects.bulk_create(
                        prompt_objects,
                        batch_size=self.batch_size,
                        ignore_conflicts=True  # Skip duplicates
                    )
            except Exception as e:
                logger.error(f"Batch {batch_num} database error: {e}")
                batch_errors += len(prompt_objects)
                batch_count = 0
        
        return batch_count, batch_errors
    
    def _parse_prompt_data(self, item: Dict) -> PromptData:
        """Parse and validate individual prompt data"""
        # Required fields
        title = item.get('title', '').strip()
        content = item.get('content', '').strip()
        category = item.get('category', 'general').strip()
        
        if not title:
            title = f"Untitled Prompt {timezone.now().strftime('%Y%m%d%H%M%S')}"
            
        if not content:
            content = "Default content for empty prompt"
        elif len(content) < 10:
            content = f"Extended content: {content}"
        elif len(content) > 10000:
            content = content[:10000]
        
        # Optional fields with defaults
        subcategory = item.get('subcategory', '').strip()
        tags = item.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        
        keywords = item.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        
        intent_category = item.get('intent_category', '').strip()
        use_case = item.get('use_case', '').strip()
        
        # Numeric fields
        try:
            complexity_score = int(item.get('complexity_score', 1))
            complexity_score = max(1, min(10, complexity_score))  # Clamp 1-10
        except (ValueError, TypeError):
            complexity_score = 1
        
        try:
            quality_score = float(item.get('quality_score', 0.0))
            quality_score = max(0.0, min(100.0, quality_score))  # Clamp 0-100
        except (ValueError, TypeError):
            quality_score = 0.0
        
        # Metadata
        source = item.get('source', '').strip()
        author = item.get('author', '').strip()
        
        return PromptData(
            title=title,
            content=content,
            category=category,
            subcategory=subcategory,
            tags=tags,
            keywords=keywords,
            intent_category=intent_category,
            use_case=use_case,
            complexity_score=complexity_score,
            source=source,
            author=author,
            quality_score=quality_score
        )
    
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
        self.stdout.write('='*60)
        
        self.stdout.write(f'Total prompts processed: {self.processed_count:,}')
        self.stdout.write(f'Errors encountered: {self.error_count:,}')
        
        # Avoid division by zero
        if self.processed_count > 0:
            success_rate = ((self.processed_count - self.error_count) / self.processed_count * 100)
            self.stdout.write(f'Success rate: {success_rate:.1f}%')
        else:
            self.stdout.write('Success rate: 0%')
            
        self.stdout.write(f'Total processing time: {total_time:.2f}s')
        total_time = time.time() - self.start_time
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('INGESTION COMPLETED'))
        self.stdout.write('='*60)
        
        self.stdout.write(f'Total prompts processed: {self.processed_count:,}')
        self.stdout.write(f'Errors encountered: {self.error_count:,}')
        self.stdout.write(f'Success rate: {((self.processed_count - self.error_count) / self.processed_count * 100):.1f}%')
        self.stdout.write(f'Total processing time: {total_time:.2f}s')
        
        if self.processed_count > 0:
            avg_time_per_prompt = (total_time / self.processed_count) * 1000
            self.stdout.write(f'Average time per prompt: {avg_time_per_prompt:.2f}ms')
            
            prompts_per_second = self.processed_count / total_time
            self.stdout.write(f'Processing rate: {prompts_per_second:.1f} prompts/second')
        
        # Database stats
        total_in_db = PromptLibrary.objects.count()
        self.stdout.write(f'Total prompts in database: {total_in_db:,}')
        
        # Performance recommendations
        if avg_time_per_prompt > 50:
            self.stdout.write(
                self.style.WARNING(
                    'Performance note: Consider increasing batch size or worker threads for faster processing'
                )
            )
        
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
            import pandas as pd
            # Convert list fields to JSON strings for CSV
            for item in data:
                for field in ['tags', 'keywords']:
                    item[field] = json.dumps(item[field])
            
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8')
        
        print(f'Generated {count} sample prompts in {filename}')