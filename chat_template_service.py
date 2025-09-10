# apps/ai_services/chat_template_service.py
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from django.contrib.auth import get_user_model
from celery import shared_task

from .template_extraction import template_extractor, template_analyzer, ExtractedTemplateData

# Import models (these will need to be added to Django apps)
try:
    from apps.chat.models import ChatSession, ChatMessage, ExtractedTemplate, UserTemplatePreference, TemplateMonetization
    from django_models import Template, TemplateCategory, PromptField, User
except ImportError:
    # Fallback - assume models exist
    pass

logger = logging.getLogger(__name__)
User = get_user_model()


class ChatTemplateIntegrationService:
    """Service to integrate template extraction with chat functionality"""
    
    def __init__(self):
        self.extractor = template_extractor
        self.analyzer = template_analyzer
        
    def process_chat_message(self, message: 'ChatMessage') -> Dict[str, Any]:
        """Process a chat message for template extraction"""
        result = {
            'message_id': str(message.id),
            'processed': False,
            'templates_found': 0,
            'templates_extracted': [],
            'error': None
        }
        
        try:
            # Only process assistant messages that are substantial
            if message.role != 'assistant' or len(message.content) < 100:
                return result
            
            # Check if already processed
            if message.extraction_processed:
                return result
            
            # Extract templates from message content
            extracted_templates = self.extractor.extract_templates_from_text(
                message.content,
                source_info={
                    'message_id': str(message.id),
                    'session_id': str(message.session.id),
                    'user_id': str(message.session.user.id),
                    'timestamp': message.created_at.isoformat()
                }
            )
            
            if extracted_templates:
                # Save extracted templates to database
                saved_templates = self._save_extracted_templates(
                    extracted_templates,
                    message,
                    message.session.user
                )
                
                # Update message flags
                with transaction.atomic():
                    message.contains_templates = True
                    message.templates_extracted = True
                    message.extraction_processed = True
                    message.save(update_fields=['contains_templates', 'templates_extracted', 'extraction_processed'])
                    
                    # Update session stats
                    session = message.session
                    session.extracted_templates_count += len(saved_templates)
                    session.save(update_fields=['extracted_templates_count'])
                
                result.update({
                    'processed': True,
                    'templates_found': len(extracted_templates),
                    'templates_extracted': [self._template_to_dict(t) for t in saved_templates]
                })
                
                # Trigger async processing for high-value templates
                self._trigger_async_processing(saved_templates)
                
            else:
                # Mark as processed even if no templates found
                message.extraction_processed = True
                message.save(update_fields=['extraction_processed'])
                result['processed'] = True
                
        except Exception as e:
            logger.error(f"Error processing chat message {message.id}: {e}")
            result['error'] = str(e)
            
        return result
    
    def _save_extracted_templates(
        self, 
        extracted_templates: List[ExtractedTemplateData], 
        source_message, 
        user
    ) -> List:
        """Save extracted templates to database"""
        saved_templates = []
        
        with transaction.atomic():
            for template_data in extracted_templates:
                try:
                    # Analyze monetization potential
                    monetization_analysis = self.analyzer.analyze_monetization_potential(template_data)
                    
                    # Create ExtractedTemplate record
                    extracted_template = ExtractedTemplate.objects.create(
                        source_message=source_message,
                        user=user,
                        title=template_data.title[:200],  # Ensure length limit
                        description=template_data.description,
                        template_content=template_data.template_content,
                        category_suggestion=template_data.category,
                        extraction_method=template_data.extraction_method,
                        confidence_score=template_data.confidence_score,
                        quality_rating=template_data.quality_rating,
                        langchain_analysis={
                            'keywords': template_data.keywords,
                            'use_cases': template_data.use_cases,
                            'monetization_analysis': monetization_analysis,
                            'metadata': template_data.metadata
                        },
                        keywords_extracted=template_data.keywords,
                        use_cases=template_data.use_cases,
                        status=self._determine_initial_status(template_data, monetization_analysis),
                        auto_approved=self._should_auto_approve(template_data, monetization_analysis)
                    )
                    
                    saved_templates.append(extracted_template)
                    logger.info(f"Saved extracted template: {extracted_template.title}")
                    
                except Exception as e:
                    logger.error(f"Error saving extracted template: {e}")
                    continue
        
        return saved_templates
    
    def _determine_initial_status(
        self, 
        template_data: ExtractedTemplateData, 
        monetization_analysis: Dict[str, Any]
    ) -> str:
        """Determine initial status for extracted template"""
        
        # Auto-approve high confidence, high quality templates
        if (template_data.confidence_score >= 0.9 and 
            template_data.quality_rating == 'high' and
            monetization_analysis['potential'] in ['high', 'medium']):
            return 'approved'
        
        # Auto-approve medium confidence templates with manual review
        if (template_data.confidence_score >= 0.7 and 
            template_data.quality_rating in ['high', 'medium']):
            return 'approved'
        
        # Everything else needs review
        return 'pending'
    
    def _should_auto_approve(
        self, 
        template_data: ExtractedTemplateData, 
        monetization_analysis: Dict[str, Any]
    ) -> bool:
        """Determine if template should be auto-approved"""
        return (
            template_data.confidence_score >= 0.85 and
            template_data.quality_rating == 'high' and
            monetization_analysis['potential'] in ['high', 'medium']
        )
    
    def _template_to_dict(self, template: 'ExtractedTemplate') -> Dict[str, Any]:
        """Convert ExtractedTemplate to dictionary"""
        return {
            'id': str(template.id),
            'title': template.title,
            'category': template.category_suggestion,
            'confidence_score': template.confidence_score,
            'quality_rating': template.quality_rating,
            'status': template.status,
            'auto_approved': template.auto_approved
        }
    
    def _trigger_async_processing(self, templates: List['ExtractedTemplate']):
        """Trigger async processing for templates"""
        for template in templates:
            if template.quality_rating == 'high' and template.confidence_score >= 0.8:
                # Trigger async publication to template library
                publish_template_to_library.delay(str(template.id))
    
    def publish_approved_template(self, extracted_template: 'ExtractedTemplate') -> Optional['Template']:
        """Publish an approved extracted template to the main template library"""
        
        if extracted_template.status != 'approved':
            logger.warning(f"Cannot publish template {extracted_template.id} - not approved")
            return None
        
        if extracted_template.published_template:
            logger.warning(f"Template {extracted_template.id} already published")
            return extracted_template.published_template
        
        try:
            with transaction.atomic():
                # Get or create category
                category = self._get_or_create_category(extracted_template.category_suggestion)
                
                # Create Template record
                template = Template.objects.create(
                    title=extracted_template.title,
                    description=extracted_template.description,
                    category=category,
                    template_content=extracted_template.template_content,
                    author=extracted_template.user,
                    is_ai_generated=True,
                    ai_confidence=extracted_template.confidence_score,
                    extracted_keywords=extracted_template.keywords_extracted,
                    tags=extracted_template.use_cases,
                    is_public=True,
                    is_active=True
                )
                
                # Link back to extracted template
                extracted_template.published_template = template
                extracted_template.save(update_fields=['published_template'])
                
                # Update user stats
                user = extracted_template.user
                user.templates_created += 1
                user.save(update_fields=['templates_created'])
                
                # Create monetization record if applicable
                self._create_monetization_record(template, extracted_template)
                
                logger.info(f"Published template {template.id} from extraction {extracted_template.id}")
                return template
                
        except Exception as e:
            logger.error(f"Error publishing template: {e}")
            return None
    
    def _get_or_create_category(self, category_name: str) -> 'TemplateCategory':
        """Get or create template category"""
        try:
            return TemplateCategory.objects.get(slug=category_name.lower().replace(' ', '-'))
        except TemplateCategory.DoesNotExist:
            return TemplateCategory.objects.create(
                name=category_name.title(),
                slug=category_name.lower().replace(' ', '-'),
                description=f"Templates related to {category_name}",
                is_active=True
            )
    
    def _create_monetization_record(self, template: 'Template', extracted_template: 'ExtractedTemplate'):
        """Create monetization record for high-value templates"""
        
        monetization_analysis = extracted_template.langchain_analysis.get('monetization_analysis', {})
        
        if monetization_analysis.get('potential') == 'high':
            # Create contribution bonus
            TemplateMonetization.objects.create(
                template=template,
                contributor=extracted_template.user,
                earning_type='contribution_bonus',
                amount=Decimal('5.00'),  # Base contribution bonus
                description=f"Contribution bonus for high-quality template: {template.title}",
                is_paid=False
            )
            
            # Quality bonus for exceptional templates
            if extracted_template.confidence_score >= 0.9 and extracted_template.quality_rating == 'high':
                TemplateMonetization.objects.create(
                    template=template,
                    contributor=extracted_template.user,
                    earning_type='quality_bonus',
                    amount=Decimal('10.00'),
                    description=f"Quality bonus for exceptional template: {template.title}",
                    is_paid=False
                )
    
    def get_user_template_stats(self, user) -> Dict[str, Any]:
        """Get user's template extraction and monetization stats"""
        
        extracted_templates = ExtractedTemplate.objects.filter(user=user)
        published_templates = Template.objects.filter(author=user, is_ai_generated=True)
        
        stats = {
            'total_extractions': extracted_templates.count(),
            'approved_extractions': extracted_templates.filter(status='approved').count(),
            'published_templates': published_templates.count(),
            'pending_review': extracted_templates.filter(status='pending').count(),
            'total_earnings': 0,
            'quality_breakdown': {
                'high': extracted_templates.filter(quality_rating='high').count(),
                'medium': extracted_templates.filter(quality_rating='medium').count(),
                'low': extracted_templates.filter(quality_rating='low').count(),
            },
            'category_breakdown': {},
            'recent_extractions': []
        }
        
        # Calculate earnings
        earnings = TemplateMonetization.objects.filter(contributor=user)
        stats['total_earnings'] = float(sum(e.amount for e in earnings))
        
        # Category breakdown
        categories = extracted_templates.values('category_suggestion').annotate(
            count=Count('id')
        ).order_by('-count')
        stats['category_breakdown'] = {cat['category_suggestion']: cat['count'] for cat in categories}
        
        # Recent extractions
        recent = extracted_templates.order_by('-created_at')[:5]
        stats['recent_extractions'] = [
            {
                'id': str(t.id),
                'title': t.title,
                'status': t.status,
                'quality_rating': t.quality_rating,
                'created_at': t.created_at.isoformat()
            }
            for t in recent
        ]
        
        return stats


# Celery tasks for async processing
@shared_task
def process_chat_message_templates(message_id: str):
    """Async task to process chat message for template extraction"""
    try:
        message = ChatMessage.objects.get(id=message_id)
        service = ChatTemplateIntegrationService()
        result = service.process_chat_message(message)
        logger.info(f"Processed message {message_id}: {result}")
        return result
    except ChatMessage.DoesNotExist:
        logger.error(f"Chat message {message_id} not found")
        return {'error': 'Message not found'}
    except Exception as e:
        logger.error(f"Error processing message {message_id}: {e}")
        return {'error': str(e)}


@shared_task
def publish_template_to_library(extracted_template_id: str):
    """Async task to publish approved template to library"""
    try:
        extracted_template = ExtractedTemplate.objects.get(id=extracted_template_id)
        service = ChatTemplateIntegrationService()
        template = service.publish_approved_template(extracted_template)
        
        if template:
            logger.info(f"Published template {template.id} from extraction {extracted_template_id}")
            return {'published': True, 'template_id': str(template.id)}
        else:
            return {'published': False, 'error': 'Failed to publish'}
            
    except ExtractedTemplate.DoesNotExist:
        logger.error(f"Extracted template {extracted_template_id} not found")
        return {'error': 'Extracted template not found'}
    except Exception as e:
        logger.error(f"Error publishing template {extracted_template_id}: {e}")
        return {'error': str(e)}


@shared_task
def batch_process_chat_history(user_id: str, days_back: int = 7):
    """Batch process chat history for template extraction"""
    try:
        user = User.objects.get(id=user_id)
        since_date = timezone.now() - timedelta(days=days_back)
        
        # Get unprocessed messages
        messages = ChatMessage.objects.filter(
            session__user=user,
            role='assistant',
            extraction_processed=False,
            created_at__gte=since_date
        ).order_by('created_at')
        
        service = ChatTemplateIntegrationService()
        processed_count = 0
        templates_found = 0
        
        for message in messages:
            result = service.process_chat_message(message)
            if result['processed']:
                processed_count += 1
                templates_found += result['templates_found']
        
        logger.info(f"Batch processed {processed_count} messages for user {user_id}, found {templates_found} templates")
        
        return {
            'processed_messages': processed_count,
            'templates_found': templates_found,
            'user_id': user_id
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error batch processing for user {user_id}: {e}")
        return {'error': str(e)}


# Initialize service
chat_template_service = ChatTemplateIntegrationService()