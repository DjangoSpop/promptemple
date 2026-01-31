"""
Lean Prompt Enhancement Service
Direct API calls to DeepSeek - no heavy dependencies

Target: <200ms response time (excluding DeepSeek API call)
"""

import requests
import logging
from typing import Dict, Optional
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class PromptEnhancementError(Exception):
    """Custom exception for enhancement failures"""
    pass


class PromptEnhancerService:
    """
    Lightweight prompt enhancement using DeepSeek API
    No LangChain, no heavy ML packages - just simple HTTP requests
    """
    
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    # System prompts for different enhancement types
    SYSTEM_PROMPTS = {
        'general': """You are an expert prompt engineer. Enhance the user's prompt to be more effective with AI models.

Apply these principles:
- Add clear context and constraints
- Structure for better reasoning
- Include output format specifications
- Maintain user's original intent

Return ONLY the enhanced prompt, no explanations.""",
        
        'technical': """You are an expert at crafting technical prompts.
Enhance this prompt for technical accuracy, precision, and structured output.
Include relevant technical context and expected format.

Return ONLY the enhanced prompt.""",
        
        'creative': """You are an expert at crafting creative prompts.
Enhance this prompt to inspire creative exploration while maintaining clarity.
Add context that encourages unique perspectives.

Return ONLY the enhanced prompt.""",
        
        'business': """You are an expert at crafting business prompts.
Enhance this prompt for clarity, professional tone, and actionable output.
Structure for decision-making and business value.

Return ONLY the enhanced prompt.""",
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the prompt enhancer service
        
        Args:
            api_key: DeepSeek API key (defaults to settings.DEEPSEEK_API_KEY)
        """
        self.api_key = api_key or getattr(settings, 'DEEPSEEK_API_KEY', None)
        
        if not self.api_key:
            logger.warning("DEEPSEEK_API_KEY not configured - enhancement will fail")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def enhance_prompt(
        self, 
        prompt: str,
        enhancement_type: str = "general",
        user_id: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Enhance a user prompt using DeepSeek
        
        Args:
            prompt: Original prompt to enhance
            enhancement_type: Type of enhancement (general, technical, creative, business)
            user_id: User ID for caching/tracking (optional)
            use_cache: Whether to use cached results (default: True)
        
        Returns:
            {
                'original': str,
                'enhanced': str,
                'improvement_notes': str,
                'tokens_used': int,
                'response_time_ms': float
            }
        
        Raises:
            PromptEnhancementError: If API call fails or input is invalid
        """
        
        # Input validation
        if not prompt or not prompt.strip():
            raise PromptEnhancementError("Empty prompt provided")
        
        if len(prompt) > 5000:
            raise PromptEnhancementError("Prompt too long (max 5000 characters)")
        
        if not self.api_key:
            raise PromptEnhancementError("DeepSeek API key not configured")
        
        # Check cache first (optional optimization)
        cache_key = None
        if use_cache:
            cache_key = f"enhanced_prompt:{hash(prompt)}:{enhancement_type}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for prompt enhancement")
                return cached_result
        
        # Select system prompt
        system_prompt = self.SYSTEM_PROMPTS.get(
            enhancement_type, 
            self.SYSTEM_PROMPTS['general']
        )
        
        # Prepare API request
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": False
        }
        
        try:
            import time
            start_time = time.time()
            
            logger.info(f"Sending enhancement request for {len(prompt)} chars prompt")
            
            response = requests.post(
                self.DEEPSEEK_API_URL,
                headers=self.headers,
                json=payload,
                timeout=15  # 15 second timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            response.raise_for_status()
            data = response.json()
            
            enhanced = data['choices'][0]['message']['content'].strip()
            tokens_used = data.get('usage', {}).get('total_tokens', 0)
            
            result = {
                'original': prompt,
                'enhanced': enhanced,
                'improvement_notes': self._generate_improvement_notes(prompt, enhanced),
                'tokens_used': tokens_used,
                'response_time_ms': response_time
            }
            
            # Cache successful result (30 minutes)
            if use_cache and cache_key:
                cache.set(cache_key, result, timeout=1800)
            
            logger.info(
                f"Prompt enhanced successfully in {response_time:.2f}ms "
                f"(tokens: {tokens_used})"
            )
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("DeepSeek API timeout")
            raise PromptEnhancementError("Enhancement timed out. Please try again.")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"DeepSeek API HTTP error: {e.response.status_code}")
            
            if e.response.status_code == 429:
                raise PromptEnhancementError("Rate limit exceeded. Please wait and try again.")
            elif e.response.status_code == 401:
                raise PromptEnhancementError("API authentication failed.")
            elif e.response.status_code == 400:
                error_msg = e.response.json().get('error', {}).get('message', 'Bad request')
                raise PromptEnhancementError(f"Invalid request: {error_msg}")
            else:
                raise PromptEnhancementError(f"API error: {str(e)}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API request failed: {str(e)}")
            raise PromptEnhancementError("Enhancement service unavailable. Please try again later.")
        
        except Exception as e:
            logger.error(f"Unexpected error during enhancement: {str(e)}")
            raise PromptEnhancementError(f"Enhancement failed: {str(e)}")
    
    def _generate_improvement_notes(self, original: str, enhanced: str) -> str:
        """
        Generate brief notes on what was improved
        
        Args:
            original: Original prompt text
            enhanced: Enhanced prompt text
        
        Returns:
            String describing improvements made
        """
        notes = []
        
        # Check for length increase (more detail added)
        if len(enhanced) > len(original) * 1.3:
            notes.append("Added context and structure")
        
        # Check for format specification
        format_keywords = ['format:', 'output:', 'structure:', 'return:']
        if any(word in enhanced.lower() for word in format_keywords):
            if not any(word in original.lower() for word in format_keywords):
                notes.append("Specified output format")
        
        # Check for improved organization
        if enhanced.count('\n') > original.count('\n') + 2:
            notes.append("Improved organization")
        
        # Check for added constraints
        constraint_keywords = ['must', 'should', 'ensure', 'include', 'avoid', 'do not']
        enhanced_constraints = sum(1 for word in constraint_keywords if word in enhanced.lower())
        original_constraints = sum(1 for word in constraint_keywords if word in original.lower())
        
        if enhanced_constraints > original_constraints + 2:
            notes.append("Added constraints")
        
        # Check for examples
        if 'example:' in enhanced.lower() and 'example:' not in original.lower():
            notes.append("Added examples")
        
        # Check for step-by-step structure
        if ('step' in enhanced.lower() or enhanced.count('1.') > 0) and 'step' not in original.lower():
            notes.append("Added step-by-step structure")
        
        return "; ".join(notes) if notes else "General refinement and clarity improvements"
    
    def batch_enhance(
        self, 
        prompts: list[str], 
        enhancement_type: str = "general",
        user_id: Optional[int] = None
    ) -> list[Dict]:
        """
        Enhance multiple prompts (useful for bulk operations)
        
        Args:
            prompts: List of prompts to enhance
            enhancement_type: Type of enhancement to apply
            user_id: User ID for tracking (optional)
        
        Returns:
            List of enhancement results (or error dicts)
        """
        results = []
        
        for idx, prompt in enumerate(prompts):
            try:
                logger.info(f"Enhancing prompt {idx + 1}/{len(prompts)}")
                result = self.enhance_prompt(prompt, enhancement_type, user_id)
                results.append(result)
                
            except PromptEnhancementError as e:
                logger.error(f"Failed to enhance prompt {idx + 1}: {str(e)}")
                results.append({
                    'original': prompt,
                    'error': str(e),
                    'success': False
                })
        
        return results
    
    def get_available_enhancement_types(self) -> list[str]:
        """Get list of available enhancement types"""
        return list(self.SYSTEM_PROMPTS.keys())
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key works
        
        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_key:
            return False
        
        try:
            # Simple test request
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": "test"}
                ],
                "max_tokens": 10
            }
            
            response = requests.post(
                self.DEEPSEEK_API_URL,
                headers=self.headers,
                json=payload,
                timeout=5
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False
