"""
RAG Service Locator with lazy loading and feature flags
Prevents import-time crashes from pydantic/langchain conflicts
"""

import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Global service instance and error tracking
_service = None
_init_error = None


def _get_feature_flag() -> bool:
    """Get RAG feature flag from Django settings with fallback to environment"""
    try:
        from django.conf import settings
        return getattr(settings, 'FEATURE_RAG', False)
    except ImportError:
        # Fallback to environment if Django not available
        return os.getenv("FEATURE_RAG", "0").lower() in {"1", "true", "yes", "on"}


def get_langchain_service() -> Optional[Dict[str, Any]]:
    """
    Lazy-create LangChain service; return None if disabled or if import fails.
    
    This function implements lazy loading to avoid import-time crashes
    when pydantic v2 conflicts with older LangChain versions.
    """
    global _service, _init_error
    
    # Return None if feature is disabled
    if not _get_feature_flag():
        logger.debug("RAG feature is disabled via FEATURE_RAG setting")
        return None
    
    # Return cached service if already initialized
    if _service is not None:
        return _service
    
    # Return None if we've already failed initialization
    if _init_error is not None:
        logger.debug(f"RAG service previously failed to initialize: {_init_error}")
        return None
    
    try:
        # Suppress Pydantic v2 warnings and force compatibility mode
        import warnings
        import os
        warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
        warnings.filterwarnings("ignore", message=".*pydantic.*")
        warnings.filterwarnings("ignore", message=".*__modify_schema__.*")
        
        # Force Pydantic v2 mode
        os.environ['PYDANTIC_V2'] = '1'
        
        # Try Strategy 1: Modern stack (Pydantic v2 + LangChain ≥ 0.2)
        # Use new split package imports to avoid conflicts
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # Try importing OpenAI with new package structure
        try:
            from langchain_openai import ChatOpenAI
            llm_factory = ChatOpenAI
            logger.info("Successfully imported langchain-openai")
        except ImportError as e:
            logger.warning(f"langchain-openai import failed: {e}")
            # Fallback to basic implementation
            llm_factory = None
        
        # Try importing vector stores with new package structure
        try:
            from langchain_community.vectorstores import FAISS
            vs_factory = FAISS
            logger.info("Successfully imported FAISS")
        except ImportError as e:
            logger.warning(f"FAISS import failed: {e}")
            vs_factory = None
        
        # Try importing embeddings
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings_factory = HuggingFaceEmbeddings
            logger.info("Successfully imported HuggingFace embeddings")
        except ImportError as e:
            logger.warning(f"HuggingFace embeddings import failed: {e}")
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                embeddings_factory = HuggingFaceEmbeddings
                logger.info("Successfully imported community HuggingFace embeddings")
            except ImportError as e2:
                logger.warning(f"Community embeddings import failed: {e2}")
                embeddings_factory = None
        
        # Build service dictionary
        _service = {
            "prompt_factory": ChatPromptTemplate,
            "parser_factory": StrOutputParser,
            "llm_factory": llm_factory,
            "vs_factory": vs_factory,
            "embeddings_factory": embeddings_factory,
            "enabled": True,
            "strategy": "robust"
        }
        
        logger.info(f"RAG service initialized successfully with components: {[k for k, v in _service.items() if v is not None]}")
        return _service
        
    except Exception as e:
        # Log the error and cache it to avoid repeated failures
        _init_error = e
        logger.warning(f"RAG service disabled due to initialization error: {e}")
        logger.info("RAG service will use mock implementations for development")
        return None
        return None


def langchain_status() -> Dict[str, Any]:
    """
    Get current status of LangChain service
    """
    service = get_langchain_service()
    
    return {
        "feature_enabled": _get_feature_flag(),
        "service_ready": service is not None,
        "error": str(_init_error) if _init_error else None,
        "strategy": service.get("strategy") if service else None,
        "available_factories": list(service.keys()) if service else []
    }


def reset_service():
    """
    Reset service state (useful for testing)
    """
    global _service, _init_error
    _service = None
    _init_error = None


# Compatibility function for existing code
def get_langchain_service_legacy():
    """
    Legacy function name for backward compatibility
    Returns the service or None if unavailable
    """
    service = get_langchain_service()
    if service:
        return service
    return None