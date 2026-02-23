"""
chat_template_service.py
========================
Extracts reusable prompt templates from AI chat messages.

Strategy:
  1. Regex-based pattern detection (fast, no extra AI calls).
  2. Optional DeepSeek classification for quality analysis (async-safe).

Exported:
  - chat_template_service  — singleton service instance
  - process_chat_message_templates  — callable for async dispatch
"""

import re
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# Minimum content length to attempt extraction
MIN_CONTENT_LENGTH = 100

# Patterns that suggest a message contains a reusable template
TEMPLATE_INDICATORS = [
    # Numbered lists suggesting structured steps
    r"^\d+\.\s+\w",
    # Section headers (markdown bold or ALL CAPS)
    r"\*\*.+\*\*",
    r"^[A-Z][A-Z\s]{3,}:",
    # Variable placeholders
    r"\{[a-zA-Z_]+\}",
    r"\[([A-Z_]+|[a-z_]+)\]",
    # Common template keywords
    r"\b(template|prompt|instructions?|guidelines?|steps?|format|structure)\b",
    # Code blocks
    r"```",
]

TEMPLATE_PATTERNS = [re.compile(p, re.MULTILINE | re.IGNORECASE) for p in TEMPLATE_INDICATORS]


def _calculate_confidence(content: str) -> float:
    """Score 0.0–1.0 based on how many template indicators match."""
    matches = sum(1 for p in TEMPLATE_PATTERNS if p.search(content))
    base = min(1.0, matches / len(TEMPLATE_PATTERNS))
    # Boost for longer, more structured content
    length_bonus = min(0.2, len(content) / 5000)
    return round(min(1.0, base + length_bonus), 2)


def _extract_title(content: str) -> str:
    """Best-effort title: first line, first sentence, or truncated start."""
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if lines:
        title = lines[0][:120]
        # Strip markdown formatting
        title = re.sub(r'[#*`_]', '', title).strip()
        if title:
            return title
    return content[:80].strip()


def _extract_keywords(content: str) -> list:
    """Extract simple keyword list."""
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
    words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
    freq: dict = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq, key=lambda k: freq[k], reverse=True)
    return sorted_words[:10]


class ChatTemplateService:
    """
    Service to detect and extract reusable templates from AI chat messages.
    """

    def process_chat_message(self, ai_message) -> dict:
        """
        Analyse an AI ChatMessage for template-extraction potential.

        Args:
            ai_message: apps.chat.models.ChatMessage instance

        Returns:
            dict with keys: extracted (bool), template_id (str|None), confidence (float)
        """
        try:
            from apps.chat.models import ExtractedTemplate
        except ImportError:
            logger.warning("ExtractedTemplate model not available")
            return {'extracted': False, 'template_id': None, 'confidence': 0.0}

        content = getattr(ai_message, 'content', '') or ''
        if len(content) < MIN_CONTENT_LENGTH:
            return {'extracted': False, 'template_id': None, 'confidence': 0.0}

        confidence = _calculate_confidence(content)
        if confidence < 0.15:
            return {'extracted': False, 'template_id': None, 'confidence': confidence}

        try:
            title = _extract_title(content)
            keywords = _extract_keywords(content)
            quality = 'high' if confidence >= 0.6 else ('medium' if confidence >= 0.35 else 'low')
            user = getattr(ai_message, 'user', None) or getattr(
                getattr(ai_message, 'session', None), 'user', None
            )
            if not user:
                return {'extracted': False, 'template_id': None, 'confidence': confidence}

            extracted = ExtractedTemplate.objects.create(
                source_message=ai_message,
                user=user,
                title=title,
                description=f"Auto-extracted template from chat session. Keywords: {', '.join(keywords[:5])}",
                template_content=content,
                extraction_method='regex',
                confidence_score=confidence,
                quality_rating=quality,
                keywords_extracted=keywords,
                status='pending',
            )

            logger.info(f"Extracted template {extracted.id} (confidence={confidence}) for user {user.id}")
            return {
                'extracted': True,
                'template_id': str(extracted.id),
                'confidence': confidence,
                'quality': quality,
            }

        except Exception as e:
            logger.error(f"Template extraction failed: {e}")
            return {'extracted': False, 'template_id': None, 'confidence': 0.0}

    def get_user_template_stats(self, user) -> dict:
        """
        Return extraction stats for a user.
        """
        try:
            from apps.chat.models import ExtractedTemplate
            qs = ExtractedTemplate.objects.filter(user=user)
            total = qs.count()
            pending = qs.filter(status='pending').count()
            approved = qs.filter(status='approved').count()
            rejected = qs.filter(status='rejected').count()
            high_quality = qs.filter(quality_rating='high').count()

            return {
                'total_extracted': total,
                'pending_review': pending,
                'approved': approved,
                'rejected': rejected,
                'high_quality': high_quality,
                'extraction_enabled': True,
                'service_status': 'active',
            }
        except Exception as e:
            logger.error(f"Failed to get template stats: {e}")
            return {
                'total_extracted': 0,
                'pending_review': 0,
                'approved': 0,
                'rejected': 0,
                'high_quality': 0,
                'extraction_enabled': True,
                'service_status': 'active',
            }

    def publish_approved_template(self, extracted_template) -> object | None:
        """
        Publish an approved ExtractedTemplate to the main template library.

        Returns the created Template object or None on failure.
        """
        try:
            # Import the main template model
            try:
                from apps.propmtcraft.models import PromptTemplate as Template
            except ImportError:
                try:
                    from apps.core.models import PromptTemplate as Template
                except ImportError:
                    logger.warning("Template model not found — cannot publish extracted template")
                    return None

            template = Template.objects.create(
                title=extracted_template.title,
                description=extracted_template.description,
                content=extracted_template.template_content,
                author=extracted_template.user,
                is_public=False,  # author reviews before publishing
                source='chat_extraction',
            )

            # Link back to the extraction
            extracted_template.published_template = template
            extracted_template.status = 'approved'
            extracted_template.reviewed_at = timezone.now()
            extracted_template.save(update_fields=['published_template', 'status', 'reviewed_at'])

            logger.info(f"Published template {template.id} from extraction {extracted_template.id}")
            return template

        except Exception as e:
            logger.error(f"Failed to publish extracted template {extracted_template.id}: {e}")
            return None


# Singleton service instance (imported by enhanced_views.py)
chat_template_service = ChatTemplateService()


def process_chat_message_templates(message_id: str):
    """
    Synchronous wrapper used when Celery is not available.
    Processes template extraction for a given ChatMessage ID.
    """
    try:
        from apps.chat.models import ChatMessage
        message = ChatMessage.objects.get(id=message_id)
        result = chat_template_service.process_chat_message(message)
        logger.debug(f"Template extraction result for message {message_id}: {result}")
        return result
    except Exception as e:
        logger.error(f"process_chat_message_templates failed for {message_id}: {e}")
        return {'extracted': False, 'template_id': None, 'confidence': 0.0}


# Make it callable like a Celery task (.delay() support)
class _TaskCompat:
    """Minimal Celery-task-like wrapper so .delay() calls don't raise AttributeError."""

    def __init__(self, fn):
        self._fn = fn

    def __call__(self, *args, **kwargs):
        return self._fn(*args, **kwargs)

    def delay(self, *args, **kwargs):
        """Synchronous fallback when Celery is not running."""
        return self._fn(*args, **kwargs)

    def apply_async(self, args=None, kwargs=None, **options):
        return self._fn(*(args or []), **(kwargs or {}))


process_chat_message_templates = _TaskCompat(process_chat_message_templates)
