# tasks/template_tasks.py
"""
Background tasks for template extraction and processing
"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

try:
    from apps.chat.models import ChatMessage, ExtractedTemplate, ChatSession
    from chat_template_service import chat_template_service
    from monetization_services import monetization_service
    from django_models import Template, TemplateCategory
except ImportError:
    # Handle import errors gracefully
    pass

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def process_pending_extractions(self):
    """Process pending template extractions"""
    try:
        # Find messages that need template extraction
        pending_messages = ChatMessage.objects.filter(
            role='assistant',
            extraction_processed=False,
            created_at__gte=timezone.now() - timedelta(hours=24)  # Last 24 hours
        ).order_by('created_at')[:50]  # Process 50 at a time
        
        processed_count = 0
        extracted_count = 0
        
        for message in pending_messages:
            try:
                result = chat_template_service.process_chat_message(message)
                if result['processed']:
                    processed_count += 1
                    extracted_count += result['templates_found']
                    
                    logger.info(f"Processed message {message.id}: {result['templates_found']} templates found")
                    
            except Exception as e:
                logger.error(f"Error processing message {message.id}: {e}")
                continue
        
        logger.info(f"Batch processing completed: {processed_count} messages, {extracted_count} templates extracted")
        
        return {
            'processed_messages': processed_count,
            'templates_extracted': extracted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in process_pending_extractions: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True, max_retries=3)
def auto_approve_high_quality_templates(self):
    """Auto-approve high-quality extracted templates"""
    try:
        # Find high-quality pending templates
        high_quality_templates = ExtractedTemplate.objects.filter(
            status='pending',
            quality_rating='high',
            confidence_score__gte=0.85,
            created_at__gte=timezone.now() - timedelta(hours=6)  # Recent extractions
        )
        
        approved_count = 0
        published_count = 0
        
        for template in high_quality_templates:
            try:
                # Auto-approve
                template.status = 'approved'
                template.auto_approved = True
                template.reviewed_at = timezone.now()
                template.save()
                
                approved_count += 1
                
                # Try to publish to library
                if chat_template_service:
                    published_template = chat_template_service.publish_approved_template(template)
                    if published_template:
                        published_count += 1
                        
                        # Process monetization rewards
                        if monetization_service:
                            rewards = monetization_service.process_template_extraction_reward(template)
                            logger.info(f"Processed rewards for template {template.id}: {rewards}")
                
                logger.info(f"Auto-approved and published template: {template.title}")
                
            except Exception as e:
                logger.error(f"Error auto-approving template {template.id}: {e}")
                continue
        
        return {
            'approved_count': approved_count,
            'published_count': published_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in auto_approve_high_quality_templates: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task(bind=True)
def batch_extract_from_chat_history(self, user_id: str = None, days_back: int = 7):
    """Batch extract templates from chat history"""
    try:
        if user_id:
            users = [User.objects.get(id=user_id)]
        else:
            # Process active users from last 30 days
            since_date = timezone.now() - timedelta(days=30)
            users = User.objects.filter(
                chat_sessions__created_at__gte=since_date
            ).distinct()[:20]  # Process 20 users at a time
        
        total_processed = 0
        total_extracted = 0
        
        for user in users:
            try:
                # Get unprocessed messages for this user
                since_date = timezone.now() - timedelta(days=days_back)
                messages = ChatMessage.objects.filter(
                    session__user=user,
                    role='assistant',
                    extraction_processed=False,
                    created_at__gte=since_date
                ).order_by('created_at')
                
                user_processed = 0
                user_extracted = 0
                
                for message in messages:
                    try:
                        result = chat_template_service.process_chat_message(message)
                        if result['processed']:
                            user_processed += 1
                            user_extracted += result['templates_found']
                            
                    except Exception as e:
                        logger.error(f"Error processing message {message.id} for user {user.id}: {e}")
                        continue
                
                total_processed += user_processed
                total_extracted += user_extracted
                
                logger.info(f"Processed {user_processed} messages for user {user.username}, extracted {user_extracted} templates")
                
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {e}")
                continue
        
        return {
            'users_processed': len(users),
            'total_messages_processed': total_processed,
            'total_templates_extracted': total_extracted,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch_extract_from_chat_history: {e}")
        raise


@shared_task(bind=True)
def cleanup_low_quality_extractions(self):
    """Clean up low-quality extracted templates"""
    try:
        # Find old, low-quality extractions that weren't approved
        cutoff_date = timezone.now() - timedelta(days=7)
        
        low_quality_templates = ExtractedTemplate.objects.filter(
            status='pending',
            quality_rating='low',
            confidence_score__lt=0.5,
            created_at__lt=cutoff_date
        )
        
        deleted_count = low_quality_templates.count()
        low_quality_templates.delete()
        
        logger.info(f"Cleaned up {deleted_count} low-quality extracted templates")
        
        return {
            'deleted_count': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_low_quality_extractions: {e}")
        raise


@shared_task(bind=True)
def generate_template_collections(self):
    """Generate curated template collections from extracted templates"""
    try:
        # Find high-quality approved templates
        high_quality_templates = ExtractedTemplate.objects.filter(
            status='approved',
            quality_rating='high',
            published_template__isnull=False
        ).select_related('published_template')
        
        # Group by category
        category_groups = {}
        for extracted in high_quality_templates:
            category = extracted.category_suggestion
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(extracted.published_template)
        
        collections_created = 0
        
        # Create collections for categories with enough templates
        for category, templates in category_groups.items():
            if len(templates) >= 10:  # Minimum 10 templates for a collection
                try:
                    from monetization_services import bundle_service
                    
                    # Create a curated bundle
                    admin_user = User.objects.filter(is_superuser=True).first()
                    if admin_user:
                        bundle = bundle_service.create_curated_collection(
                            templates[:20],  # Max 20 templates per collection
                            f"Best {category.title()} Templates",
                            f"Curated collection of {len(templates[:20])} high-quality {category} templates",
                            admin_user
                        )
                        collections_created += 1
                        logger.info(f"Created collection: {bundle.title}")
                        
                except Exception as e:
                    logger.error(f"Error creating collection for {category}: {e}")
                    continue
        
        return {
            'collections_created': collections_created,
            'categories_processed': len(category_groups),
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in generate_template_collections: {e}")
        raise


@shared_task(bind=True)
def update_template_popularity_scores(self):
    """Update popularity scores for templates based on usage"""
    try:
        from django.db.models import Count, Avg
        
        # Get templates with usage data
        templates = Template.objects.filter(is_active=True).annotate(
            usage_count=Count('usage_logs'),
            avg_rating=Avg('ratings__rating')
        )
        
        updated_count = 0
        
        for template in templates:
            try:
                # Calculate popularity score based on multiple factors
                usage_score = min(template.usage_count / 10, 10)  # Max 10 points for usage
                rating_score = (template.avg_rating or 3) * 2  # Max 10 points for rating
                recency_score = self._calculate_recency_score(template)
                
                popularity_score = (usage_score + rating_score + recency_score) / 3
                
                if abs(template.popularity_score - popularity_score) > 0.1:
                    template.popularity_score = popularity_score
                    template.save(update_fields=['popularity_score'])
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating popularity for template {template.id}: {e}")
                continue
        
        logger.info(f"Updated popularity scores for {updated_count} templates")
        
        return {
            'updated_count': updated_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in update_template_popularity_scores: {e}")
        raise


def _calculate_recency_score(template):
    """Calculate recency score for template popularity"""
    days_since_creation = (timezone.now() - template.created_at).days
    
    if days_since_creation <= 7:
        return 10  # Very recent
    elif days_since_creation <= 30:
        return 7   # Recent
    elif days_since_creation <= 90:
        return 5   # Moderately recent
    else:
        return 2   # Older content


@shared_task(bind=True)
def sync_extracted_templates_to_library(self):
    """Sync approved extracted templates to the main template library"""
    try:
        # Find approved templates that haven't been published yet
        unpublished = ExtractedTemplate.objects.filter(
            status='approved',
            published_template__isnull=True
        ).select_related('user')
        
        published_count = 0
        error_count = 0
        
        for extracted_template in unpublished:
            try:
                published = chat_template_service.publish_approved_template(extracted_template)
                if published:
                    published_count += 1
                    
                    # Process monetization rewards
                    if monetization_service:
                        rewards = monetization_service.process_template_extraction_reward(extracted_template)
                        logger.info(f"Processed rewards for {extracted_template.id}: {rewards}")
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error publishing extracted template {extracted_template.id}: {e}")
                error_count += 1
                continue
        
        return {
            'published_count': published_count,
            'error_count': error_count,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in sync_extracted_templates_to_library: {e}")
        raise