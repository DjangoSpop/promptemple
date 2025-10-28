"""
Embeddings and text processing utilities for research agent.
"""
import logging
from typing import List, Optional
from django.conf import settings

# Global embedder instance
_model = None

logger = logging.getLogger(__name__)


def get_embedder():
    """
    Get the sentence transformer model for embeddings.
    Lazy loads the model to avoid startup delays.
    """
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(settings, 'RESEARCH', {}).get(
                'EMBED_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'
            )
            _model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except ImportError as e:
            logger.error(f"sentence-transformers not available: {e}")
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install sentence-transformers"
            )
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (normalized)
    """
    if not texts:
        return []

    try:
        model = get_embedder()
        embeddings = model.encode(texts, normalize_embeddings=True)
        # Convert numpy arrays to Python lists for JSON serialization
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Return zero vectors as fallback
        return [[0.0] * 384 for _ in texts]


def embed_query(query: str) -> List[float]:
    """
    Generate embedding for a single query text.

    Args:
        query: Query text to embed

    Returns:
        Embedding vector (normalized)
    """
    if not query:
        return [0.0] * 384

    embeddings = embed_texts([query])
    return embeddings[0] if embeddings else [0.0] * 384


def split_text(text: str, tokens: int = 800, overlap: int = 120) -> List[str]:
    """
    Split text into chunks for processing.

    Args:
        text: Text to split
        tokens: Target chunk size in tokens (approximate)
        overlap: Overlap between chunks in tokens (approximate)

    Returns:
        List of text chunks
    """
    if not text:
        return []

    try:
        # Try to use LangChain splitter if available
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        # Rough estimation: 4 characters per token
        chunk_size = tokens * 4
        chunk_overlap = overlap * 4

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        chunks = splitter.split_text(text)
        return chunks

    except ImportError:
        logger.warning("LangChain not available, using simple text splitting")
        return _simple_text_split(text, tokens * 4, overlap * 4)
    except Exception as e:
        logger.error(f"Error splitting text: {e}")
        return _simple_text_split(text, tokens * 4, overlap * 4)


def _simple_text_split(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Simple text splitting fallback when LangChain is not available.

    Args:
        text: Text to split
        chunk_size: Character-based chunk size
        overlap: Character-based overlap

    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # If we're not at the end, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence boundary (period + space)
            last_period = text.rfind('. ', start, end)
            if last_period > start:
                end = last_period + 1
            else:
                # Look for word boundary
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = max(start + 1, end - overlap)

        # Avoid infinite loop
        if start >= len(text):
            break

    return chunks


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text (rough approximation).

    Args:
        text: Input text

    Returns:
        Estimated token count
    """
    if not text:
        return 0

    # Rough estimation: 4 characters per token on average
    return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to approximate token limit.

    Args:
        text: Input text
        max_tokens: Maximum token count

    Returns:
        Truncated text
    """
    if not text:
        return text

    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text

    # Truncate and try to end at word boundary
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:  # Don't truncate too much
        truncated = truncated[:last_space]

    return truncated + "..."


def validate_embedding_dimensions(embedding: List[float], expected_dim: int = 384) -> bool:
    """
    Validate embedding vector dimensions.

    Args:
        embedding: Embedding vector to validate
        expected_dim: Expected dimensionality

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(embedding, list):
        return False

    if len(embedding) != expected_dim:
        return False

    # Check that all values are numeric
    try:
        for val in embedding:
            float(val)
        return True
    except (TypeError, ValueError):
        return False