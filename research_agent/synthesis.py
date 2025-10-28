"""
AI synthesis module for research agent.
Integrates with existing DeepSeek service and supports LangChain.
"""
import logging
from typing import List, Dict, Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# System prompt for research synthesis
RESEARCH_SYSTEM_PROMPT = """You are a precise research analyst. Your task is to synthesize findings ONLY from the provided sources.

Guidelines:
- Cite sources using [^n] footnotes where n is the source number
- Be accurate and only use information from the provided context
- If information is uncertain or contradictory, mention this
- Keep responses well-structured and concise
- Include a References section at the end mapping [^n] to URL + title
- Do not add information not present in the sources
- If sources are insufficient, state this clearly"""

USER_PROMPT_TEMPLATE = """Query: {query}

Context from top search results:

{context}

Please provide a comprehensive, well-structured answer in Markdown format. Use inline citations like [^1] and include a References section at the end."""


def build_context(chunks: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Build context string from retrieved chunks and create citation list.

    Args:
        chunks: List of chunk dictionaries

    Returns:
        Tuple of (context_string, citations_list)
    """
    if not chunks:
        return "No relevant sources found.", []

    context_lines = []
    citations = []

    for i, chunk in enumerate(chunks, start=1):
        url = chunk.get('url', 'Unknown URL')
        title = chunk.get('title', 'Untitled')
        text = chunk.get('text', '')
        score = chunk.get('score', 0)

        # Truncate text if too long
        if len(text) > 1200:
            text = text[:1200] + "..."

        # Add to context
        context_lines.append(f"[{i}] {title} — {url}\n{text}")

        # Add to citations
        citations.append({
            "n": i,
            "url": url,
            "title": title,
            "score": score
        })

    context = "\n\n".join(context_lines)
    return context, citations


def synthesize_answer(query: str, chunks: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Synthesize an answer from retrieved chunks using AI.

    Args:
        query: Research query
        chunks: Retrieved and ranked chunks

    Returns:
        Tuple of (answer_markdown, citations)
    """
    if not chunks:
        return "No relevant information found for this query.", []

    context, citations = build_context(chunks)

    try:
        # Use existing DeepSeek integration
        answer = _synthesize_with_deepseek(query, context)
        return answer, citations

    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        return _fallback_synthesis(query, chunks), citations


def _synthesize_with_deepseek(query: str, context: str) -> str:
    """
    Synthesize answer using DeepSeek API.

    Args:
        query: Research query
        context: Formatted context from sources

    Returns:
        Generated answer in markdown
    """
    try:
        # Import the existing DeepSeek service
        from apps.templates.deepseek_service import DeepSeekService

        # Create service instance
        service = DeepSeekService()

        # Prepare messages
        messages = [
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                query=query,
                context=context
            )}
        ]

        # Get response from DeepSeek
        response = service.complete(
            messages=messages,
            model=getattr(settings, 'RESEARCH', {}).get('ANSWER_MODEL', 'deepseek-chat'),
            temperature=0.1,  # Lower temperature for more factual responses
            max_tokens=2048
        )

        return response.content

    except ImportError:
        logger.warning("DeepSeek service not available, trying LangChain integration")
        return _synthesize_with_langchain(query, context)
    except Exception as e:
        logger.error(f"DeepSeek synthesis error: {e}")
        raise


def _synthesize_with_langchain(query: str, context: str) -> str:
    """
    Synthesize answer using LangChain (fallback method).

    Args:
        query: Research query
        context: Formatted context from sources

    Returns:
        Generated answer in markdown
    """
    try:
        # Try LangChain with OpenAI
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        # Use OpenAI as fallback
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=2048
        )

        messages = [
            SystemMessage(content=RESEARCH_SYSTEM_PROMPT),
            HumanMessage(content=USER_PROMPT_TEMPLATE.format(
                query=query,
                context=context
            ))
        ]

        response = llm.invoke(messages)
        return response.content

    except ImportError:
        logger.warning("LangChain not available, using basic synthesis")
        return _fallback_synthesis(query, context)
    except Exception as e:
        logger.error(f"LangChain synthesis error: {e}")
        raise


def _fallback_synthesis(query: str, chunks: List[Dict]) -> str:
    """
    Basic synthesis fallback when AI services are unavailable.

    Args:
        query: Research query
        chunks: Retrieved chunks

    Returns:
        Basic synthesized answer
    """
    if not chunks:
        return "No relevant sources found for this query."

    # Basic template-based synthesis
    answer_parts = [
        f"# Research Results for: {query}",
        "",
        "Based on the available sources, here are the key findings:",
        ""
    ]

    for i, chunk in enumerate(chunks[:5], start=1):
        title = chunk.get('title', 'Untitled')
        url = chunk.get('url', '')
        text = chunk.get('text', '')

        # Truncate text
        if len(text) > 300:
            text = text[:300] + "..."

        answer_parts.extend([
            f"## Source {i}: {title}",
            f"**URL:** {url}",
            f"**Content:** {text}",
            ""
        ])

    answer_parts.extend([
        "## References",
        ""
    ])

    for i, chunk in enumerate(chunks[:5], start=1):
        title = chunk.get('title', 'Untitled')
        url = chunk.get('url', '')
        answer_parts.append(f"[^{i}] {title} - {url}")

    return "\n".join(answer_parts)


def generate_summary(answer_md: str, max_length: int = 200) -> str:
    """
    Generate a brief summary of the research answer.

    Args:
        answer_md: Full markdown answer
        max_length: Maximum summary length

    Returns:
        Brief summary text
    """
    if not answer_md:
        return "No summary available."

    # Extract first paragraph or first few sentences
    lines = answer_md.split('\n')
    content_lines = [line for line in lines if line.strip() and not line.startswith('#')]

    if not content_lines:
        return "Summary not available."

    summary = content_lines[0]

    # Truncate if too long
    if len(summary) > max_length:
        # Try to end at sentence boundary
        sentences = summary.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence) > max_length - 10:
                break
            truncated += sentence + ". "

        if truncated:
            summary = truncated.strip()
        else:
            summary = summary[:max_length-3] + "..."

    return summary


def extract_key_points(answer_md: str) -> List[str]:
    """
    Extract key points from the research answer.

    Args:
        answer_md: Full markdown answer

    Returns:
        List of key points
    """
    if not answer_md:
        return []

    key_points = []
    lines = answer_md.split('\n')

    for line in lines:
        line = line.strip()
        # Look for bullet points, numbered lists, or headers
        if (line.startswith('- ') or
            line.startswith('* ') or
            line.startswith('## ') or
            (len(line.split('.')) > 1 and line.split('.')[0].isdigit())):

            # Clean up markdown formatting
            point = line.lstrip('- *#0123456789. ')
            if len(point) > 10 and len(point) < 200:  # Reasonable length
                key_points.append(point)

    return key_points[:5]  # Return top 5 key points


def validate_citations(answer_md: str, citations: List[Dict]) -> bool:
    """
    Validate that citations in the answer match the provided sources.

    Args:
        answer_md: Generated answer with citations
        citations: List of source citations

    Returns:
        True if citations are valid
    """
    if not citations:
        return True

    import re

    # Find all citation patterns [^n] in the answer
    citation_pattern = r'\[\^(\d+)\]'
    found_citations = re.findall(citation_pattern, answer_md)

    citation_numbers = {str(c['n']) for c in citations}

    # Check if all found citations have corresponding sources
    for citation_num in found_citations:
        if citation_num not in citation_numbers:
            logger.warning(f"Invalid citation [^{citation_num}] found in answer")
            return False

    return True