"""
AI-Powered Suggestion Service for Intelligent Prompt Recommendations
Provides personalized template suggestions based on user behavior, preferences, and context
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, F
from django.contrib.auth import get_user_model

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.utils import timezone
from apps.templates.models import Template, TemplateUsage, TemplateRating, TemplateCategory
from apps.analytics.models import AnalyticsEvent

User = get_user_model()
logger = logging.getLogger(__name__)


class UserBehaviorAnalyzer:
    """Analyze user behavior patterns for personalized recommendations"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour cache for user profiles
    
    def get_user_profile(self, user: User) -> Dict[str, Any]:
        """Generate comprehensive user behavior profile"""
        cache_key = f"user_profile_{user.id}"
        profile = cache.get(cache_key)
        
        if profile is None:
            profile = self._build_user_profile(user)
            cache.set(cache_key, profile, self.cache_timeout)
        
        return profile
    
    def _build_user_profile(self, user: User) -> Dict[str, Any]:
        """Build detailed user behavior profile"""
        
        # Get user's template usage history
        usage_history = TemplateUsage.objects.filter(user=user).select_related('template__category')
        
        # Analyze category preferences
        category_preferences = self._analyze_category_preferences(usage_history)
        
        # Analyze completion patterns
        completion_patterns = self._analyze_completion_patterns(usage_history)
        
        # Analyze time patterns
        time_patterns = self._analyze_time_patterns(usage_history)
        
        # Analyze rating patterns
        rating_patterns = self._analyze_rating_patterns(user)
        
        # Get user's skill level and experience
        user_experience = self._calculate_user_experience(user, usage_history)
        
        # Analyze search and browse patterns
        browse_patterns = self._analyze_browse_patterns(user)
        
        return {
            'user_id': user.id,
            'category_preferences': category_preferences,
            'completion_patterns': completion_patterns,
            'time_patterns': time_patterns,
            'rating_patterns': rating_patterns,
            'experience_level': user_experience,
            'browse_patterns': browse_patterns,
            'last_updated': timezone.now().isoformat(),
        }
    
    def _analyze_category_preferences(self, usage_history) -> Dict[str, float]:
        """Analyze user's category preferences based on usage"""
        category_counts = {}
        total_usage = usage_history.count()
        
        if total_usage == 0:
            return {}
        
        # Count usage by category
        for usage in usage_history:
            category = usage.template.category.name
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Calculate preferences as percentages
        preferences = {}
        for category, count in category_counts.items():
            preferences[category] = count / total_usage
        
        # Add completion rate weighting
        for usage in usage_history.filter(was_completed=True):
            category = usage.template.category.name
            if category in preferences:
                preferences[category] *= 1.2  # Boost completed categories
        
        return preferences
    
    def _analyze_completion_patterns(self, usage_history) -> Dict[str, Any]:
        """Analyze user's template completion patterns"""
        completed_count = usage_history.filter(was_completed=True).count()
        total_count = usage_history.count()
        
        if total_count == 0:
            return {'completion_rate': 0, 'avg_completion_time': 0, 'preferred_complexity': 'simple'}
        
        completion_rate = completed_count / total_count
        
        # Calculate average completion time
        completed_usages = usage_history.filter(was_completed=True, time_spent_seconds__isnull=False)
        avg_completion_time = 0
        if completed_usages.exists():
            total_time = sum(usage.time_spent_seconds for usage in completed_usages)
            avg_completion_time = total_time / completed_usages.count()
        
        # Determine preferred complexity based on completion patterns
        preferred_complexity = self._determine_preferred_complexity(usage_history)
        
        return {
            'completion_rate': completion_rate,
            'avg_completion_time': avg_completion_time,
            'preferred_complexity': preferred_complexity,
            'total_completions': completed_count,
        }
    
    def _analyze_time_patterns(self, usage_history) -> Dict[str, Any]:
        """Analyze when user typically uses templates"""
        if not usage_history.exists():
            return {}
        
        # Analyze by hour of day
        hour_counts = {}
        for usage in usage_history:
            hour = usage.started_at.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
        
        # Find peak usage hours
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyze by day of week
        day_counts = {}
        for usage in usage_history:
            day = usage.started_at.weekday()  # 0=Monday, 6=Sunday
            day_counts[day] = day_counts.get(day, 0) + 1
        
        return {
            'peak_hours': [hour for hour, _ in peak_hours],
            'day_distribution': day_counts,
            'most_active_day': max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None,
        }
    
    def _analyze_rating_patterns(self, user: User) -> Dict[str, Any]:
        """Analyze user's rating patterns"""
        ratings = TemplateRating.objects.filter(user=user)
        
        if not ratings.exists():
            return {}
        
        avg_rating = ratings.aggregate(avg=Avg('rating'))['avg']
        rating_distribution = {}
        
        for rating in ratings:
            star = rating.rating
            rating_distribution[star] = rating_distribution.get(star, 0) + 1
        
        # Calculate rating tendency (generous vs critical)
        total_ratings = ratings.count()
        high_ratings = ratings.filter(rating__gte=4).count()
        rating_tendency = 'generous' if (high_ratings / total_ratings) > 0.7 else 'balanced'
        if (high_ratings / total_ratings) < 0.3:
            rating_tendency = 'critical'
        
        return {
            'average_rating': avg_rating,
            'rating_distribution': rating_distribution,
            'rating_tendency': rating_tendency,
            'total_ratings': total_ratings,
        }
    
    def _calculate_user_experience(self, user: User, usage_history) -> Dict[str, Any]:
        """Calculate user's experience level and expertise"""
        
        # Basic metrics
        total_templates_used = usage_history.count()
        completed_templates = usage_history.filter(was_completed=True).count()
        days_since_signup = (timezone.now() - user.date_joined).days
        
        # Calculate experience score
        experience_score = 0
        experience_score += min(total_templates_used * 2, 100)  # Max 100 from usage
        experience_score += min(completed_templates * 5, 150)   # Max 150 from completions
        experience_score += min(days_since_signup * 0.5, 50)   # Max 50 from tenure
        
        # Determine experience level
        if experience_score < 50:
            level = 'beginner'
        elif experience_score < 150:
            level = 'intermediate'
        elif experience_score < 250:
            level = 'advanced'
        else:
            level = 'expert'
        
        # Calculate domain expertise
        domain_expertise = self._calculate_domain_expertise(usage_history)
        
        return {
            'level': level,
            'score': experience_score,
            'templates_used': total_templates_used,
            'completions': completed_templates,
            'domain_expertise': domain_expertise,
        }
    
    def _calculate_domain_expertise(self, usage_history) -> Dict[str, str]:
        """Calculate expertise in different domains/categories"""
        category_expertise = {}
        
        # Group by category
        category_usage = {}
        for usage in usage_history:
            category = usage.template.category.name
            if category not in category_usage:
                category_usage[category] = {'total': 0, 'completed': 0}
            
            category_usage[category]['total'] += 1
            if usage.was_completed:
                category_usage[category]['completed'] += 1
        
        # Calculate expertise level for each category
        for category, stats in category_usage.items():
            total = stats['total']
            completed = stats['completed']
            
            if total >= 20 and completed >= 15:
                expertise = 'expert'
            elif total >= 10 and completed >= 7:
                expertise = 'advanced'
            elif total >= 5 and completed >= 3:
                expertise = 'intermediate'
            else:
                expertise = 'beginner'
            
            category_expertise[category] = expertise
        
        return category_expertise
    
    def _analyze_browse_patterns(self, user: User) -> Dict[str, Any]:
        """Analyze user's browsing and search patterns"""
        
        # Get analytics events for this user
        events = AnalyticsEvent.objects.filter(
            user=user,
            event_name__in=['template_view', 'template_search', 'category_browse']
        ).order_by('-created_at')[:100]  # Last 100 events
        
        if not events.exists():
            return {}
        
        # Analyze search patterns
        search_events = events.filter(event_name='template_search')
        search_terms = []
        for event in search_events:
            if 'search_term' in event.properties:
                search_terms.append(event.properties['search_term'])
        
        # Analyze browse patterns
        browse_events = events.filter(event_name='category_browse')
        browsed_categories = []
        for event in browse_events:
            if 'category' in event.properties:
                browsed_categories.append(event.properties['category'])
        
        return {
            'recent_searches': search_terms[:10],
            'browsed_categories': list(set(browsed_categories)),
            'search_frequency': search_events.count(),
            'browse_frequency': browse_events.count(),
        }
    
    def _determine_preferred_complexity(self, usage_history) -> str:
        """Determine user's preferred template complexity"""
        if not usage_history.exists():
            return 'simple'
        
        # Analyze field count patterns from completed templates
        completed_usages = usage_history.filter(was_completed=True)
        
        if not completed_usages.exists():
            return 'simple'
        
        field_counts = []
        for usage in completed_usages:
            field_count = usage.template.field_count
            field_counts.append(field_count)
        
        avg_field_count = sum(field_counts) / len(field_counts)
        
        if avg_field_count <= 3:
            return 'simple'
        elif avg_field_count <= 7:
            return 'medium'
        else:
            return 'complex'


class TemplateRecommendationEngine:
    """Generate intelligent template recommendations"""
    
    def __init__(self):
        self.behavior_analyzer = UserBehaviorAnalyzer()
        self.cache_timeout = 1800  # 30 minutes cache for recommendations
    
    def get_personalized_recommendations(
        self, 
        user: User, 
        limit: int = 10,
        exclude_used: bool = True,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get personalized template recommendations for user"""
        
        cache_key = f"recommendations_{user.id}_{limit}_{exclude_used}_{category_filter}"
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            recommendations = self._generate_recommendations(
                user, limit, exclude_used, category_filter
            )
            cache.set(cache_key, recommendations, self.cache_timeout)
        
        return recommendations
    
    def _generate_recommendations(
        self, 
        user: User, 
        limit: int,
        exclude_used: bool,
        category_filter: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations using multiple strategies"""
        
        # Get user profile
        user_profile = self.behavior_analyzer.get_user_profile(user)
        
        # Start with all active, public templates
        queryset = Template.objects.filter(
            is_active=True,
            is_public=True
        ).select_related('category', 'author')
        
        # Apply category filter if specified
        if category_filter:
            queryset = queryset.filter(category__slug=category_filter)
        
        # Exclude templates user has already used
        if exclude_used:
            used_template_ids = TemplateUsage.objects.filter(
                user=user
            ).values_list('template_id', flat=True)
            queryset = queryset.exclude(id__in=used_template_ids)
        
        # Apply multiple recommendation strategies
        recommendations = []
        
        # Strategy 1: Category-based recommendations (40% weight)
        category_recs = self._get_category_based_recommendations(
            queryset, user_profile, limit // 2
        )
        recommendations.extend(category_recs)
        
        # Strategy 2: Popularity-based recommendations (30% weight)
        popularity_recs = self._get_popularity_based_recommendations(
            queryset, user_profile, limit // 3
        )
        recommendations.extend(popularity_recs)
        
        # Strategy 3: Collaborative filtering (20% weight)
        collaborative_recs = self._get_collaborative_recommendations(
            queryset, user, limit // 4
        )
        recommendations.extend(collaborative_recs)
        
        # Strategy 4: Content-based recommendations (10% weight)
        content_recs = self._get_content_based_recommendations(
            queryset, user_profile, limit // 5
        )
        recommendations.extend(content_recs)
        
        # Deduplicate and score
        unique_recommendations = self._deduplicate_and_score(recommendations)
        
        # Sort by final score and return top results
        final_recommendations = sorted(
            unique_recommendations, 
            key=lambda x: x['score'], 
            reverse=True
        )[:limit]
        
        # Add explanation and metadata
        for rec in final_recommendations:
            rec['explanation'] = self._generate_explanation(rec, user_profile)
            rec['estimated_completion_time'] = self._estimate_completion_time(
                rec['template'], user_profile
            )
        
        return final_recommendations
    
    def _get_category_based_recommendations(
        self, 
        queryset, 
        user_profile: Dict[str, Any], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on user's category preferences"""
        
        recommendations = []
        category_preferences = user_profile.get('category_preferences', {})
        
        if not category_preferences:
            # New user - recommend popular templates from each category
            categories = TemplateCategory.objects.filter(is_active=True)[:5]
            for category in categories:
                templates = queryset.filter(category=category).order_by('-popularity_score')[:2]
                for template in templates:
                    recommendations.append({
                        'template': template,
                        'score': 0.6,  # Base score for new users
                        'strategy': 'category_exploration',
                        'confidence': 0.5,
                    })
        else:
            # Existing user - use preferences
            for category_name, preference_score in category_preferences.items():
                try:
                    category = TemplateCategory.objects.get(name=category_name)
                    templates = queryset.filter(category=category).order_by('-popularity_score')[:3]
                    
                    for template in templates:
                        score = preference_score * 0.8 + template.popularity_score * 0.2
                        recommendations.append({
                            'template': template,
                            'score': score,
                            'strategy': 'category_preference',
                            'confidence': preference_score,
                        })
                except TemplateCategory.DoesNotExist:
                    continue
        
        return recommendations[:limit]
    
    def _get_popularity_based_recommendations(
        self, 
        queryset, 
        user_profile: Dict[str, Any], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on overall popularity"""
        
        # Adjust popularity based on user experience
        experience_level = user_profile.get('experience_level', {}).get('level', 'beginner')
        
        if experience_level == 'beginner':
            # Recommend highly-rated, simple templates
            templates = queryset.filter(
                average_rating__gte=4.0
            ).annotate(
                field_count=Count('fields')
            ).filter(field_count__lte=5).order_by('-popularity_score')[:limit]
        else:
            # Recommend trending and featured templates
            templates = queryset.filter(
                Q(is_featured=True) | Q(popularity_score__gte=70)
            ).order_by('-popularity_score', '-average_rating')[:limit]
        
        recommendations = []
        for template in templates:
            score = (template.popularity_score / 100) * 0.7 + (template.average_rating / 5) * 0.3
            recommendations.append({
                'template': template,
                'score': score,
                'strategy': 'popularity',
                'confidence': 0.8,
            })
        
        return recommendations
    
    def _get_collaborative_recommendations(
        self, 
        queryset, 
        user: User, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on similar users' behavior"""
        
        # Find users with similar preferences
        similar_users = self._find_similar_users(user)
        
        if not similar_users:
            return []
        
        # Get templates highly rated by similar users
        similar_user_ids = [u.id for u in similar_users]
        
        highly_rated_templates = Template.objects.filter(
            ratings__user_id__in=similar_user_ids,
            ratings__rating__gte=4
        ).annotate(
            similar_user_rating_avg=Avg('ratings__rating')
        ).filter(
            id__in=queryset.values_list('id', flat=True)
        ).order_by('-similar_user_rating_avg')[:limit]
        
        recommendations = []
        for template in highly_rated_templates:
            score = template.similar_user_rating_avg / 5 * 0.9
            recommendations.append({
                'template': template,
                'score': score,
                'strategy': 'collaborative',
                'confidence': 0.7,
            })
        
        return recommendations
    
    def _get_content_based_recommendations(
        self, 
        queryset, 
        user_profile: Dict[str, Any], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on content similarity"""
        
        recommendations = []
        browse_patterns = user_profile.get('browse_patterns', {})
        recent_searches = browse_patterns.get('recent_searches', [])
        
        if recent_searches:
            # Find templates matching recent search terms
            search_query = Q()
            for term in recent_searches[:5]:  # Use last 5 searches
                search_query |= Q(title__icontains=term) | Q(description__icontains=term)
            
            matching_templates = queryset.filter(search_query).order_by('-popularity_score')[:limit]
            
            for template in matching_templates:
                score = 0.6 + (template.popularity_score / 100) * 0.4
                recommendations.append({
                    'template': template,
                    'score': score,
                    'strategy': 'content_search',
                    'confidence': 0.6,
                })
        
        return recommendations
    
    def _find_similar_users(self, user: User, limit: int = 10) -> List[User]:
        """Find users with similar behavior patterns"""
        
        # Get user's categories and ratings
        user_categories = set(
            TemplateUsage.objects.filter(user=user).values_list(
                'template__category__name', flat=True
            )
        )
        
        user_ratings = dict(
            TemplateRating.objects.filter(user=user).values_list(
                'template_id', 'rating'
            )
        )
        
        if not user_categories:
            return []
        
        # Find users who used similar categories
        similar_users = User.objects.filter(
            template_usages__template__category__name__in=user_categories
        ).exclude(id=user.id).annotate(
            shared_categories=Count('template_usages__template__category', distinct=True)
        ).filter(shared_categories__gte=2).order_by('-shared_categories')[:limit]
        
        return list(similar_users)
    
    def _deduplicate_and_score(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and calculate final scores"""
        
        template_scores = {}
        
        for rec in recommendations:
            template_id = rec['template'].id
            
            if template_id not in template_scores:
                template_scores[template_id] = {
                    'template': rec['template'],
                    'strategies': [],
                    'total_score': 0,
                    'confidence': 0,
                }
            
            template_scores[template_id]['strategies'].append(rec['strategy'])
            template_scores[template_id]['total_score'] += rec['score']
            template_scores[template_id]['confidence'] = max(
                template_scores[template_id]['confidence'],
                rec['confidence']
            )
        
        # Calculate final scores
        final_recommendations = []
        for template_id, data in template_scores.items():
            # Average score with bonus for multiple strategies
            strategy_count = len(data['strategies'])
            final_score = data['total_score'] / strategy_count
            
            if strategy_count > 1:
                final_score *= 1.1  # 10% bonus for multiple strategies
            
            final_recommendations.append({
                'template': data['template'],
                'score': final_score,
                'strategies': data['strategies'],
                'confidence': data['confidence'],
            })
        
        return final_recommendations
    
    def _generate_explanation(self, recommendation: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Generate human-readable explanation for recommendation"""
        
        template = recommendation['template']
        strategies = recommendation['strategies']
        
        explanations = []
        
        if 'category_preference' in strategies:
            category = template.category.name
            explanations.append(f"You frequently use {category} templates")
        
        if 'popularity' in strategies:
            explanations.append("Highly popular and well-rated")
        
        if 'collaborative' in strategies:
            explanations.append("Recommended by users with similar interests")
        
        if 'content_search' in strategies:
            explanations.append("Matches your recent searches")
        
        if 'category_exploration' in strategies:
            explanations.append("Popular template to help you explore new categories")
        
        if not explanations:
            explanations = ["Recommended for you"]
        
        return " • ".join(explanations)
    
    def _estimate_completion_time(self, template: Template, user_profile: Dict[str, Any]) -> int:
        """Estimate completion time in minutes"""
        
        base_time = template.field_count * 2  # 2 minutes per field baseline
        
        # Adjust based on user experience
        experience_level = user_profile.get('experience_level', {}).get('level', 'beginner')
        
        if experience_level == 'expert':
            base_time *= 0.7
        elif experience_level == 'advanced':
            base_time *= 0.8
        elif experience_level == 'intermediate':
            base_time *= 0.9
        # beginner uses full time
        
        # Adjust based on template complexity
        if template.field_count > 10:
            base_time *= 1.3
        elif template.field_count > 7:
            base_time *= 1.1
        
        return max(int(base_time), 1)  # Minimum 1 minute


class SuggestionAPIService:
    """Service for providing suggestions through API endpoints"""
    
    def __init__(self):
        self.recommendation_engine = TemplateRecommendationEngine()
    
    def get_home_suggestions(self, user: User, limit: int = 6) -> Dict[str, Any]:
        """Get suggestions for home page"""
        
        if user.is_authenticated:
            recommendations = self.recommendation_engine.get_personalized_recommendations(
                user, limit=limit
            )
        else:
            # Anonymous user - show popular templates
            recommendations = self._get_popular_templates(limit)
        
        return {
            'recommendations': [
                {
                    'id': str(rec['template'].id),
                    'title': rec['template'].title,
                    'description': rec['template'].description,
                    'category': rec['template'].category.name,
                    'rating': rec['template'].average_rating,
                    'usage_count': rec['template'].usage_count,
                    'field_count': rec['template'].field_count,
                    'estimated_time': rec.get('estimated_completion_time', 5),
                    'explanation': rec.get('explanation', ''),
                    'confidence': rec.get('confidence', 0.5),
                }
                for rec in recommendations
            ],
            'personalized': user.is_authenticated,
        }
    
    def get_category_suggestions(self, user: User, category_slug: str, limit: int = 10) -> Dict[str, Any]:
        """Get suggestions for specific category"""
        
        if user.is_authenticated:
            recommendations = self.recommendation_engine.get_personalized_recommendations(
                user, limit=limit, category_filter=category_slug
            )
        else:
            # Anonymous user
            recommendations = self._get_category_popular_templates(category_slug, limit)
        
        return {
            'recommendations': [
                {
                    'id': str(rec['template'].id),
                    'title': rec['template'].title,
                    'description': rec['template'].description,
                    'rating': rec['template'].average_rating,
                    'usage_count': rec['template'].usage_count,
                    'field_count': rec['template'].field_count,
                    'estimated_time': rec.get('estimated_completion_time', 5),
                }
                for rec in recommendations
            ],
            'category': category_slug,
        }
    
    def get_similar_templates(self, template_id: str, user: User = None, limit: int = 5) -> Dict[str, Any]:
        """Get templates similar to a specific template"""
        
        try:
            template = Template.objects.get(id=template_id)
        except Template.DoesNotExist:
            return {'recommendations': []}
        
        # Find similar templates by category and tags
        similar_templates = Template.objects.filter(
            category=template.category,
            is_active=True,
            is_public=True
        ).exclude(id=template_id)
        
        # If template has tags, prioritize by tag similarity
        if template.tags:
            tag_matches = similar_templates.filter(
                tags__overlap=template.tags
            ).order_by('-popularity_score')
            
            other_templates = similar_templates.exclude(
                id__in=tag_matches.values_list('id', flat=True)
            ).order_by('-popularity_score')
            
            # Combine with tag matches first
            final_similar = list(tag_matches[:limit//2]) + list(other_templates[:limit//2])
        else:
            final_similar = similar_templates.order_by('-popularity_score')[:limit]
        
        return {
            'recommendations': [
                {
                    'id': str(t.id),
                    'title': t.title,
                    'description': t.description,
                    'rating': t.average_rating,
                    'usage_count': t.usage_count,
                    'field_count': t.field_count,
                }
                for t in final_similar
            ],
            'base_template': template_id,
        }
    
    def _get_popular_templates(self, limit: int) -> List[Dict[str, Any]]:
        """Get popular templates for anonymous users"""
        
        templates = Template.objects.filter(
            is_active=True,
            is_public=True,
            popularity_score__gte=50
        ).order_by('-popularity_score', '-average_rating')[:limit]
        
        return [
            {
                'template': template,
                'score': template.popularity_score / 100,
                'strategies': ['popularity'],
                'confidence': 0.8,
                'explanation': 'Popular template',
                'estimated_completion_time': template.field_count * 2,
            }
            for template in templates
        ]
    
    def _get_category_popular_templates(self, category_slug: str, limit: int) -> List[Dict[str, Any]]:
        """Get popular templates in specific category for anonymous users"""
        
        try:
            category = TemplateCategory.objects.get(slug=category_slug)
            templates = Template.objects.filter(
                category=category,
                is_active=True,
                is_public=True
            ).order_by('-popularity_score', '-average_rating')[:limit]
            
            return [
                {
                    'template': template,
                    'score': template.popularity_score / 100,
                    'strategies': ['category_popular'],
                    'confidence': 0.7,
                    'explanation': f'Popular in {category.name}',
                    'estimated_completion_time': template.field_count * 2,
                }
                for template in templates
            ]
        except TemplateCategory.DoesNotExist:
            return []