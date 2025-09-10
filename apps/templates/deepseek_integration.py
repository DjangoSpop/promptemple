"""
DeepSeek API integration for budget-friendly AI services
Provides OpenAI-compatible interface with DeepSeek models
"""

import os
import json
import time
import logging
import asyncio
import httpx
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

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
    default_model: str = "deepseek-chat"
    coder_model: str = "deepseek-coder"
    max_retries: int = 3
    timeout: int = 30
    
class DeepSeekClient:
    """
    DeepSeek API client with OpenAI-compatible interface
    Supports both chat and code generation models
    """
    
    def __init__(self, config: DeepSeekConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            },
            timeout=config.timeout
        )
        
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Create chat completion using DeepSeek API"""
        
        model = model or self.config.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt
                    logger.warning(f"Rate limited, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                    raise
                    
            except Exception as e:
                logger.error(f"DeepSeek API error (attempt {attempt + 1}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(1)
        
        raise Exception("Max retries exceeded for DeepSeek API")
    
    async def create_completion(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Create text completion using DeepSeek API"""
        
        # Convert to chat format for consistency
        messages = [{"role": "user", "content": prompt}]
        return await self.create_chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

class DeepSeekLangChainWrapper:
    """
    LangChain-compatible wrapper for DeepSeek API
    Provides the same interface as OpenAI models
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ):
        # Use Django's config system if available
        if DJANGO_AVAILABLE:
            self.api_key = api_key or config('DEEPSEEK_API_KEY', default='')
        else:
            self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", '')
            
        if not self.api_key:
            raise ValueError("DeepSeek API key not provided and not found in configuration")
            
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        self.config = DeepSeekConfig(api_key=self.api_key, default_model=model)
        self.client = DeepSeekClient(self.config)
        
    async def ainvoke(self, messages: Union[List[Dict], str]) -> "DeepSeekResponse":
        """Async invoke method compatible with LangChain"""
        
        # Handle different input formats
        if isinstance(messages, str):
            formatted_messages = [{"role": "user", "content": messages}]
        elif isinstance(messages, list):
            # Convert LangChain message objects to dict format
            formatted_messages = []
            for msg in messages:
                if hasattr(msg, 'content') and hasattr(msg, '__class__'):
                    # LangChain message object
                    role = "system" if "System" in msg.__class__.__name__ else "user"
                    if "Assistant" in msg.__class__.__name__ or "AI" in msg.__class__.__name__:
                        role = "assistant"
                    formatted_messages.append({"role": role, "content": msg.content})
                elif isinstance(msg, dict):
                    formatted_messages.append(msg)
                else:
                    formatted_messages.append({"role": "user", "content": str(msg)})
        else:
            formatted_messages = [{"role": "user", "content": str(messages)}]
        
        try:
            response = await self.client.create_chat_completion(
                messages=formatted_messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **self.kwargs
            )
            
            return DeepSeekResponse(response)
            
        except Exception as e:
            logger.error(f"DeepSeek invoke error: {e}")
            # Return a fallback response
            return DeepSeekResponse({
                "choices": [{
                    "message": {
                        "content": f"Error processing request: {str(e)}"
                    }
                }]
            })
    
    def invoke(self, messages: Union[List[Dict], str]) -> "DeepSeekResponse":
        """Sync invoke method - runs async method in new event loop"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.ainvoke(messages))
    
    # Aliases for different LangChain interfaces
    async def agenerate(self, messages):
        return await self.ainvoke(messages)
    
    def generate(self, messages):
        return self.invoke(messages)
    
    async def acall(self, messages):
        return await self.ainvoke(messages)
    
    def __call__(self, messages):
        return self.invoke(messages)

class DeepSeekResponse:
    """Response wrapper compatible with LangChain expectations"""
    
    def __init__(self, response_data: Dict[str, Any]):
        self.response_data = response_data
        
    @property
    def content(self) -> str:
        """Extract content from DeepSeek response"""
        try:
            return self.response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "Error: Invalid response format"
    
    @property
    def usage(self) -> Dict[str, int]:
        """Get token usage information"""
        return self.response_data.get("usage", {})
    
    def __str__(self) -> str:
        return self.content

def get_deepseek_models() -> Dict[str, str]:
    """Get available DeepSeek models for different use cases"""
    return {
        "chat": "deepseek-chat",           # General conversation and reasoning
        "coder": "deepseek-coder",         # Code generation and programming
        "math": "deepseek-math",           # Mathematical reasoning (if available)
        "fast": "deepseek-chat",           # Fast responses (same as chat)
        "creative": "deepseek-chat",       # Creative writing tasks
    }

def create_deepseek_llm(
    task_type: str = "chat",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    **kwargs
) -> DeepSeekLangChainWrapper:
    """
    Factory function to create DeepSeek LLM for specific tasks
    
    Args:
        task_type: Type of task ("chat", "coder", "math", "fast", "creative")
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        **kwargs: Additional arguments
    
    Returns:
        DeepSeekLangChainWrapper instance
    """
    
    models = get_deepseek_models()
    model = models.get(task_type, models["chat"])
    
    # Adjust temperature based on task type
    if task_type == "coder":
        temperature = min(temperature, 0.3)  # Lower temperature for code
    elif task_type == "creative":
        temperature = max(temperature, 0.8)  # Higher temperature for creativity
    elif task_type == "fast":
        max_tokens = min(max_tokens, 500)   # Limit tokens for speed
    
    return DeepSeekLangChainWrapper(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs
    )

# Compatibility aliases for easy replacement
DeepSeekChatModel = DeepSeekLangChainWrapper
ChatDeepSeek = DeepSeekLangChainWrapper

# Example usage and testing
async def test_deepseek_integration():
    """Test DeepSeek integration"""
    try:
        # Test basic chat
        llm = create_deepseek_llm("chat", temperature=0.7)
        response = await llm.ainvoke("Hello, how are you?")
        print(f"Chat response: {response.content}")
        
        # Test code generation
        coder = create_deepseek_llm("coder", temperature=0.2)
        code_response = await coder.ainvoke("Write a Python function to calculate fibonacci numbers")
        print(f"Code response: {code_response.content}")
        
        return True
        
    except Exception as e:
        logger.error(f"DeepSeek test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the integration
    asyncio.run(test_deepseek_integration())