"""Assistant registry and DeepSeek-powered assistants for AI services."""

from __future__ import annotations

import logging
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Type

from asgiref.sync import async_to_sync, sync_to_async
from django.conf import settings
from django.utils import timezone

from .models import AssistantMessage, AssistantThread
from apps.templates.deepseek_integration import create_deepseek_llm
try:
    from tavily import TavilyClient
except ImportError:  # pragma: no cover
    TavilyClient = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssistantDescription:
    """Lightweight description of a registered assistant."""

    id: str
    name: str
    model: str
    summary: str
    tags: Sequence[str]


class AssistantRegistry:
    """Keeps track of all available assistants within the project."""

    _registry: Dict[str, Type["BaseAIAssistant"]] = {}

    @staticmethod
    def _is_enabled(assistant_cls: Type["BaseAIAssistant"]) -> bool:
        config = getattr(settings, "AI_ASSISTANT_SETTINGS", {})
        enabled = config.get("ENABLED") or ()
        if not enabled:
            return True
        full_path = f"{assistant_cls.__module__}.{assistant_cls.__name__}"
        return assistant_cls.id in enabled or full_path in enabled

    @classmethod
    def register(cls, assistant_cls: Type["BaseAIAssistant"]) -> Type["BaseAIAssistant"]:
        if not getattr(assistant_cls, "id", None):
            raise ValueError("Assistant classes must define a non-empty 'id' attribute")
        cls._registry[assistant_cls.id] = assistant_cls
        logger.debug("Registered AI assistant %s", assistant_cls.id)
        return assistant_cls

    @classmethod
    def create(
        cls,
        assistant_id: str,
        *,
        user=None,
        request=None,
        view=None,
        **kwargs,
    ) -> "BaseAIAssistant":
        assistant_cls = cls._registry.get(assistant_id)
        if not assistant_cls or not cls._is_enabled(assistant_cls):
            raise KeyError(f"Assistant '{assistant_id}' is not registered")
        return assistant_cls(user=user, request=request, view=view, **kwargs)

    @classmethod
    def list_descriptions(cls) -> List[AssistantDescription]:
        descriptions: List[AssistantDescription] = []
        for assistant_cls in cls._registry.values():
            if not cls._is_enabled(assistant_cls):
                continue
            descriptions.append(
                AssistantDescription(
                    id=assistant_cls.id,
                    name=assistant_cls.name,
                    model=assistant_cls.model,
                    summary=assistant_cls.summary,
                    tags=getattr(assistant_cls, "tags", ()),
                )
            )
        return descriptions


class BaseAIAssistant:
    """Minimal drop-in replacement for django-ai-assistant using DeepSeek."""

    id: str = "base"
    name: str = "Base Assistant"
    summary: str = "Generic AI assistant"
    instructions: str = "You are a helpful assistant."
    model: str = "deepseek-chat"
    task_type: str = "chat"
    temperature: float = 0.7
    max_tokens: int = 800
    tags: Sequence[str] = ("general",)

    def __init__(self, *, user=None, request=None, view=None, **kwargs):
        self._user = user if getattr(user, "is_authenticated", False) else None
        self._request = request
        self._view = view
        self._init_kwargs = kwargs
        self._llm = None

    # ------------------------------------------------------------------
    # Hooks that subclasses may override
    # ------------------------------------------------------------------
    def get_instructions(self) -> str:
        return self.instructions

    def get_tools(self) -> Sequence["AssistantTool"]:
        return ()

    def get_task_type(self) -> str:
        return self.task_type

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def arun(
        self,
        message: str,
        *,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not message:
            raise ValueError("Message content cannot be empty")

        thread = await self._ensure_thread(thread_id, metadata=metadata)
        await self._store_message(thread, role="user", content=message)

        messages = await self._build_message_payload(thread)
        response_payload = await self._call_model(messages)

        await self._store_message(
            thread,
            role="assistant",
            content=response_payload["content"],
            extra=response_payload.get("raw"),
        )
        await sync_to_async(thread.touch)()

        return {
            "assistant_id": self.id,
            "thread_id": str(thread.id),
            "message": response_payload["content"],
            "usage": response_payload.get("usage", {}),
            "raw": response_payload.get("raw", {}),
        }

    def run(
        self,
        message: str,
        *,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synchronous helper used by Django views."""

        return async_to_sync(self.arun)(message, thread_id=thread_id, metadata=metadata)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _ensure_thread(
        self,
        thread_id: Optional[str],
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AssistantThread:
        metadata = metadata or {}
        thread: Optional[AssistantThread] = None

        if thread_id:
            try:
                thread = await sync_to_async(AssistantThread.objects.get)(id=thread_id)
                if self._user and thread.user_id and thread.user_id != self._user.id:
                    logger.warning(
                        "User mismatch for assistant thread %s; creating a new thread",
                        thread_id,
                    )
                    thread = None
            except AssistantThread.DoesNotExist:
                logger.info("Assistant thread %s not found; creating a new one", thread_id)

        if thread is None:
            title = metadata.get("title") or self._generate_default_title(metadata)
            thread = await sync_to_async(AssistantThread.objects.create)(
                user=self._user,
                assistant_id=self.id,
                title=title[:255],
                metadata=metadata,
            )
        return thread

    async def _store_message(
        self,
        thread: AssistantThread,
        *,
        role: str,
        content: str,
        tool_name: Optional[str] = None,
        tool_result: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AssistantMessage:
        return await sync_to_async(AssistantMessage.objects.create)(
            thread=thread,
            role=role,
            content=content,
            tool_name=tool_name or "",
            tool_result=tool_result or {},
            extra=extra or {},
        )

    async def _build_message_payload(self, thread: AssistantThread) -> List[Dict[str, Any]]:
        history = await sync_to_async(list)(thread.messages.order_by("created_at"))
        messages: List[Dict[str, Any]] = []
        instructions = self.get_instructions()
        if instructions:
            messages.append({"role": "system", "content": instructions})
        for entry in history:
            messages.append(entry.as_openai_dict())
        return messages

    async def _call_model(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        llm = await self._get_llm()
        logger.debug("Calling DeepSeek LLM '%s' with %d messages", self.model, len(messages))
        response = await llm.ainvoke(messages)

        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

        usage = getattr(response, "usage", {})
        raw = getattr(response, "response_data", None)
        return {"content": content, "usage": usage, "raw": raw}

    async def _get_llm(self):
        if self._llm is None:
            llm_settings = getattr(settings, "AI_ASSISTANT_SETTINGS", {})
            llm_overrides = llm_settings.get("LLM_KWARGS", {})
            self._llm = create_deepseek_llm(
                task_type=self.get_task_type(),
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **llm_overrides,
            )
        return self._llm

    def _generate_default_title(self, metadata: Dict[str, Any]) -> str:
        prefix = metadata.get("title_hint") or self.name
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        return f"{prefix} {timestamp}"


class AssistantTool:
    """Simple callable tool abstraction so assistants can expose LangChain tools."""

    name: str
    description: str

    async def arun(self, *args, **kwargs) -> Any:
        raise NotImplementedError

    def run(self, *args, **kwargs) -> Any:
        return async_to_sync(self.arun)(*args, **kwargs)






class TavilySearchTool(AssistantTool):
    """Wrapper around Tavily search results."""

    name = "tavily_search"
    description = "Search the web with Tavily to gather fresh context."

    def __init__(self):
        config = getattr(settings, "AI_ASSISTANT_SETTINGS", {}).get("TAVILY", {})
        self.api_key = config.get("API_KEY")
        self.search_depth = config.get("SEARCH_DEPTH", "basic")
        self.max_results = int(config.get("MAX_RESULTS", 5))
        self._client: Optional[TavilyClient] = None

    def _get_client(self) -> Optional[TavilyClient]:
        if self._client is None and TavilyClient and self.api_key:
            self._client = TavilyClient(api_key=self.api_key)
        return self._client

    async def arun(self, query: str) -> Dict[str, Any]:
        client = self._get_client()
        if not client:
            logger.warning("Tavily API key missing; returning empty context")
            return {"error": "Tavily API key is not configured."}

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        def _search():
            return client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=self.max_results,
                include_answer=True,
            )

        return await loop.run_in_executor(None, _search)

    @staticmethod
    def format_context(payload: Dict[str, Any]) -> str:
        if not payload:
            return "No context was retrieved."
        if payload.get("error"):
            return str(payload["error"])

        lines: List[str] = []
        answer = payload.get("answer")
        if answer:
            lines.append(f"Summary: {answer}")

        for result in payload.get("results", [])[:3]:
            title = result.get("title") or "Untitled"
            url = result.get("url") or ""
            snippet = (result.get("content") or "").strip()
            if len(snippet) > 400:
                snippet = snippet[:400] + "..."
            lines.append(f"- {title} ({url})\n  {snippet}")

        if not lines:
            return "No relevant search snippets were returned."
        return "".join(lines)


@AssistantRegistry.register
class TavilyResearchAssistant(BaseAIAssistant):
    id = "tavily_research"
    name = "Tavily Research Assistant"
    summary = "Grounds answers in Tavily search results before responding"
    tags = ("research", "rag", "tavily")
    max_tokens = 900

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._search_tool = TavilySearchTool()

    def get_instructions(self) -> str:
        now = timezone.now().strftime("%Y-%m-%d %H:%M")
        return (
            "You are an investigative research assistant. Always incorporate the provided web search context "
            "in your answers and cite at least one source when relevant. Current timestamp: "
            f"{now}."
        )

    def get_tools(self) -> Sequence[AssistantTool]:
        return (self._search_tool,)

    async def arun(
        self,
        message: str,
        *,
        thread_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        thread = await self._ensure_thread(thread_id, metadata=metadata)
        await self._store_message(thread, role="user", content=message)

        context_payload = await self._search_tool.arun(message)
        context_text = self._search_tool.format_context(context_payload)
        await self._store_message(
            thread,
            role="tool",
            content=context_text,
            tool_name=self._search_tool.name,
            tool_result=context_payload,
        )

        messages = await self._build_message_payload(thread)
        if context_text:
            messages.append(
                {
                    "role": "system",
                    "content": "Use the Tavily context below when crafting your answer:\n" + context_text,
                }
            )

        response_payload = await self._call_model(messages)
        await self._store_message(
            thread,
            role="assistant",
            content=response_payload["content"],
            extra=response_payload.get("raw"),
        )
        await sync_to_async(thread.touch)()

        return {
            "assistant_id": self.id,
            "thread_id": str(thread.id),
            "message": response_payload["content"],
            "usage": response_payload.get("usage", {}),
            "raw": response_payload.get("raw", {}),
            "context": context_payload,
        }


@AssistantRegistry.register
class DeepSeekChatAssistant(BaseAIAssistant):
    id = "deepseek_chat"
    name = "DeepSeek Conversational Assistant"
    summary = "General-purpose assistant powered by DeepSeek chat models"
    tags = ("general", "deepseek")


@AssistantRegistry.register
class DeepSeekCoderAssistant(BaseAIAssistant):
    id = "deepseek_coder"
    name = "DeepSeek Coding Assistant"
    summary = "Focuses on high-quality code generation and review"
    tags = ("code", "deepseek")
    task_type = "coder"
    temperature = 0.25
    max_tokens = 1200

    def get_instructions(self) -> str:
        return (
            "You are a senior software engineer. Provide concise, production-ready code "
            "and include reasoning when highlighting potential issues."
        )
