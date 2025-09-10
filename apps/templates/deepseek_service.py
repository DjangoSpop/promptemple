"""
DeepSeek AI Service Integration
Budget-friendly AI provider with competitive performance
Supports both direct API calls and LangChain integration
"""

import os
import json
import time
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

# Import Django's config system
try:
    from django.conf import settings
    from decouple import config
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    def config(key, default=None, cast=None):
        value = os.environ.get(key, default)
        if cast and value is not None:
            if cast == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            else:
                return cast(value)
        return value

logger = logging.getLogger(__name__)

@dataclass
class DeepSeekConfig:
    """Configuration for DeepSeek API"""
    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    model_chat: str = "deepseek-chat"
    model_coder: str = "deepseek-coder"
    model_math: str = "deepseek-math"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30

@dataclass
class DeepSeekResponse:
    """Standardized response from DeepSeek API"""
    content: str
    model: str
    tokens_used: int
    response_time_ms: int
    success: bool
    error: Optional[str] = None

class DeepSeekService:
    """
    High-performance DeepSeek AI service
    Provides cost-effective AI capabilities for prompt optimization
    """
    
    def __init__(self, config: Optional[DeepSeekConfig] = None):
        self.config = config or self._load_config()
        self.session = None
        self._setup_session()
        
    def _load_config(self) -> DeepSeekConfig:
        """Load configuration from Django config/environment variables"""
        # Use Django's config system if available, fallback to os.environ
        if DJANGO_AVAILABLE:
            api_key = config('DEEPSEEK_API_KEY', default='')
            base_url = config('DEEPSEEK_BASE_URL', default='https://api.deepseek.com/v1')
            model_chat = config('DEEPSEEK_DEFAULT_MODEL', default='deepseek-chat')
            model_coder = config('DEEPSEEK_CODER_MODEL', default='deepseek-coder')
            model_math = config('DEEPSEEK_MATH_MODEL', default='deepseek-math')
            max_tokens = config('DEEPSEEK_MAX_TOKENS', default=2048, cast=int)
            temperature = config('DEEPSEEK_TEMPERATURE', default=0.7, cast=float)
            timeout = config('DEEPSEEK_TIMEOUT', default=30, cast=int)
        else:
            api_key = os.getenv('DEEPSEEK_API_KEY', '')
            base_url = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
            model_chat = os.getenv('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat')
            model_coder = os.getenv('DEEPSEEK_CODER_MODEL', 'deepseek-coder')
            model_math = os.getenv('DEEPSEEK_MATH_MODEL', 'deepseek-math')
            max_tokens = int(os.getenv('DEEPSEEK_MAX_TOKENS', '2048'))
            temperature = float(os.getenv('DEEPSEEK_TEMPERATURE', '0.7'))
            timeout = int(os.getenv('DEEPSEEK_TIMEOUT', '30'))
        
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not configured - DeepSeek service will be disabled")
            
        return DeepSeekConfig(
            api_key=api_key,
            base_url=base_url,
            model_chat=model_chat,
            model_coder=model_coder,
            model_math=model_math,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )
    
    def _setup_session(self):
        """Setup aiohttp session with proper headers"""
        if not self.config.api_key:
            # Don't set up session if no API key
            self.headers = {}
            return
            
        self.headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PromptCraft/1.0"
        }
    
    @property
    def enabled(self) -> bool:
        """Check if the service is properly configured and enabled"""
        return bool(self.config.api_key)
    
    def is_enabled(self) -> bool:
        """Check if the service is properly configured and enabled"""
        return bool(self.config.api_key)
    
    async def _make_request(
        self, 
        messages: List[Dict], 
        model: Optional[str] = None,
        **kwargs
    ) -> DeepSeekResponse:
        """Make API request to DeepSeek"""
        start_time = time.time()
        
        payload = {
            "model": model or self.config.model_chat,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "stream": False
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ['max_tokens', 'temperature']:
                payload[key] = value
        
        try:
            if not self.session:
                connector = aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                self.session = aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=self.headers
                )
            
            async with self.session.post(
                f"{self.config.base_url}/chat/completions",
                json=payload
            ) as response:
                response_time_ms = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    choice = data['choices'][0]
                    
                    return DeepSeekResponse(
                        content=choice['message']['content'],
                        model=data['model'],
                        tokens_used=data['usage']['total_tokens'],
                        response_time_ms=response_time_ms,
                        success=True
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"DeepSeek API error {response.status}: {error_text}")
                    
                    return DeepSeekResponse(
                        content="",
                        model=model or self.config.model_chat,
                        tokens_used=0,
                        response_time_ms=response_time_ms,
                        success=False,
                        error=f"API Error {response.status}: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error("DeepSeek API timeout")
            
            return DeepSeekResponse(
                content="",
                model=model or self.config.model_chat,
                tokens_used=0,
                response_time_ms=response_time_ms,
                success=False,
                error="Request timeout"
            )
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"DeepSeek API request failed: {e}")
            
            return DeepSeekResponse(
                content="",
                model=model or self.config.model_chat,
                tokens_used=0,
                response_time_ms=response_time_ms,
                success=False,
                error=str(e)
            )
    
    async def process_intent(self, query: str) -> Dict[str, Any]:
        """Process user intent using DeepSeek"""
        if not self.is_enabled():
            logger.warning("DeepSeek service is disabled - returning fallback intent")
            return self._fallback_intent(query)
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert at understanding user intent for prompt engineering.
                Analyze the user's query and classify it into one of these categories:
                - content_creation: Writing articles, stories, marketing copy
                - technical_writing: Documentation, tutorials, technical specs  
                - communication: Emails, messages, formal letters
                - analysis: Data analysis, research, summarization
                - creative: Brainstorming, ideation, creative writing
                - coding: Programming, code review, technical solutions
                - business: Proposals, reports, presentations
                - education: Teaching materials, explanations, learning
                - general: Other or unclear intent
                
                Respond with JSON format:
                {
                    "category": "category_name",
                    "confidence": 0.95,
                    "keywords": ["key1", "key2"],
                    "context": "brief explanation",
                    "suggested_approach": "optimization strategy"
                }"""
            },
            {
                "role": "user",
                "content": f"Query: {query}"
            }
        ]
        
        response = await self._make_request(
            messages, 
            model=self.config.model_chat,
            temperature=0.1,
            max_tokens=300
        )
        
        if response.success:
            try:
                parsed_data = json.loads(response.content)
                return {
                    "processed_data": parsed_data,
                    "category": parsed_data.get("category", "general"),
                    "confidence": parsed_data.get("confidence", 0.5),
                    "keywords": parsed_data.get("keywords", []),
                    "context": parsed_data.get("context", ""),
                    "processing_time_ms": response.response_time_ms,
                    "tokens_used": response.tokens_used,
                    "model": response.model
                }
            except json.JSONDecodeError:
                # Fallback parsing
                return self._parse_fallback_intent(response.content, query)
        else:
            logger.error(f"Intent processing failed: {response.error}")
            return {
                "processed_data": {},
                "category": "general",
                "confidence": 0.1,
                "keywords": [],
                "context": f"Error: {response.error}",
                "processing_time_ms": response.response_time_ms
            }
    
    def _fallback_intent(self, query: str) -> Dict[str, Any]:
        """Fallback intent classification when service is disabled"""
        query_lower = query.lower()
        
        # Simple keyword-based classification
        if any(word in query_lower for word in ['write', 'create', 'generate', 'compose']):
            category = 'content_creation'
        elif any(word in query_lower for word in ['code', 'program', 'debug', 'function']):
            category = 'coding'
        elif any(word in query_lower for word in ['analyze', 'research', 'study', 'examine']):
            category = 'analysis'
        elif any(word in query_lower for word in ['email', 'letter', 'message', 'communication']):
            category = 'communication'
        elif any(word in query_lower for word in ['business', 'proposal', 'report', 'presentation']):
            category = 'business'
        elif any(word in query_lower for word in ['creative', 'brainstorm', 'idea', 'innovative']):
            category = 'creative'
        elif any(word in query_lower for word in ['teach', 'explain', 'tutorial', 'learn']):
            category = 'education'
        elif any(word in query_lower for word in ['document', 'technical', 'specification']):
            category = 'technical_writing'
        else:
            category = 'general'
        
        keywords = [word for word in query_lower.split() if len(word) > 3][:5]
        
        return {
            "processed_data": {
                "category": category,
                "confidence": 0.6,
                "keywords": keywords,
                "context": "Simple classification (DeepSeek disabled)",
                "suggested_approach": f"Basic {category} optimization"
            },
            "category": category,
            "confidence": 0.6,
            "keywords": keywords,
            "context": "Simple classification (DeepSeek disabled)",
            "processing_time_ms": 1
        }
    
    def _fallback_optimization(self, prompt: str) -> Dict[str, Any]:
        """Fallback prompt optimization when service is disabled"""
        improvements = []
        optimized = prompt
        
        # Basic optimization suggestions
        if not prompt.strip().endswith(('?', '.', '!')):
            improvements.append("Add clear punctuation to end the prompt")
            optimized = prompt.strip() + "."
        
        if len(prompt.split()) < 5:
            improvements.append("Consider adding more specific details")
        
        if prompt.isupper():
            improvements.append("Use normal capitalization instead of all caps")
            optimized = prompt.capitalize()
        
        if not improvements:
            improvements.append("Prompt appears well-formed")
        
        return {
            "optimized_prompt": optimized,
            "improvements": improvements,
            "clarity_score": 0.7,
            "specificity_score": 0.6,
            "effectiveness_score": 0.6,
            "suggestions": improvements,
            "processing_time_ms": 1,
            "note": "Fallback optimization (DeepSeek disabled)"
        }
    
    def _fallback_content(self, prompt: str) -> Dict[str, Any]:
        """Fallback content generation when service is disabled"""
        return {
            "content": f"[DeepSeek service disabled] Would generate content for: {prompt[:50]}...",
            "confidence": 0.1,
            "note": "DeepSeek service is disabled - no API key configured"
        }
    
    async def optimize_prompt(
        self, 
        original_prompt: str, 
        user_intent: Optional[str] = None,
        optimization_type: str = "enhancement"
    ) -> Dict[str, Any]:
        """Optimize a prompt using DeepSeek"""
        
        if not self.is_enabled():
            logger.warning("DeepSeek service is disabled - returning fallback optimization")
            return self._fallback_optimization(original_prompt)
        
        system_message = f"""You are an expert prompt engineer specializing in optimization.
        Your task is to improve prompts while maintaining their core intent and effectiveness.
        
        Guidelines:
        - Maintain the original intent and purpose
        - Improve clarity and specificity
        - Enhance actionability and outcomes
        - Consider the user's context and intent
        - Provide specific, measurable improvements
        
        User Intent: {user_intent or 'Not specified'}
        Optimization Type: {optimization_type}
        
        Respond with JSON format:
        {{
            "optimized_content": "improved prompt content",
            "improvements": ["specific improvement 1", "improvement 2"],
            "rationale": "explanation of changes",
            "confidence": 0.85,
            "clarity_score": 0.9,
            "effectiveness_score": 0.8
        }}"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Original Prompt: {original_prompt}"}
        ]
        
        # Use the coder model for better structured output
        response = await self._make_request(
            messages,
            model=self.config.model_coder,
            temperature=0.3,
            max_tokens=1500
        )
        
        if response.success:
            try:
                parsed_data = json.loads(response.content)
                return {
                    "optimized_content": parsed_data.get("optimized_content", original_prompt),
                    "improvements": parsed_data.get("improvements", []),
                    "rationale": parsed_data.get("rationale", ""),
                    "confidence": parsed_data.get("confidence", 0.7),
                    "clarity_score": parsed_data.get("clarity_score", 0.7),
                    "effectiveness_score": parsed_data.get("effectiveness_score", 0.7),
                    "processing_time_ms": response.response_time_ms,
                    "tokens_used": response.tokens_used,
                    "model": response.model
                }
            except json.JSONDecodeError:
                return {
                    "optimized_content": response.content,
                    "improvements": ["Response parsing issue - manual review recommended"],
                    "rationale": "DeepSeek provided optimization but JSON parsing failed",
                    "confidence": 0.5,
                    "processing_time_ms": response.response_time_ms,
                    "tokens_used": response.tokens_used
                }
        else:
            return {
                "optimized_content": original_prompt,
                "improvements": [f"Optimization failed: {response.error}"],
                "rationale": "DeepSeek API error occurred",
                "confidence": 0.0,
                "processing_time_ms": response.response_time_ms
            }
    
    async def generate_content(
        self,
        prompt: str,
        content_type: str = "general",
        max_length: int = 500
    ) -> Dict[str, Any]:
        """Generate content using DeepSeek"""
        
        if not self.is_enabled():
            logger.warning("DeepSeek service is disabled - returning fallback content")
            return self._fallback_content(prompt)
        
        system_prompts = {
            "marketing": "You are a marketing copy expert. Create compelling, persuasive content.",
            "technical": "You are a technical writer. Create clear, accurate documentation.",
            "creative": "You are a creative writer. Create engaging, imaginative content.",
            "business": "You are a business communications expert. Create professional content.",
            "general": "You are a helpful AI assistant. Create high-quality content."
        }
        
        system_message = system_prompts.get(content_type, system_prompts["general"])
        system_message += f"\n\nGenerate content based on the following prompt. Keep it under {max_length} characters."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._make_request(
            messages,
            model=self.config.model_chat,
            temperature=0.7,
            max_tokens=min(max_length // 3, self.config.max_tokens)  # Rough token estimation
        )
        
        if response.success:
            return {
                "generated_content": response.content,
                "content_type": content_type,
                "length": len(response.content),
                "processing_time_ms": response.response_time_ms,
                "tokens_used": response.tokens_used,
                "model": response.model,
                "success": True
            }
        else:
            return {
                "generated_content": f"Content generation failed: {response.error}",
                "content_type": content_type,
                "length": 0,
                "processing_time_ms": response.response_time_ms,
                "success": False,
                "error": response.error
            }
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using DeepSeek"""
        
        messages = [
            {
                "role": "system",
                "content": """Analyze the sentiment of the given text. Respond with JSON format:
                {
                    "sentiment": "positive|negative|neutral",
                    "confidence": 0.95,
                    "emotions": ["joy", "excitement"],
                    "intensity": 0.8,
                    "reasoning": "brief explanation"
                }"""
            },
            {"role": "user", "content": f"Text to analyze: {text}"}
        ]
        
        response = await self._make_request(
            messages,
            model=self.config.model_chat,
            temperature=0.2,
            max_tokens=300
        )
        
        if response.success:
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                return self._parse_fallback_sentiment(response.content)
        else:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "emotions": [],
                "error": response.error
            }
    
    async def generate_suggestions(
        self, 
        partial_input: str, 
        context: Optional[str] = None
    ) -> List[str]:
        """Generate real-time suggestions"""
        
        system_message = """Generate 5 helpful suggestions to complete or improve the user's input.
        Focus on practical, actionable suggestions.
        Respond with JSON format: {"suggestions": ["suggestion1", "suggestion2", ...]}"""
        
        if context:
            system_message += f"\n\nContext: {context}"
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Partial input: {partial_input}"}
        ]
        
        response = await self._make_request(
            messages,
            model=self.config.model_chat,
            temperature=0.8,
            max_tokens=400
        )
        
        if response.success:
            try:
                data = json.loads(response.content)
                return data.get("suggestions", [])
            except json.JSONDecodeError:
                # Fallback: split response by lines
                return [line.strip() for line in response.content.split('\n') if line.strip()][:5]
        else:
            return []
    
    def _parse_fallback_intent(self, response_text: str, query: str) -> Dict:
        """Fallback intent parsing when JSON parsing fails"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["write", "create", "draft", "compose"]):
            category = "content_creation"
        elif any(word in query_lower for word in ["email", "message", "letter"]):
            category = "communication"
        elif any(word in query_lower for word in ["technical", "documentation", "code"]):
            category = "technical_writing"
        elif any(word in query_lower for word in ["analyze", "research", "data"]):
            category = "analysis"
        else:
            category = "general"
            
        return {
            "processed_data": {"category": category},
            "category": category,
            "confidence": 0.6,
            "keywords": query.split()[:5],
            "context": f"Fallback parsing detected {category}",
            "processing_time_ms": 50
        }
    
    def _parse_fallback_sentiment(self, response_text: str) -> Dict:
        """Fallback sentiment parsing"""
        text_lower = response_text.lower()
        
        if any(word in text_lower for word in ["positive", "good", "happy", "great"]):
            sentiment = "positive"
        elif any(word in text_lower for word in ["negative", "bad", "sad", "awful"]):
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        return {
            "sentiment": sentiment,
            "confidence": 0.5,
            "emotions": [],
            "reasoning": "Fallback keyword-based analysis"
        }
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    def __del__(self):
        """Cleanup session on deletion"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            # Don't try to close in __del__ as it can cause issues
            # Log a warning instead
            logger.warning("DeepSeek session not properly closed - use await service.close()")
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

# Global DeepSeek service instance
_deepseek_service = None

def get_deepseek_service() -> Optional[DeepSeekService]:
    """Get or create global DeepSeek service instance"""
    global _deepseek_service
    
    if _deepseek_service is None:
        try:
            _deepseek_service = DeepSeekService()
            logger.info("DeepSeek service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek service: {e}")
            _deepseek_service = None
    
    return _deepseek_service

# Convenience function for quick testing
async def test_deepseek_connection() -> bool:
    """Test DeepSeek API connection"""
    try:
        service = get_deepseek_service()
        if not service:
            return False
            
        response = await service._make_request([
            {"role": "user", "content": "Say 'Hello' if you can hear me."}
        ])
        
        success = response.success and "hello" in response.content.lower()
        logger.info(f"DeepSeek connection test: {'SUCCESS' if success else 'FAILED'}")
        return success
        
    except Exception as e:
        logger.error(f"DeepSeek connection test failed: {e}")
        return False