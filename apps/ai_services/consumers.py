"""
WebSocket consumers for AI services - streaming AI responses and real-time processing
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()

class AIProcessingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time AI processing operations"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.room_group_name = None
        self.processing_queue = []
        
    async def connect(self):
        """Handle WebSocket connection"""
        start_time = time.time()
        
        try:
            self.session_id = self.scope['url_route']['kwargs'].get('session_id')
            if not self.session_id:
                await self.close()
                return
                
            if self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
                
            self.room_group_name = f'ai_processing_{self.session_id}'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'ai_connection_established',
                'session_id': self.session_id,
                'timestamp': timezone.now().isoformat(),
                'capabilities': [
                    'prompt_optimization',
                    'content_generation',
                    'real_time_processing',
                    'streaming_responses'
                ]
            }))
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info(f"AI WebSocket connected: session={self.session_id}, time={elapsed_ms}ms")
            
        except Exception as e:
            logger.error(f"AI WebSocket connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        logger.info(f"AI WebSocket disconnected: session={self.session_id}")
    
    async def receive(self, text_data):
        """Process incoming AI processing requests"""
        start_time = time.time()
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'process')
            
            handlers = {
                'generate_content': self.handle_content_generation,
                'optimize_prompt': self.handle_prompt_optimization,
                'analyze_sentiment': self.handle_sentiment_analysis,
                'extract_keywords': self.handle_keyword_extraction,
                'summarize': self.handle_summarization,
                'translate': self.handle_translation,
                'ping': self.handle_ping
            }
            
            handler = handlers.get(message_type)
            if handler:
                await handler(data)
            else:
                await self._send_error(f"Unknown AI operation: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            await self._send_error("AI processing failed")
    
    async def handle_content_generation(self, data: Dict[str, Any]):
        """Handle content generation requests"""
        try:
            prompt = data.get('prompt', '').strip()
            content_type = data.get('content_type', 'general')
            max_length = min(data.get('max_length', 500), 2000)
            
            if not prompt:
                await self._send_error("Prompt required for content generation")
                return
            
            # Send processing status
            await self.send(text_data=json.dumps({
                'type': 'processing_started',
                'operation': 'content_generation',
                'prompt': prompt[:100] + '...' if len(prompt) > 100 else prompt
            }))
            
            # Simulate AI processing (replace with actual AI service)
            generated_content = await self._generate_content(prompt, content_type, max_length)
            
            await self.send(text_data=json.dumps({
                'type': 'content_generated',
                'original_prompt': prompt,
                'generated_content': generated_content,
                'content_type': content_type,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            await self._send_error("Content generation failed")
    
    async def handle_prompt_optimization(self, data: Dict[str, Any]):
        """Handle prompt optimization requests"""
        try:
            original_prompt = data.get('prompt', '').strip()
            optimization_goals = data.get('goals', ['clarity', 'effectiveness'])
            
            if not original_prompt:
                await self._send_error("Original prompt required")
                return
            
            await self.send(text_data=json.dumps({
                'type': 'optimization_started',
                'original_prompt': original_prompt
            }))
            
            # Optimize prompt
            optimization_result = await self._optimize_prompt(original_prompt, optimization_goals)
            
            await self.send(text_data=json.dumps({
                'type': 'prompt_optimized',
                'original_prompt': original_prompt,
                'optimized_prompt': optimization_result['optimized'],
                'improvements': optimization_result['improvements'],
                'score_improvement': optimization_result['score_improvement'],
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Prompt optimization error: {e}")
            await self._send_error("Prompt optimization failed")
    
    async def handle_sentiment_analysis(self, data: Dict[str, Any]):
        """Handle sentiment analysis requests"""
        try:
            text = data.get('text', '').strip()
            
            if not text:
                await self._send_error("Text required for sentiment analysis")
                return
            
            sentiment_result = await self._analyze_sentiment(text)
            
            await self.send(text_data=json.dumps({
                'type': 'sentiment_analyzed',
                'text': text[:200] + '...' if len(text) > 200 else text,
                'sentiment': sentiment_result['sentiment'],
                'confidence': sentiment_result['confidence'],
                'emotions': sentiment_result['emotions'],
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            await self._send_error("Sentiment analysis failed")
    
    async def handle_keyword_extraction(self, data: Dict[str, Any]):
        """Handle keyword extraction requests"""
        try:
            text = data.get('text', '').strip()
            max_keywords = min(data.get('max_keywords', 10), 20)
            
            if not text:
                await self._send_error("Text required for keyword extraction")
                return
            
            keywords = await self._extract_keywords(text, max_keywords)
            
            await self.send(text_data=json.dumps({
                'type': 'keywords_extracted',
                'text_length': len(text),
                'keywords': keywords,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            await self._send_error("Keyword extraction failed")
    
    async def handle_summarization(self, data: Dict[str, Any]):
        """Handle text summarization requests"""
        try:
            text = data.get('text', '').strip()
            summary_length = data.get('summary_length', 'medium')  # short, medium, long
            
            if not text:
                await self._send_error("Text required for summarization")
                return
            
            if len(text) < 100:
                await self._send_error("Text too short for meaningful summarization")
                return
            
            summary = await self._summarize_text(text, summary_length)
            
            await self.send(text_data=json.dumps({
                'type': 'text_summarized',
                'original_length': len(text),
                'summary': summary,
                'summary_length': summary_length,
                'compression_ratio': round(len(summary) / len(text), 2),
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            await self._send_error("Text summarization failed")
    
    async def handle_translation(self, data: Dict[str, Any]):
        """Handle translation requests"""
        try:
            text = data.get('text', '').strip()
            target_language = data.get('target_language', 'en')
            source_language = data.get('source_language', 'auto')
            
            if not text:
                await self._send_error("Text required for translation")
                return
            
            translation_result = await self._translate_text(text, source_language, target_language)
            
            await self.send(text_data=json.dumps({
                'type': 'text_translated',
                'original_text': text,
                'translated_text': translation_result['translated'],
                'source_language': translation_result['detected_language'],
                'target_language': target_language,
                'confidence': translation_result['confidence'],
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            await self._send_error("Translation failed")
    
    async def handle_ping(self, data: Dict[str, Any]):
        """Handle ping for connection health"""
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'ai_status': 'operational',
            'timestamp': timezone.now().isoformat()
        }))
    
    # AI Processing Methods (implement with actual AI services)
    
    async def _generate_content(self, prompt: str, content_type: str, max_length: int) -> str:
        """Generate content using AI (placeholder implementation)"""
        # Simulate processing delay
        await asyncio.sleep(0.5)
        
        templates = {
            'general': f"Generated content based on: {prompt}",
            'marketing': f"Compelling marketing copy: {prompt}",
            'technical': f"Technical documentation for: {prompt}",
            'creative': f"Creative narrative: {prompt}"
        }
        
        base_content = templates.get(content_type, templates['general'])
        return base_content[:max_length]
    
    async def _optimize_prompt(self, prompt: str, goals: List[str]) -> Dict[str, Any]:
        """Optimize prompt using AI (placeholder implementation)"""
        await asyncio.sleep(0.3)
        
        improvements = []
        score_improvement = 0.0
        
        if 'clarity' in goals:
            improvements.append("Improved clarity and specificity")
            score_improvement += 0.2
        
        if 'effectiveness' in goals:
            improvements.append("Enhanced effectiveness and actionability")
            score_improvement += 0.15
        
        optimized = f"OPTIMIZED: {prompt} [with improved clarity and effectiveness]"
        
        return {
            'optimized': optimized,
            'improvements': improvements,
            'score_improvement': score_improvement
        }
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment (placeholder implementation)"""
        await asyncio.sleep(0.2)
        
        # Simple keyword-based sentiment analysis
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.6 + (positive_count - negative_count) * 0.1, 0.95)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(0.6 + (negative_count - positive_count) * 0.1, 0.95)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'emotions': ['analytical'] if 'analysis' in text_lower else ['general']
        }
    
    async def _extract_keywords(self, text: str, max_keywords: int) -> List[Dict[str, Any]]:
        """Extract keywords (placeholder implementation)"""
        await asyncio.sleep(0.2)
        
        # Simple frequency-based keyword extraction
        words = text.lower().split()
        word_freq = {}
        
        # Filter out common words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'a', 'an'}
        
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if len(clean_word) > 3 and clean_word not in stop_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:max_keywords]
        
        return [
            {'keyword': word, 'frequency': freq, 'relevance': min(freq / len(words) * 10, 1.0)}
            for word, freq in sorted_keywords
        ]
    
    async def _summarize_text(self, text: str, length: str) -> str:
        """Summarize text (placeholder implementation)"""
        await asyncio.sleep(0.4)
        
        # Simple extractive summarization
        sentences = text.split('.')
        
        length_ratios = {
            'short': 0.2,
            'medium': 0.4,
            'long': 0.6
        }
        
        ratio = length_ratios.get(length, 0.4)
        summary_length = max(1, int(len(sentences) * ratio))
        
        # Take first few sentences as summary (in real implementation, use proper algorithms)
        summary_sentences = sentences[:summary_length]
        return '. '.join(summary_sentences) + '.'
    
    async def _translate_text(self, text: str, source_lang: str, target_lang: str) -> Dict[str, Any]:
        """Translate text (placeholder implementation)"""
        await asyncio.sleep(0.3)
        
        # Placeholder translation
        return {
            'translated': f"[TRANSLATED TO {target_lang.upper()}]: {text}",
            'detected_language': source_lang if source_lang != 'auto' else 'en',
            'confidence': 0.85
        }
    
    async def _send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'ai_error',
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }))


class SearchConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time search with AI enhancement"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.user = None
        self.room_group_name = None
        
    async def connect(self):
        """Handle search WebSocket connection"""
        try:
            self.session_id = self.scope['url_route']['kwargs'].get('session_id')
            if not self.session_id:
                await self.close()
                return
                
            if self.scope["user"].is_authenticated:
                self.user = self.scope["user"]
                
            self.room_group_name = f'search_{self.session_id}'
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            await self.send(text_data=json.dumps({
                'type': 'search_connection_established',
                'session_id': self.session_id,
                'timestamp': timezone.now().isoformat(),
                'features': ['real_time_search', 'ai_suggestions', 'semantic_search']
            }))
            
        except Exception as e:
            logger.error(f"Search WebSocket connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle search WebSocket disconnection"""
        if self.room_group_name:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Process search requests"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'search')
            
            if message_type == 'real_time_search':
                await self.handle_real_time_search(data)
            elif message_type == 'get_suggestions':
                await self.handle_get_suggestions(data)
            elif message_type == 'semantic_search':
                await self.handle_semantic_search(data)
            else:
                await self._send_error(f"Unknown search operation: {message_type}")
                
        except Exception as e:
            logger.error(f"Search processing error: {e}")
            await self._send_error("Search processing failed")
    
    async def handle_real_time_search(self, data: Dict[str, Any]):
        """Handle real-time search as user types"""
        try:
            query = data.get('query', '').strip()
            
            if len(query) < 2:
                return  # Too short for meaningful search
            
            # Import here to avoid circular imports
            from apps.templates.search_services import search_service
            
            # Perform search
            results, metrics = await asyncio.get_event_loop().run_in_executor(
                None, 
                search_service.search_prompts,
                query, None, None, 10, self.session_id
            )
            
            # Format for WebSocket
            formatted_results = [
                {
                    'id': str(result.prompt.id),
                    'title': result.prompt.title,
                    'content': result.prompt.content[:300],
                    'score': result.score,
                    'category': result.prompt.category
                }
                for result in results[:5]  # Limit for real-time
            ]
            
            await self.send(text_data=json.dumps({
                'type': 'real_time_results',
                'query': query,
                'results': formatted_results,
                'search_time_ms': metrics.get('total_time_ms', 0),
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Real-time search error: {e}")
    
    async def handle_semantic_search(self, data: Dict[str, Any]):
        """Handle AI-powered semantic search"""
        try:
            query = data.get('query', '').strip()
            
            if not query:
                await self._send_error("Query required for semantic search")
                return
            
            # Placeholder for semantic search implementation
            # In production, this would use embeddings and vector similarity
            
            await self.send(text_data=json.dumps({
                'type': 'semantic_results',
                'query': query,
                'message': 'Semantic search will be available with vector embeddings',
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
    
    async def handle_get_suggestions(self, data: Dict[str, Any]):
        """Provide search suggestions"""
        try:
            partial_query = data.get('query', '').strip()
            
            if len(partial_query) < 2:
                return
            
            # Generate suggestions based on popular searches and cache
            suggestions = await self._get_search_suggestions(partial_query)
            
            await self.send(text_data=json.dumps({
                'type': 'search_suggestions',
                'query': partial_query,
                'suggestions': suggestions,
                'timestamp': timezone.now().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Search suggestions error: {e}")
    
    async def _get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        # Simple implementation - in production, use more sophisticated methods
        common_searches = [
            "write a professional email",
            "create marketing copy",
            "technical documentation",
            "creative writing prompts",
            "data analysis prompts",
            "business proposal template",
            "social media content",
            "educational materials"
        ]
        
        suggestions = [
            s for s in common_searches 
            if partial_query.lower() in s.lower()
        ]
        
        return suggestions[:5]
    
    async def _send_error(self, error_message: str):
        """Send error message to client"""
        await self.send(text_data=json.dumps({
            'type': 'search_error',
            'message': error_message,
            'timestamp': timezone.now().isoformat()
        }))


class AnalyticsConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time analytics and insights"""
    
    async def connect(self):
        """Handle analytics WebSocket connection"""
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'analytics_connected',
            'message': 'Real-time analytics will be available soon',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Handle analytics disconnection"""
        pass
    
    async def receive(self, text_data):
        """Handle analytics requests"""
        await self.send(text_data=json.dumps({
            'type': 'analytics_placeholder',
            'message': 'Analytics features coming soon',
            'timestamp': timezone.now().isoformat()
        }))


class AIStreamingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for streaming AI responses"""
    
    async def connect(self):
        """Handle streaming connection"""
        await self.accept()
        
        await self.send(text_data=json.dumps({
            'type': 'streaming_connected',
            'message': 'AI streaming ready',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def disconnect(self, close_code):
        """Handle streaming disconnection"""
        pass
    
    async def receive(self, text_data):
        """Handle streaming requests"""
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'stream_content':
                await self.handle_stream_generation(data)
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
    
    async def handle_stream_generation(self, data: Dict[str, Any]):
        """Handle streaming content generation"""
        prompt = data.get('prompt', '')
        
        # Simulate streaming response
        response_parts = [
            "Generating your content...",
            "Processing requirements...",
            "Creating optimized output...",
            f"Final result based on: {prompt}"
        ]
        
        for i, part in enumerate(response_parts):
            await asyncio.sleep(0.5)  # Simulate processing delay
            
            await self.send(text_data=json.dumps({
                'type': 'stream_chunk',
                'chunk': part,
                'chunk_index': i,
                'is_final': i == len(response_parts) - 1,
                'timestamp': timezone.now().isoformat()
            }))