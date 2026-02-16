"""
OpenRouter API integration for multi-provider AI services.
OpenAI-compatible interface with free models support.
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

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
                return str(value).lower() in ("true", "1", "yes", "on")
            return cast(value)
        return value

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API."""

    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "nvidia/nemotron-3-nano-30b-a3b:free"
    max_retries: int = 3
    timeout: int = 30
    http_referer: str = ""
    app_title: str = "PromptCraft"


class OpenRouterClient:
    """OpenRouter API client using OpenAI-compatible endpoints."""

    def __init__(self, config: OpenRouterConfig):
        self.config = config
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        if config.http_referer:
            headers["HTTP-Referer"] = config.http_referer
        if config.app_title:
            headers["X-Title"] = config.app_title

        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            headers=headers,
            timeout=config.timeout,
        )

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        payload = {
            "model": model or self.config.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            **kwargs,
        }

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = 2 ** attempt
                    logger.warning("OpenRouter rate limited, waiting %ss", wait_time)
                    await asyncio.sleep(wait_time)
                    continue
                logger.error("OpenRouter HTTP error %s: %s", e.response.status_code, e.response.text)
                raise
            except Exception as e:
                logger.error("OpenRouter API error (attempt %s): %s", attempt + 1, e)
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(1)

        raise Exception("Max retries exceeded for OpenRouter API")

    async def close(self):
        await self.client.aclose()


class OpenRouterResponse:
    """Response wrapper compatible with LangChain expectations."""

    def __init__(self, response_data: Dict[str, Any]):
        self.response_data = response_data

    @property
    def content(self) -> str:
        try:
            return self.response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "Error: Invalid response format"

    @property
    def usage(self) -> Dict[str, int]:
        return self.response_data.get("usage", {})

    def __str__(self) -> str:
        return self.content


class OpenRouterLangChainWrapper:
    """LangChain-compatible wrapper for OpenRouter API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs,
    ):
        if DJANGO_AVAILABLE:
            self.api_key = api_key or config("OPENROUTER_API_KEY", default="")
            base_url = config("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")
            default_model = config(
                "OPENROUTER_DEFAULT_MODEL",
                default="nvidia/nemotron-3-nano-30b-a3b:free",
            )
            timeout = config("OPENROUTER_TIMEOUT", default=30, cast=int)
            http_referer = config("OPENROUTER_HTTP_REFERER", default="")
            app_title = config("OPENROUTER_APP_TITLE", default="PromptCraft")
        else:
            self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
            base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            default_model = os.environ.get(
                "OPENROUTER_DEFAULT_MODEL",
                "nvidia/nemotron-3-nano-30b-a3b:free",
            )
            timeout = int(os.environ.get("OPENROUTER_TIMEOUT", "30"))
            http_referer = os.environ.get("OPENROUTER_HTTP_REFERER", "")
            app_title = os.environ.get("OPENROUTER_APP_TITLE", "PromptCraft")

        if not self.api_key:
            raise ValueError("OpenRouter API key not provided and not found in configuration")

        self.model = model or default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs

        self.config = OpenRouterConfig(
            api_key=self.api_key,
            base_url=base_url,
            default_model=default_model,
            timeout=timeout,
            http_referer=http_referer,
            app_title=app_title,
        )
        self.client = OpenRouterClient(self.config)

    async def ainvoke(self, messages):
        if isinstance(messages, str):
            formatted_messages = [{"role": "user", "content": messages}]
        elif isinstance(messages, list):
            formatted_messages = []
            for msg in messages:
                if hasattr(msg, "content") and hasattr(msg, "__class__"):
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
                **self.kwargs,
            )
            return OpenRouterResponse(response)
        except Exception as e:
            logger.error("OpenRouter invoke error: %s", e)
            return OpenRouterResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": f"Error processing request: {str(e)}"
                            }
                        }
                    ]
                }
            )

    def invoke(self, messages):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.ainvoke(messages))

    async def agenerate(self, messages):
        return await self.ainvoke(messages)

    def generate(self, messages):
        return self.invoke(messages)

    async def acall(self, messages):
        return await self.ainvoke(messages)

    def __call__(self, messages):
        return self.invoke(messages)


def create_openrouter_llm(
    task_type: str = "chat",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    model: Optional[str] = None,
    **kwargs,
) -> OpenRouterLangChainWrapper:
    """Factory to create OpenRouter LLM for specific tasks."""

    if task_type == "creative":
        temperature = max(temperature, 0.8)
    elif task_type == "coder":
        temperature = min(temperature, 0.3)
    elif task_type == "fast":
        max_tokens = min(max_tokens, 500)

    return OpenRouterLangChainWrapper(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        **kwargs,
    )


def get_openrouter_models() -> List[str]:
    """Return list of available free OpenRouter models."""
    return [
        "nvidia/nemotron-3-nano-30b-a3b:free",
        "qwen/qwen3-next-80b-a3b-instruct:free",
        "ai/glm-4.5-air:free",
        "deepseek/deepseek-r1-0528:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
    ]
