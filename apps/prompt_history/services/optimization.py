import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Try to import LangChain and LangSmith; graceful fallback
try:
    from langchain_core.prompts import PromptTemplate
    from langchain_openai import OpenAI
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False


def _hash_user_id(user_id: int) -> str:
    # Lightweight hash for telemetry privacy
    try:
        import hashlib
        return hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()[:12]
    except Exception:
        return 'anon'


def enhance_prompt(prompt: str, meta: Dict[str, Any], model: str = None, style: str = None) -> Dict[str, Any]:
    """Enhance prompt using LangChain (best-effort).

    Returns a dict with optimized_prompt, tokens_input, tokens_output, credits_spent, model_used, meta
    """
    start = time.time()
    result = {
        'optimized_prompt': prompt,
        'tokens_input': 0,
        'tokens_output': 0,
        'credits_spent': 0,
        'model_used': model or os.environ.get('PROMPT_OPTIMIZER_MODEL', 'gpt-3.5-turbo'),
        'meta': {}
    }

    if not LANGCHAIN_AVAILABLE:
        result['meta']['note'] = 'langchain_unavailable'
        result['credits_spent'] = 0
        result['meta']['latency_ms'] = int((time.time() - start) * 1000)
        return result

    # Setup tracing via environment variables (LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, etc.)
    # LangSmith tracing is auto-configured when env vars are set in LangChain 0.3+

    try:
        llm = OpenAI(temperature=0.2, model=result['model_used'])
        template_text = """You are a prompt optimizer. Improve the user prompt for clarity and brevity.
        Style: {style}
        Original:
        {original}
        """
        prompt_template = PromptTemplate(input_variables=['original', 'style'], template=template_text)
        # Use LCEL (LangChain Expression Language) instead of deprecated LLMChain
        chain = prompt_template | llm
        optimized = chain.invoke({'original': prompt, 'style': style or 'concise'})

        latency = int((time.time() - start) * 1000)
        # Best-effort tokens (LangChain/OpenAI client may provide exact counts)
        result.update({
            'optimized_prompt': optimized.strip(),
            'tokens_input': max(0, len(prompt.split())),
            'tokens_output': max(0, len(optimized.split())),
            'credits_spent': 1,
            'meta': {
                'latency_ms': latency,
                'user_hash': _hash_user_id(meta.get('user_id')) if meta.get('user_id') else 'anon',
                'session_id': meta.get('session_id')
            }
        })

        return result

    except Exception as e:
        logger.exception('Prompt enhancement failed: %s', e)
        result['meta']['error'] = str(e)
        result['meta']['latency_ms'] = int((time.time() - start) * 1000)
        return result
