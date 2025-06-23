"""
Utility functions for the PromptCraft application.
These utilities help with common tasks across the application.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from django.conf import settings
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)

class TemplateUtilities:
    """Utilities for working with templates"""
    
    @staticmethod
    def extract_variables_from_template(template_content: str) -> List[str]:
        """
        Extract variable placeholders from a template content
        Variable format: {variable_name}
        
        Returns a list of variable names without braces
        """
        import re
        pattern = r'\{([a-zA-Z0-9_]+)\}'
        variables = re.findall(pattern, template_content)
        return list(set(variables))  # Remove duplicates
    
    @staticmethod
    def render_template(template_content: str, variables: Dict[str, Any]) -> str:
        """
        Render a template by replacing variables with their values
        
        Args:
            template_content: The template text with {variable} placeholders
            variables: Dictionary of variable names and values
            
        Returns:
            Rendered template with variables replaced
        """
        result = template_content
        for name, value in variables.items():
            result = result.replace(f"{{{name}}}", str(value))
        return result
    
    @staticmethod
    def validate_template_structure(template_data: Dict) -> List[str]:
        """
        Validate template structure and return any errors
        
        Returns:
            List of error messages, empty if valid
        """
        errors = []
        
        # Required fields
        required_fields = ['title', 'template_content']
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Check content length
        if 'template_content' in template_data:
            if len(template_data['template_content']) < 10:
                errors.append("Template content is too short (minimum 10 characters)")
            elif len(template_data['template_content']) > 10000:
                errors.append("Template content is too long (maximum 10000 characters)")
        
        # Check field definitions match variables in content
        if 'template_content' in template_data and 'fields' in template_data:
            content_variables = TemplateUtilities.extract_variables_from_template(
                template_data['template_content']
            )
            field_variables = [field.get('name') for field in template_data['fields']]
            
            # Check for variables in content that aren't defined as fields
            for var in content_variables:
                if var not in field_variables:
                    errors.append(f"Variable {{{var}}} used in content but not defined as a field")
            
            # Check for fields that aren't used in content
            for field in field_variables:
                if field not in content_variables:
                    errors.append(f"Field '{field}' is defined but not used in template content")
        
        return errors


class AIUtilities:
    """Utilities for working with AI services"""
    
    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        """
        Sanitize a prompt for safe AI processing
        
        Args:
            prompt: The user prompt
            
        Returns:
            Sanitized prompt
        """
        # Basic sanitization
        sanitized = prompt.strip()
        
        # Remove potential injection patterns
        injection_patterns = [
            "ignore previous instructions",
            "ignore above instructions",
            "disregard previous"
        ]
        
        for pattern in injection_patterns:
            if pattern.lower() in sanitized.lower():
                logger.warning(f"Potential prompt injection detected: {pattern}")
                sanitized = sanitized.replace(pattern, "")
        
        return sanitized
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate the number of tokens in a text
        
        This is a simplified estimation. For accurate counts,
        use the tokenizer from the specific AI provider.
        
        Args:
            text: The text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Simple estimation - approximately 4 chars per token
        return max(1, len(text) // 4)
    
    @staticmethod
    def format_prompt_with_system_message(
        user_prompt: str, system_message: str = None
    ) -> Dict:
        """
        Format a prompt with system message for AI services
        
        Args:
            user_prompt: The user's prompt text
            system_message: Optional system message/instructions
            
        Returns:
            Formatted messages dictionary
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        return messages
    
    @staticmethod
    def parse_json_from_response(response_text: str) -> Dict:
        """
        Extract and parse JSON from AI response text
        
        Args:
            response_text: The AI response text potentially containing JSON
            
        Returns:
            Parsed JSON as dictionary or empty dict if parsing fails
        """
        try:
            # Try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response text
            import re
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            matches = re.findall(json_pattern, response_text)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
                    
            # Try with different pattern
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, response_text)
            
            if matches:
                try:
                    return json.loads(matches[0])
                except json.JSONDecodeError:
                    pass
            
            logger.warning("Failed to parse JSON from response")
            return {}


class AnalyticsUtilities:
    """Utilities for analytics"""
    
    @staticmethod
    def get_date_range(range_type: str = 'week') -> tuple:
        """
        Get start and end dates for analytics queries
        
        Args:
            range_type: 'day', 'week', 'month', 'quarter', 'year'
            
        Returns:
            Tuple of (start_date, end_date) as timezone-aware datetimes
        """
        now = timezone.now()
        
        if range_type == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif range_type == 'week':
            start_date = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        elif range_type == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif range_type == 'quarter':
            quarter_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(
                month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif range_type == 'year':
            start_date = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Invalid range_type: {range_type}")
            
        return start_date, now
    
    @staticmethod
    def get_recurring_users(days: int = 30) -> Dict:
        """
        Analyze user recurring usage patterns
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with recurring user statistics
        """
        from apps.analytics.models import UserSession
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get users with sessions in the period
        user_sessions = UserSession.objects.filter(
            start_time__gte=start_date,
            start_time__lte=end_date
        ).values('user').distinct()
        
        # Count distinct days per user
        user_engagement = {}
        
        for user_data in user_sessions:
            user_id = user_data['user']
            if not user_id:  # Skip anonymous sessions
                continue
                
            # Get distinct days this user was active
            distinct_days = UserSession.objects.filter(
                user_id=user_id,
                start_time__gte=start_date,
                start_time__lte=end_date
            ).dates('start_time', 'day').count()
            
            user_engagement[user_id] = distinct_days
        
        # Categorize users by engagement level
        engagement_levels = {
            'power_users': 0,      # >20 days active
            'regular_users': 0,    # 10-20 days active
            'casual_users': 0,     # 3-9 days active
            'one_time_users': 0    # 1-2 days active
        }
        
        for user_id, days_active in user_engagement.items():
            if days_active > 20:
                engagement_levels['power_users'] += 1
            elif days_active >= 10:
                engagement_levels['regular_users'] += 1
            elif days_active >= 3:
                engagement_levels['casual_users'] += 1
            else:
                engagement_levels['one_time_users'] += 1
        
        total_users = len(user_engagement)
        
        return {
            'total_users': total_users,
            'engagement_levels': engagement_levels,
            'engagement_percentages': {
                key: round((value / total_users) * 100, 1) if total_users > 0 else 0
                for key, value in engagement_levels.items()
            } if total_users > 0 else {
                'power_users': 0,
                'regular_users': 0,
                'casual_users': 0,
                'one_time_users': 0
            },
            'avg_active_days': round(
                sum(user_engagement.values()) / total_users, 1
            ) if total_users > 0 else 0
        }


class FileUtilities:
    """Utilities for file operations"""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        Get the file extension from a filename
        
        Args:
            filename: The filename
            
        Returns:
            File extension without dot
        """
        return os.path.splitext(filename)[1][1:].lower()
    
    @staticmethod
    def generate_unique_filename(filename: str) -> str:
        """
        Generate a unique filename by adding UUID
        
        Args:
            filename: Original filename
            
        Returns:
            Unique filename
        """
        name, ext = os.path.splitext(filename)
        return f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    
    @staticmethod
    def is_allowed_file_type(filename: str, allowed_types: List[str]) -> bool:
        """
        Check if file type is allowed
        
        Args:
            filename: The filename
            allowed_types: List of allowed extensions
            
        Returns:
            True if allowed, False otherwise
        """
        return FileUtilities.get_file_extension(filename) in allowed_types
    
    @staticmethod
    def get_file_size_mb(file_path: str) -> float:
        """
        Get file size in megabytes
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in MB
        """
        return os.path.getsize(file_path) / (1024 * 1024)


class SecurityUtilities:
    """Security utilities"""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Basic input sanitization
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
            
        import html
        return html.escape(text)
    
    @staticmethod
    def validate_request_origin(origin: str, allowed_origins: List[str]) -> bool:
        """
        Validate request origin for CORS
        
        Args:
            origin: The origin header from request
            allowed_origins: List of allowed origins
            
        Returns:
            True if allowed, False otherwise
        """
        if not origin:
            return False
            
        return origin in allowed_origins or '*' in allowed_origins
    
    @staticmethod
    def generate_rate_limit_key(user_id: str, action_type: str) -> str:
        """
        Generate a key for rate limiting
        
        Args:
            user_id: User ID or IP address
            action_type: Type of action being rate limited
            
        Returns:
            Rate limit key
        """
        return f"rate_limit:{action_type}:{user_id}"
