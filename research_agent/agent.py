"""
Research Agent Orchestrator
Coordinates the entire research pipeline: search → fetch → chunk → embed → retrieve → synthesize
"""
import uuid
import asyncio
import logging
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import ResearchJob, SourceDoc, Chunk, ResearchAnswer
from .search import web_search, fetch_urls_batch
from .utils import clean_html_to_text, now_ms
from .embeddings import split_text, embed_texts, get_embedder, estimate_tokens
from .retrieval import top_k_chunks, rerank_chunks
from .synthesis import synthesize_answer, generate_summary

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Main research agent orchestrator."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job = None
        self.config = getattr(settings, 'RESEARCH', {})

    async def run(self) -> Dict[str, Any]:
        """
        Execute the complete research pipeline.

        Returns:
            Result dictionary with success status and metadata
        """
        try:
            # Load job
            self.job = ResearchJob.objects.get(pk=self.job_id)
            self.job.status = "running"
            self.job.save(update_fields=["status"])

            logger.info(f"Starting research job {self.job_id}: {self.job.query}")

            # Step 1: Web search
            search_results = await self._search_phase()

            # Step 2: Fetch and extract content
            docs = await self._fetch_phase(search_results)

            # Step 3: Chunk and embed content
            await self._chunk_and_embed_phase(docs)

            # Step 4: Retrieve relevant chunks
            relevant_chunks = await self._retrieval_phase()

            # Step 5: Synthesize answer
            await self._synthesis_phase(relevant_chunks)

            # Mark job as completed
            self.job.status = "done"
            self.job.finished_at = timezone.now()
            self.job.save(update_fields=["status", "finished_at"])

            logger.info(f"Research job {self.job_id} completed successfully")

            return {
                "success": True,
                "job_id": self.job_id,
                "query": self.job.query,
                "docs_processed": len(docs),
                "chunks_created": Chunk.objects.filter(doc__job=self.job).count(),
                "answer_available": hasattr(self.job, 'answer')
            }

        except Exception as e:
            logger.error(f"Research job {self.job_id} failed: {e}")
            if self.job:
                self.job.status = "error"
                self.job.error = str(e)
                self.job.finished_at = timezone.now()
                self.job.save(update_fields=["status", "error", "finished_at"])

            return {
                "success": False,
                "job_id": self.job_id,
                "error": str(e)
            }

    async def _search_phase(self) -> List[Dict[str, str]]:
        """
        Phase 1: Web search for relevant URLs.

        Returns:
            List of search results
        """
        logger.info(f"Searching for: {self.job.query}")

        search_results = web_search(
            query=self.job.query,
            k=self.config.get('SEARCH_TOP_K', 6)
        )

        logger.info(f"Found {len(search_results)} search results")
        return search_results

    async def _fetch_phase(self, search_results: List[Dict[str, str]]) -> List[SourceDoc]:
        """
        Phase 2: Fetch content from URLs.

        Args:
            search_results: List of search results

        Returns:
            List of created SourceDoc instances
        """
        if not search_results:
            return []

        logger.info(f"Fetching content from {len(search_results)} URLs")

        # Limit number of pages
        max_pages = self.config.get('MAX_PAGES', 10)
        urls_to_fetch = [result['url'] for result in search_results[:max_pages]]

        # Fetch URLs in batch
        timeout = self.config.get('FETCH_TIMEOUT_S', 15)
        fetch_results = await fetch_urls_batch(urls_to_fetch, timeout=timeout)

        # Create SourceDoc instances
        docs = []
        for result in search_results:
            url = result['url']
            title = result['title']

            # Find corresponding fetch result
            fetch_result = next(
                (fr for fr in fetch_results if fr[0] == url),
                (url, 0, "")
            )

            _, status_code, content = fetch_result

            # Clean HTML content
            clean_text = clean_html_to_text(content) if content else ""

            # Create SourceDoc
            doc = SourceDoc.objects.create(
                job=self.job,
                url=url,
                title=title,
                raw_html="",  # Don't store raw HTML to save space
                text=clean_text,
                status_code=status_code,
                fetched_ms=1000  # Placeholder
            )

            docs.append(doc)

        logger.info(f"Created {len(docs)} source documents")
        return docs

    async def _chunk_and_embed_phase(self, docs: List[SourceDoc]) -> None:
        """
        Phase 3: Split documents into chunks and generate embeddings.

        Args:
            docs: List of source documents
        """
        logger.info("Chunking and embedding documents")

        chunk_data = []
        texts_to_embed = []

        for doc in docs:
            if not doc.text or len(doc.text.strip()) < 50:
                continue

            # Split text into chunks
            chunks = split_text(
                text=doc.text,
                tokens=self.config.get('MAX_TOKENS_PER_CHUNK', 800),
                overlap=self.config.get('CHUNK_OVERLAP_TOKENS', 120)
            )

            for chunk_text in chunks:
                if len(chunk_text.strip()) < 20:  # Skip very short chunks
                    continue

                chunk_data.append({
                    'doc': doc,
                    'text': chunk_text,
                    'tokens': estimate_tokens(chunk_text),
                    'url': doc.url,
                    'title': doc.title
                })

                texts_to_embed.append(chunk_text)

        if not texts_to_embed:
            logger.warning("No texts to embed")
            return

        # Generate embeddings in batch
        logger.info(f"Generating embeddings for {len(texts_to_embed)} chunks")
        embeddings = embed_texts(texts_to_embed)

        # Create Chunk instances with embeddings
        chunks_to_create = []
        for chunk_info, embedding in zip(chunk_data, embeddings):
            chunks_to_create.append(Chunk(
                doc=chunk_info['doc'],
                text=chunk_info['text'],
                tokens=chunk_info['tokens'],
                embedding=embedding,
                url=chunk_info['url'],
                title=chunk_info['title']
            ))

        # Bulk create chunks
        with transaction.atomic():
            Chunk.objects.bulk_create(chunks_to_create, batch_size=100)

        logger.info(f"Created {len(chunks_to_create)} chunks with embeddings")

    async def _retrieval_phase(self) -> List[Dict]:
        """
        Phase 4: Retrieve relevant chunks for the query.

        Returns:
            List of relevant chunks
        """
        logger.info("Retrieving relevant chunks")

        # Generate query embedding
        query_embedding = embed_texts([self.job.query])
        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []

        # Retrieve top-k chunks
        chunks = top_k_chunks(
            query_embedding=query_embedding[0],
            k=8,
            job_id=str(self.job.id)
        )

        # Rerank chunks for better relevance
        chunks = rerank_chunks(chunks, self.job.query, method="relevance")

        logger.info(f"Retrieved {len(chunks)} relevant chunks")
        return chunks

    async def _synthesis_phase(self, chunks: List[Dict]) -> None:
        """
        Phase 5: Synthesize final answer from retrieved chunks.

        Args:
            chunks: List of relevant chunks
        """
        logger.info("Synthesizing answer from retrieved chunks")

        if not chunks:
            answer_md = "No relevant information found for this query."
            citations = []
        else:
            # Generate answer using AI
            answer_md, citations = synthesize_answer(self.job.query, chunks)

        # Create ResearchAnswer
        ResearchAnswer.objects.create(
            job=self.job,
            answer_md=answer_md,
            citations=citations
        )

        logger.info("Answer synthesis completed")


async def run_research_job(job_id: str) -> Dict[str, Any]:
    """
    Main entry point for running a research job.

    Args:
        job_id: UUID of the research job

    Returns:
        Result dictionary
    """
    agent = ResearchAgent(job_id)
    return await agent.run()


def run_research_job_sync(job_id: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for running a research job.

    Args:
        job_id: UUID of the research job

    Returns:
        Result dictionary
    """
    return asyncio.run(run_research_job(job_id))


class ResearchJobStats:
    """Utility class for job statistics and monitoring."""

    @staticmethod
    def get_job_progress(job_id: str) -> Dict[str, Any]:
        """
        Get progress information for a research job.

        Args:
            job_id: Job UUID

        Returns:
            Progress information
        """
        try:
            job = ResearchJob.objects.get(pk=job_id)

            progress = {
                "job_id": job_id,
                "status": job.status,
                "query": job.query,
                "created_at": job.created_at.isoformat(),
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "error": job.error,
            }

            # Add detailed progress if job is running or completed
            if job.status in ["running", "done"]:
                docs_count = job.docs.count()
                chunks_count = Chunk.objects.filter(doc__job=job).count()
                has_answer = hasattr(job, 'answer')

                progress.update({
                    "docs_processed": docs_count,
                    "chunks_created": chunks_count,
                    "answer_ready": has_answer,
                })

                if has_answer:
                    answer = job.answer
                    progress.update({
                        "answer_length": len(answer.answer_md),
                        "citations_count": len(answer.citations),
                        "summary": generate_summary(answer.answer_md)
                    })

            return progress

        except ResearchJob.DoesNotExist:
            return {"error": "Job not found"}
        except Exception as e:
            logger.error(f"Error getting job progress: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_system_stats() -> Dict[str, Any]:
        """
        Get system-wide research agent statistics.

        Returns:
            System statistics
        """
        try:
            from django.db.models import Count, Avg
            from datetime import timedelta

            now = timezone.now()
            last_24h = now - timedelta(hours=24)

            stats = {
                "total_jobs": ResearchJob.objects.count(),
                "jobs_last_24h": ResearchJob.objects.filter(created_at__gte=last_24h).count(),
                "completed_jobs": ResearchJob.objects.filter(status="done").count(),
                "failed_jobs": ResearchJob.objects.filter(status="error").count(),
                "total_documents": SourceDoc.objects.count(),
                "total_chunks": Chunk.objects.count(),
            }

            # Average processing time for completed jobs
            completed_jobs = ResearchJob.objects.filter(
                status="done",
                finished_at__isnull=False
            )

            if completed_jobs.exists():
                # Calculate average duration in seconds
                durations = []
                for job in completed_jobs:
                    duration = (job.finished_at - job.created_at).total_seconds()
                    durations.append(duration)

                if durations:
                    stats["avg_processing_time_seconds"] = sum(durations) / len(durations)

            return stats

        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}