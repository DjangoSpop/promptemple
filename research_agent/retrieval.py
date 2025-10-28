"""
Vector retrieval functions with PostgreSQL pgvector and SQLite fallback support.
"""
import logging
from typing import List, Dict, Optional
from django.db import connection
from django.conf import settings
from .models import Chunk
from .utils import calculate_similarity

logger = logging.getLogger(__name__)


def get_database_engine() -> str:
    """Get the current database engine name."""
    return settings.DATABASES['default']['ENGINE']


def is_postgresql() -> bool:
    """Check if the current database is PostgreSQL."""
    return 'postgresql' in get_database_engine()


def top_k_chunks(query_embedding: List[float], k: int = 8, job_id: Optional[str] = None) -> List[Dict]:
    """
    Retrieve top-k most similar chunks using vector search.

    Args:
        query_embedding: Query embedding vector
        k: Number of chunks to retrieve
        job_id: Optional job ID to filter results

    Returns:
        List of chunk dictionaries with similarity scores
    """
    if not query_embedding:
        logger.warning("Empty query embedding provided")
        return []

    if is_postgresql():
        return _pgvector_search(query_embedding, k, job_id)
    else:
        return _sqlite_search(query_embedding, k, job_id)


def _pgvector_search(query_embedding: List[float], k: int, job_id: Optional[str] = None) -> List[Dict]:
    """
    Perform vector search using PostgreSQL pgvector extension.

    Args:
        query_embedding: Query embedding vector
        k: Number of results
        job_id: Optional job ID filter

    Returns:
        List of similar chunks
    """
    try:
        # pgvector cosine distance: 1 - cos_sim (lower is more similar)
        base_sql = """
            SELECT id, url, title, text, 1 - (embedding <=> %s::vector) AS score
            FROM research_agent_chunk
        """

        params = [query_embedding]

        if job_id:
            base_sql += " WHERE doc_id IN (SELECT id FROM research_agent_sourcedoc WHERE job_id = %s)"
            params.append(job_id)

        sql = base_sql + " ORDER BY embedding <=> %s::vector LIMIT %s"
        params.extend([query_embedding, k])

        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "url": row[1],
                "title": row[2],
                "text": row[3],
                "score": float(row[4])
            })

        logger.info(f"pgvector search returned {len(results)} chunks")
        return results

    except Exception as e:
        logger.error(f"pgvector search error: {e}")
        return []


def _sqlite_search(query_embedding: List[float], k: int, job_id: Optional[str] = None) -> List[Dict]:
    """
    Perform vector search using SQLite with cosine similarity calculation.

    Args:
        query_embedding: Query embedding vector
        k: Number of results
        job_id: Optional job ID filter

    Returns:
        List of similar chunks
    """
    try:
        # Build queryset
        queryset = Chunk.objects.all()

        if job_id:
            queryset = queryset.filter(doc__job_id=job_id)

        # Get all chunks and calculate similarity in Python
        # This is less efficient but works with SQLite
        chunks = list(queryset.values('id', 'url', 'title', 'text', 'embedding'))

        results = []
        for chunk in chunks:
            embedding = chunk.get('embedding', [])
            if not embedding:
                continue

            # Calculate cosine similarity
            similarity = calculate_similarity(query_embedding, embedding)

            results.append({
                "id": chunk['id'],
                "url": chunk['url'],
                "title": chunk['title'],
                "text": chunk['text'],
                "score": similarity
            })

        # Sort by similarity score (descending) and take top k
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:k]

        logger.info(f"SQLite search returned {len(results)} chunks")
        return results

    except Exception as e:
        logger.error(f"SQLite search error: {e}")
        return []


def search_chunks_by_text(query: str, k: int = 8, job_id: Optional[str] = None) -> List[Dict]:
    """
    Search chunks using text-based similarity (fallback method).

    Args:
        query: Text query
        k: Number of results
        job_id: Optional job ID filter

    Returns:
        List of matching chunks
    """
    try:
        # Build queryset
        queryset = Chunk.objects.all()

        if job_id:
            queryset = queryset.filter(doc__job_id=job_id)

        # Simple text search using Django's icontains
        chunks = list(queryset.filter(
            text__icontains=query
        ).values('id', 'url', 'title', 'text')[:k])

        results = []
        for chunk in chunks:
            results.append({
                "id": chunk['id'],
                "url": chunk['url'],
                "title": chunk['title'],
                "text": chunk['text'],
                "score": 0.5  # Default score for text search
            })

        logger.info(f"Text search returned {len(results)} chunks for: {query}")
        return results

    except Exception as e:
        logger.error(f"Text search error: {e}")
        return []


def get_chunk_by_id(chunk_id: int) -> Optional[Dict]:
    """
    Retrieve a specific chunk by ID.

    Args:
        chunk_id: Chunk ID

    Returns:
        Chunk data or None
    """
    try:
        chunk = Chunk.objects.get(id=chunk_id)
        return {
            "id": chunk.id,
            "url": chunk.url,
            "title": chunk.title,
            "text": chunk.text,
            "tokens": chunk.tokens,
            "doc_id": chunk.doc_id,
        }
    except Chunk.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Error retrieving chunk {chunk_id}: {e}")
        return None


def get_chunks_by_url(url: str, k: int = 10) -> List[Dict]:
    """
    Retrieve chunks from a specific URL.

    Args:
        url: Source URL
        k: Maximum number of chunks

    Returns:
        List of chunks from the URL
    """
    try:
        chunks = list(Chunk.objects.filter(
            url=url
        ).values('id', 'url', 'title', 'text', 'tokens')[:k])

        return chunks

    except Exception as e:
        logger.error(f"Error retrieving chunks for URL {url}: {e}")
        return []


def delete_chunks_by_job(job_id: str) -> int:
    """
    Delete all chunks associated with a job.

    Args:
        job_id: Job ID

    Returns:
        Number of chunks deleted
    """
    try:
        deleted_count, _ = Chunk.objects.filter(doc__job_id=job_id).delete()
        logger.info(f"Deleted {deleted_count} chunks for job {job_id}")
        return deleted_count

    except Exception as e:
        logger.error(f"Error deleting chunks for job {job_id}: {e}")
        return 0


def get_retrieval_stats() -> Dict:
    """
    Get statistics about the vector database.

    Returns:
        Database statistics
    """
    try:
        stats = {
            "total_chunks": Chunk.objects.count(),
            "unique_urls": Chunk.objects.values('url').distinct().count(),
            "database_engine": get_database_engine(),
            "supports_vector_search": is_postgresql(),
        }

        # Add more detailed stats if needed
        if stats["total_chunks"] > 0:
            from django.db import models
            avg_tokens = Chunk.objects.aggregate(
                avg_tokens=models.Avg('tokens')
            )['avg_tokens']
            stats["avg_tokens_per_chunk"] = round(avg_tokens or 0, 2)

        return stats

    except Exception as e:
        logger.error(f"Error getting retrieval stats: {e}")
        return {
            "total_chunks": 0,
            "unique_urls": 0,
            "database_engine": get_database_engine(),
            "supports_vector_search": is_postgresql(),
            "error": str(e)
        }


def rerank_chunks(chunks: List[Dict], query: str, method: str = "relevance") -> List[Dict]:
    """
    Rerank chunks using additional relevance signals.

    Args:
        chunks: List of chunks to rerank
        query: Original query
        method: Reranking method

    Returns:
        Reranked chunks
    """
    if not chunks or method == "none":
        return chunks

    try:
        if method == "relevance":
            # Simple relevance reranking based on query term frequency
            query_terms = query.lower().split()

            for chunk in chunks:
                text = chunk.get('text', '').lower()
                relevance_boost = 0

                for term in query_terms:
                    relevance_boost += text.count(term) * 0.1

                # Boost score based on relevance
                chunk['score'] = chunk.get('score', 0) + relevance_boost

            # Re-sort by updated scores
            chunks.sort(key=lambda x: x.get('score', 0), reverse=True)

        return chunks

    except Exception as e:
        logger.error(f"Error reranking chunks: {e}")
        return chunks