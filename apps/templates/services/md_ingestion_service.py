"""
Markdown Ingestion Service for extracting prompts from MD files
Handles large-scale prompt extraction and database seeding
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField, FieldType

User = get_user_model()
logger = logging.getLogger(__name__)


class MarkdownPromptExtractor:
    """Extract structured prompts from markdown files"""
    
    def __init__(self):
        self.prompt_patterns = {
            'header': r'^#{1,6}\s+(.+?)$',
            'code_block': r'```[\s\S]*?```',
            'variable': r'\{\{([^}]+)\}\}',
            'category_marker': r'\*\*Category\*\*:\s*(.+?)(?:\n|\*\*)',
            'revenue_marker': r'\*\*Revenue Potential\*\*:\s*(.+?)(?:\n|\*\*)',
            'audience_marker': r'\*\*Target Audience\*\*:\s*(.+?)(?:\n|\*\*)',
            'template_block': r'```\n(.*?)\n```',
            'field_definition': r'\*\*([^*]+)\*\*:\s*(.+?)(?:\n|$)',
        }
        
    def extract_prompts_from_md(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract all prompts from a markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            return self._parse_markdown_content(content, file_path)
        except Exception as e:
            logger.error(f"Error reading MD file {file_path}: {str(e)}")
            return []
    
    def _parse_markdown_content(self, content: str, source_file: str) -> List[Dict[str, Any]]:
        """Parse markdown content and extract structured prompts"""
        prompts = []
        sections = self._split_into_sections(content)
        
        for section in sections:
            prompt_data = self._extract_prompt_from_section(section, source_file)
            if prompt_data:
                prompts.append(prompt_data)
        
        return prompts
    
    def _split_into_sections(self, content: str) -> List[str]:
        """Split markdown content into logical sections"""
        # Split by major headers or template blocks
        sections = []
        current_section = ""
        
        lines = content.split('\n')
        for line in lines:
            if re.match(r'^#{1,3}\s+', line) and current_section.strip():
                sections.append(current_section)
                current_section = line + '\n'
            else:
                current_section += line + '\n'
        
        if current_section.strip():
            sections.append(current_section)
        
        return sections
    
    def _extract_prompt_from_section(self, section: str, source_file: str) -> Optional[Dict[str, Any]]:
        """Extract prompt data from a markdown section"""
        try:
            # Extract basic metadata
            title = self._extract_title(section)
            if not title:
                return None
            
            category = self._extract_metadata(section, 'category_marker') or 'General'
            revenue_potential = self._extract_metadata(section, 'revenue_marker')
            target_audience = self._extract_metadata(section, 'audience_marker')
            
            # Extract template content and variables
            template_content = self._extract_template_content(section)
            if not template_content:
                return None
            
            variables = self._extract_variables(template_content)
            description = self._generate_description(section, title)
            tags = self._extract_tags(section)
            
            return {
                'title': title,
                'description': description,
                'category': category,
                'template_content': template_content,
                'variables': variables,
                'metadata': {
                    'revenue_potential': revenue_potential,
                    'target_audience': target_audience,
                    'source_file': source_file,
                    'extracted_at': None,  # Will be set during processing
                },
                'tags': tags,
                'is_ai_generated': False,
                'popularity_score': self._calculate_initial_popularity(section),
            }
        except Exception as e:
            logger.error(f"Error extracting prompt from section: {str(e)}")
            return None
    
    def _extract_title(self, section: str) -> Optional[str]:
        """Extract title from section header"""
        lines = section.strip().split('\n')
        for line in lines[:5]:  # Check first 5 lines
            match = re.match(self.prompt_patterns['header'], line.strip())
            if match:
                title = match.group(1).strip()
                # Clean up title (remove markdown formatting)
                title = re.sub(r'[*_`#]', '', title)
                return title[:200]  # Limit title length
        return None
    
    def _extract_metadata(self, section: str, pattern_key: str) -> Optional[str]:
        """Extract metadata using regex patterns"""
        pattern = self.prompt_patterns.get(pattern_key)
        if not pattern:
            return None
        
        match = re.search(pattern, section, re.MULTILINE | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_template_content(self, section: str) -> Optional[str]:
        """Extract the main template content from code blocks"""
        code_blocks = re.findall(self.prompt_patterns['code_block'], section, re.DOTALL)
        
        if code_blocks:
            # Return the largest code block (likely the main template)
            return max(code_blocks, key=len).strip('```').strip()
        
        # If no code blocks, try to extract from the section itself
        lines = section.split('\n')
        template_lines = []
        in_template = False
        
        for line in lines:
            if '{{' in line and '}}' in line:
                in_template = True
            if in_template:
                template_lines.append(line)
            if in_template and not ('{{' in line or '}}' in line) and line.strip() == '':
                break
        
        if template_lines:
            return '\n'.join(template_lines).strip()
        
        return None
    
    def _extract_variables(self, template_content: str) -> List[Dict[str, str]]:
        """Extract template variables and their properties"""
        variables = []
        matches = re.findall(self.prompt_patterns['variable'], template_content)
        
        for match in matches:
            var_name = match.strip()
            if var_name and var_name not in [v['name'] for v in variables]:
                variables.append({
                    'name': var_name,
                    'label': self._humanize_variable_name(var_name),
                    'type': self._guess_field_type(var_name),
                    'required': True,
                    'placeholder': f"Enter {self._humanize_variable_name(var_name).lower()}",
                })
        
        return variables
    
    def _humanize_variable_name(self, var_name: str) -> str:
        """Convert variable name to human-readable label"""
        # Replace underscores with spaces and title case
        return var_name.replace('_', ' ').title()
    
    def _guess_field_type(self, var_name: str) -> str:
        """Guess appropriate field type based on variable name"""
        var_lower = var_name.lower()
        
        if any(keyword in var_lower for keyword in ['description', 'content', 'details', 'summary']):
            return FieldType.TEXTAREA
        elif any(keyword in var_lower for keyword in ['number', 'count', 'amount', 'price', 'cost']):
            return FieldType.NUMBER
        elif any(keyword in var_lower for keyword in ['type', 'category', 'level', 'priority']):
            return FieldType.DROPDOWN
        else:
            return FieldType.TEXT
    
    def _generate_description(self, section: str, title: str) -> str:
        """Generate description from section content"""
        lines = section.split('\n')
        description_lines = []
        
        # Look for description-like content
        for line in lines:
            line = line.strip()
            if (line and 
                not line.startswith('#') and 
                not line.startswith('**') and 
                not line.startswith('```') and
                len(line) > 20):
                description_lines.append(line)
                if len(description_lines) >= 3:  # Limit description length
                    break
        
        if description_lines:
            return ' '.join(description_lines)[:500]  # Limit description length
        
        return f"AI-generated template for {title.lower()}"
    
    def _extract_tags(self, section: str) -> List[str]:
        """Extract relevant tags from section content"""
        tags = []
        
        # Extract from common patterns
        text = section.lower()
        
        # Technology tags
        tech_keywords = ['ai', 'machine learning', 'saas', 'api', 'automation', 'analytics', 'marketing', 'business']
        for keyword in tech_keywords:
            if keyword in text:
                tags.append(keyword)
        
        # Industry tags from content
        industry_keywords = ['healthcare', 'finance', 'education', 'retail', 'technology', 'consulting']
        for keyword in industry_keywords:
            if keyword in text:
                tags.append(keyword)
        
        return list(set(tags))[:10]  # Limit to 10 unique tags
    
    def _calculate_initial_popularity(self, section: str) -> float:
        """Calculate initial popularity score based on content analysis"""
        score = 0.0
        
        # Higher score for more detailed templates
        if '{{' in section:
            score += 0.3
        
        # Higher score for revenue-related content
        if any(keyword in section.lower() for keyword in ['revenue', 'profit', 'money', 'sales']):
            score += 0.2
        
        # Higher score for structured content
        if '**' in section:  # Bold formatting
            score += 0.1
        
        # Higher score for longer, more detailed content
        word_count = len(section.split())
        if word_count > 100:
            score += 0.2
        elif word_count > 50:
            score += 0.1
        
        return min(score, 1.0)


class DatabaseIngestionService:
    """Service for ingesting extracted prompts into the database"""
    
    def __init__(self, default_author_username: str = 'system'):
        self.default_author = self._get_or_create_system_user(default_author_username)
        self.category_cache = {}
        
    def _get_or_create_system_user(self, username: str) -> User:
        """Get or create system user for authored templates"""
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@system.local',
                'first_name': 'System',
                'last_name': 'Generator',
                'is_staff': True,
            }
        )
        return user
    
    @transaction.atomic
    def bulk_ingest_prompts(self, prompts_data: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, int]:
        """Bulk ingest prompts with efficient database operations"""
        stats = {
            'total_processed': 0,
            'successfully_created': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'categories_created': 0,
            'fields_created': 0,
        }
        
        try:
            # Process in batches for memory efficiency
            for i in range(0, len(prompts_data), batch_size):
                batch = prompts_data[i:i + batch_size]
                batch_stats = self._process_batch(batch)
                
                # Update overall stats
                for key, value in batch_stats.items():
                    stats[key] += value
                
                logger.info(f"Processed batch {i//batch_size + 1}, {len(batch)} prompts")
        
        except Exception as e:
            logger.error(f"Error during bulk ingestion: {str(e)}")
            stats['errors'] += 1
        
        return stats
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a single batch of prompts"""
        batch_stats = {
            'total_processed': 0,
            'successfully_created': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'categories_created': 0,
            'fields_created': 0,
        }
        
        for prompt_data in batch:
            try:
                batch_stats['total_processed'] += 1
                result = self._create_template_from_data(prompt_data)
                
                if result['success']:
                    batch_stats['successfully_created'] += 1
                    if result.get('category_created'):
                        batch_stats['categories_created'] += 1
                    batch_stats['fields_created'] += result.get('fields_created', 0)
                else:
                    if 'duplicate' in result.get('reason', ''):
                        batch_stats['skipped_duplicates'] += 1
                    else:
                        batch_stats['errors'] += 1
            
            except Exception as e:
                logger.error(f"Error processing prompt '{prompt_data.get('title', 'Unknown')}': {str(e)}")
                batch_stats['errors'] += 1
        
        return batch_stats
    
    def _create_template_from_data(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a template and associated fields from prompt data"""
        try:
            # Check for duplicates
            if Template.objects.filter(title=prompt_data['title']).exists():
                return {'success': False, 'reason': 'duplicate'}
            
            # Get or create category
            category, category_created = self._get_or_create_category(prompt_data['category'])
            
            # Create template
            template = Template.objects.create(
                title=prompt_data['title'],
                description=prompt_data['description'],
                category=category,
                template_content=prompt_data['template_content'],
                author=self.default_author,
                tags=prompt_data.get('tags', []),
                is_ai_generated=prompt_data.get('is_ai_generated', False),
                popularity_score=prompt_data.get('popularity_score', 0.0),
                smart_suggestions=prompt_data.get('metadata', {}),
            )
            
            # Create fields from variables
            fields_created = 0
            for i, var_data in enumerate(prompt_data.get('variables', [])):
                field = PromptField.objects.create(
                    label=var_data['label'],
                    placeholder=var_data.get('placeholder', ''),
                    field_type=var_data.get('type', FieldType.TEXT),
                    is_required=var_data.get('required', True),
                    help_text=f"Variable: {var_data['name']}",
                    order=i,
                )
                
                TemplateField.objects.create(
                    template=template,
                    field=field,
                    order=i,
                )
                fields_created += 1
            
            return {
                'success': True,
                'template_id': template.id,
                'category_created': category_created,
                'fields_created': fields_created,
            }
        
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return {'success': False, 'reason': str(e)}
    
    def _get_or_create_category(self, category_name: str) -> Tuple[TemplateCategory, bool]:
        """Get or create a template category with caching"""
        if category_name in self.category_cache:
            return self.category_cache[category_name], False
        
        category, created = TemplateCategory.objects.get_or_create(
            name=category_name,
            defaults={
                'slug': slugify(category_name),
                'description': f'Templates for {category_name.lower()}',
                'is_active': True,
            }
        )
        
        self.category_cache[category_name] = category
        return category, created


class MarkdownIngestionManager:
    """Main manager for coordinating MD ingestion process"""
    
    def __init__(self):
        self.extractor = MarkdownPromptExtractor()
        self.ingestion_service = DatabaseIngestionService()
    
    def ingest_from_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest prompts from a single markdown file"""
        logger.info(f"Starting ingestion from file: {file_path}")
        
        # Extract prompts
        prompts_data = self.extractor.extract_prompts_from_md(file_path)
        
        if not prompts_data:
            return {
                'success': False,
                'message': 'No prompts extracted from file',
                'stats': {},
            }
        
        # Ingest to database
        stats = self.ingestion_service.bulk_ingest_prompts(prompts_data)
        
        return {
            'success': True,
            'message': f'Successfully processed {len(prompts_data)} prompts',
            'stats': stats,
            'prompts_extracted': len(prompts_data),
        }
    
    def ingest_from_directory(self, directory_path: str, pattern: str = "*.md") -> Dict[str, Any]:
        """Ingest prompts from all markdown files in a directory"""
        logger.info(f"Starting batch ingestion from directory: {directory_path}")
        
        directory = Path(directory_path)
        md_files = list(directory.glob(pattern))
        
        if not md_files:
            return {
                'success': False,
                'message': 'No markdown files found in directory',
                'stats': {},
            }
        
        total_stats = {
            'total_processed': 0,
            'successfully_created': 0,
            'skipped_duplicates': 0,
            'errors': 0,
            'categories_created': 0,
            'fields_created': 0,
        }
        
        processed_files = []
        
        for md_file in md_files:
            try:
                result = self.ingest_from_file(str(md_file))
                if result['success']:
                    # Merge stats
                    for key, value in result['stats'].items():
                        total_stats[key] += value
                    
                    processed_files.append({
                        'file': str(md_file),
                        'prompts_extracted': result['prompts_extracted'],
                        'success': True,
                    })
                else:
                    processed_files.append({
                        'file': str(md_file),
                        'error': result['message'],
                        'success': False,
                    })
                    total_stats['errors'] += 1
            
            except Exception as e:
                logger.error(f"Error processing file {md_file}: {str(e)}")
                processed_files.append({
                    'file': str(md_file),
                    'error': str(e),
                    'success': False,
                })
                total_stats['errors'] += 1
        
        return {
            'success': True,
            'message': f'Processed {len(md_files)} files',
            'stats': total_stats,
            'files': processed_files,
        }
    
    def ingest_from_json(self, json_file_path: str) -> Dict[str, Any]:
        """Ingest prompts from JSON file format"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert JSON format to our prompt format
            prompts_data = self._convert_json_to_prompts(data)
            
            if not prompts_data:
                return {
                    'success': False,
                    'message': 'No valid prompts found in JSON file',
                    'stats': {},
                }
            
            # Ingest to database
            stats = self.ingestion_service.bulk_ingest_prompts(prompts_data)
            
            return {
                'success': True,
                'message': f'Successfully processed {len(prompts_data)} prompts from JSON',
                'stats': stats,
                'prompts_extracted': len(prompts_data),
            }
        
        except Exception as e:
            logger.error(f"Error processing JSON file {json_file_path}: {str(e)}")
            return {
                'success': False,
                'message': f'Error processing JSON file: {str(e)}',
                'stats': {},
            }
    
    def _convert_json_to_prompts(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert JSON prompt library format to our internal format"""
        prompts = []
        
        # Handle different JSON structures
        if 'prompts' in json_data:
            prompt_list = json_data['prompts']
        elif isinstance(json_data, list):
            prompt_list = json_data
        else:
            # Try to find prompt-like objects in the JSON
            prompt_list = []
            for key, value in json_data.items():
                if isinstance(value, dict) and any(field in value for field in ['title', 'prompt', 'template']):
                    prompt_list.append(value)
        
        for item in prompt_list:
            try:
                prompt_data = self._convert_json_item_to_prompt(item)
                if prompt_data:
                    prompts.append(prompt_data)
            except Exception as e:
                logger.error(f"Error converting JSON item: {str(e)}")
                continue
        
        return prompts
    
    def _convert_json_item_to_prompt(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a single JSON item to prompt format"""
        # Extract title
        title = item.get('title') or item.get('name') or item.get('prompt_name')
        if not title:
            return None
        
        # Extract template content
        template_content = (
            item.get('template') or 
            item.get('prompt') or 
            item.get('content') or 
            item.get('text', '')
        )
        
        if not template_content:
            return None
        
        # Extract other fields
        description = (
            item.get('description') or 
            item.get('summary') or 
            f"AI prompt template: {title}"
        )
        
        category = item.get('category') or item.get('type') or 'General'
        tags = item.get('tags', [])
        if isinstance(tags, str):
            tags = [tag.strip() for tag in tags.split(',')]
        
        # Extract variables from template content
        variables = []
        var_matches = re.findall(r'\[([^\]]+)\]|\{([^}]+)\}|\<([^>]+)\>', template_content)
        for match in var_matches:
            var_name = next((m for m in match if m), None)
            if var_name:
                variables.append({
                    'name': var_name,
                    'label': var_name.replace('_', ' ').title(),
                    'type': FieldType.TEXT,
                    'required': True,
                    'placeholder': f"Enter {var_name.lower()}",
                })
        
        return {
            'title': title[:200],
            'description': description[:500],
            'category': category,
            'template_content': template_content,
            'variables': variables,
            'tags': tags[:10],
            'metadata': {
                'source_type': 'json',
                'original_data': item,
            },
            'is_ai_generated': False,
            'popularity_score': float(item.get('rating', 0.5)),
        }