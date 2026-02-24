import re
import json
import logging
import requests

from django.conf import settings
from django.db.models import Q, F
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_deepseek_config():
    """Return (api_key, base_url, model) from settings."""
    cfg = getattr(settings, 'DEEPSEEK_CONFIG', {})
    api_key = cfg.get('API_KEY') or cfg.get('DEEPSEEK_API_KEY', '')
    base_url = (cfg.get('BASE_URL') or cfg.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')).rstrip('/')
    model = cfg.get('DEFAULT_MODEL') or cfg.get('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat')
    return api_key, base_url, model


def _call_deepseek_sync(system_prompt: str, user_content: str,
                        max_tokens: int = 512, temperature: float = 0.3) -> str:
    """Synchronous DeepSeek chat completion. Returns content string."""
    api_key, base_url, model = _get_deepseek_config()
    if not api_key:
        raise ValueError("DeepSeek API key not configured")

    resp = requests.post(
        f"{base_url}/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _parse_json_response(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


def _get_template_model():
    """Lazily import the primary PromptTemplate model."""
    for path in (
        ('apps.templates.models', 'Template'),
        ('apps.propmtcraft.models', 'PromptTemplate'),
        ('apps.core.models', 'PromptTemplate'),
    ):
        module_path, class_name = path
        try:
            import importlib
            mod = importlib.import_module(module_path)
            return getattr(mod, class_name, None)
        except ImportError:
            continue
    return None


# ---------------------------------------------------------------------------
# Heuristic fallbacks (used when DeepSeek is unavailable)
# ---------------------------------------------------------------------------

def _heuristic_intent(prompt: str) -> dict:
    lower = prompt.lower()
    mapping = [
        ('coding',      ['code', 'function', 'class', 'debug', 'python', 'javascript', 'sql', 'api', 'bug']),
        ('creative',    ['story', 'poem', 'creative', 'write', 'fiction', 'narrative', 'imagine', 'novel']),
        ('analytical',  ['analyse', 'analyze', 'compare', 'evaluate', 'assess', 'report', 'data', 'chart']),
        ('technical',   ['technical', 'architecture', 'system', 'design', 'infrastructure', 'server']),
        ('business',    ['business', 'strategy', 'market', 'sales', 'revenue', 'plan', 'startup']),
        ('marketing',   ['marketing', 'campaign', 'brand', 'ad', 'social media', 'content', 'seo']),
        ('educational', ['explain', 'teach', 'learn', 'tutorial', 'how to', 'guide', 'course']),
    ]
    for intent, keywords in mapping:
        if any(kw in lower for kw in keywords):
            return {'intent': intent, 'confidence': 0.65, 'sub_intent': '', 'suggested_categories': [], 'keywords': []}
    return {'intent': 'general', 'confidence': 0.5, 'sub_intent': '', 'suggested_categories': [], 'keywords': []}


def _heuristic_assessment(prompt: str) -> dict:
    score = min(10.0, max(1.0, 3.0 + len(prompt) / 200))
    suggestions = []
    if len(prompt) < 50:
        suggestions.append("Add more context and background information")
    if '?' not in prompt and len(prompt) < 100:
        suggestions.append("Specify the expected output format or length")
    if not any(kw in prompt.lower() for kw in ['you are', 'act as', 'as a', 'your role']):
        suggestions.append("Add a role or persona to guide the AI (e.g. 'You are an expert...')")
    return {
        'score': round(score, 1),
        'clarity': round(score * 0.9, 1),
        'specificity': round(score * 0.8, 1),
        'effectiveness': round(score * 0.85, 1),
        'suggestions': suggestions or ["Add specific constraints", "Include example output"],
        'strengths': ["Clear intent"],
        'improved_prompt': '',
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class IntentDetectionView(APIView):
    """Detect user intent from a prompt using DeepSeek AI."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = (request.data.get('prompt') or request.data.get('query') or '').strip()
        if not prompt:
            return Response({'error': 'prompt is required'}, status=status.HTTP_400_BAD_REQUEST)

        system = (
            "You are an intent classifier for a prompt engineering tool. "
            "Analyse the user's input and respond ONLY with a JSON object (no markdown) with these fields:\n"
            "- intent: one of [creative, technical, analytical, educational, business, marketing, coding, general]\n"
            "- confidence: float 0.0-1.0\n"
            "- sub_intent: brief string (max 30 chars)\n"
            "- suggested_categories: array of 1-3 template category names\n"
            "- keywords: array of 3-6 key terms from the input"
        )
        try:
            raw = _call_deepseek_sync(system, prompt, max_tokens=300, temperature=0.2)
            data = _parse_json_response(raw)
            return Response({
                'intent': data.get('intent', 'general'),
                'confidence': float(data.get('confidence', 0.75)),
                'sub_intent': data.get('sub_intent', ''),
                'suggested_categories': data.get('suggested_categories', []),
                'keywords': data.get('keywords', []),
            })
        except Exception as e:
            logger.warning(f"IntentDetection DeepSeek call failed: {e}; using heuristic fallback")
            return Response(_heuristic_intent(prompt))


class PromptAssessmentView(APIView):
    """Assess prompt quality using DeepSeek AI."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        original_prompt = (request.data.get('original_prompt') or request.data.get('prompt') or '').strip()
        llm_response = (request.data.get('llm_response') or request.data.get('response') or '').strip()

        if not original_prompt:
            return Response({'error': 'original_prompt is required'}, status=status.HTTP_400_BAD_REQUEST)

        content_for_ai = f"PROMPT:\n{original_prompt}"
        if llm_response:
            content_for_ai += f"\n\nAI RESPONSE (first 1000 chars):\n{llm_response[:1000]}"

        system = (
            "You are a prompt engineering expert. Assess the quality of the prompt (and optional AI response). "
            "Respond ONLY with a JSON object (no markdown) containing:\n"
            "- score: float 1.0-10.0 (overall quality)\n"
            "- clarity: float 1.0-10.0\n"
            "- specificity: float 1.0-10.0\n"
            "- effectiveness: float 1.0-10.0\n"
            "- suggestions: array of 2-4 specific improvement strings\n"
            "- strengths: array of 1-3 positive aspects\n"
            "- improved_prompt: a rewritten, improved version of the original prompt"
        )
        try:
            raw = _call_deepseek_sync(system, content_for_ai, max_tokens=700, temperature=0.3)
            data = _parse_json_response(raw)
            return Response({
                'score': float(data.get('score', 7.0)),
                'clarity': float(data.get('clarity', 7.0)),
                'specificity': float(data.get('specificity', 7.0)),
                'effectiveness': float(data.get('effectiveness', 7.0)),
                'suggestions': data.get('suggestions', []),
                'strengths': data.get('strengths', []),
                'improved_prompt': data.get('improved_prompt', ''),
            })
        except Exception as e:
            logger.warning(f"PromptAssessment DeepSeek call failed: {e}; using heuristic")
            return Response(_heuristic_assessment(original_prompt))


class TemplateRenderingView(APIView):
    """Render a template by substituting {{variable}} placeholders."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        template_id = request.data.get('template_id') or request.data.get('templateId')
        variables = request.data.get('variables') or {}
        raw_template = request.data.get('template_content')  # caller may pass content directly

        if not raw_template and template_id:
            TemplateModel = _get_template_model()
            if TemplateModel:
                try:
                    tmpl = TemplateModel.objects.get(pk=template_id)
                    raw_template = getattr(tmpl, 'template_content', None) or getattr(tmpl, 'content', '')
                    # Increment usage counter
                    TemplateModel.objects.filter(pk=template_id).update(usage_count=F('usage_count') + 1)
                except Exception:
                    return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)

        if not raw_template:
            return Response(
                {'error': 'template_id or template_content is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Substitute {{variable}} and {variable} placeholders
        rendered = raw_template
        for key, val in variables.items():
            rendered = rendered.replace(f'{{{{{key}}}}}', str(val))
            rendered = rendered.replace(f'{{{key}}}', str(val))

        return Response({
            'rendered': rendered,
            'primary_result': rendered,
            'template_id': template_id,
            'variables_applied': list(variables.keys()),
            'metadata': {'variables_count': len(variables)},
        })


class LibrarySearchView(APIView):
    """Search for templates in the library."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = (request.query_params.get('q') or request.query_params.get('query') or '').strip()
        category = request.query_params.get('category', '')
        page_size = min(int(request.query_params.get('limit', 12)), 50)

        TemplateModel = _get_template_model()
        if not TemplateModel:
            return Response({'templates': [], 'total': 0})

        try:
            qs = TemplateModel.objects.filter(is_active=True, is_public=True)
            if query:
                qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))
            if category:
                qs = qs.filter(category__name__icontains=category)
            qs = qs.order_by('-usage_count', '-created_at')[:page_size]

            templates = []
            for t in qs:
                templates.append({
                    'id': str(t.id),
                    'title': getattr(t, 'title', ''),
                    'description': getattr(t, 'description', ''),
                    'category': str(getattr(t, 'category', '') or ''),
                    'usage_count': getattr(t, 'usage_count', 0),
                    'average_rating': getattr(t, 'average_rating', 0.0),
                    'tags': getattr(t, 'tags', []) or [],
                })
            return Response({'templates': templates, 'total': len(templates), 'query': query})
        except Exception as e:
            logger.error(f"LibrarySearch error: {e}")
            return Response({'templates': [], 'total': 0})


class GetTemplateView(APIView):
    """Get a specific template by ID or name."""
    permission_classes = [IsAuthenticated]

    def get(self, request, template_id=None):
        template_name = request.GET.get('name', '').strip()

        TemplateModel = _get_template_model()
        if not TemplateModel:
            return Response({'error': 'Template service unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            if template_id:
                tmpl = TemplateModel.objects.get(pk=template_id, is_active=True)
            elif template_name:
                tmpl = TemplateModel.objects.filter(title__iexact=template_name, is_active=True).first()
                if not tmpl:
                    return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'error': 'template_id or name is required'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'template': {
                    'id': str(tmpl.id),
                    'title': getattr(tmpl, 'title', ''),
                    'description': getattr(tmpl, 'description', ''),
                    'content': getattr(tmpl, 'template_content', None) or getattr(tmpl, 'content', ''),
                    'category': str(getattr(tmpl, 'category', '') or ''),
                    'tags': getattr(tmpl, 'tags', []) or [],
                    'usage_count': getattr(tmpl, 'usage_count', 0),
                    'average_rating': getattr(tmpl, 'average_rating', 0.0),
                    'is_public': getattr(tmpl, 'is_public', True),
                }
            })
        except Exception as e:
            logger.error(f"GetTemplate error: {e}")
            return Response({'error': 'Template not found'}, status=status.HTTP_404_NOT_FOUND)
