"""
Fallback AI services when LangChain is not available
Provides basic functionality for development and testing
"""

import time
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass 
class MockOptimizationResult:
    """Mock result structure for prompt optimization"""
    optimized_content: str
    improvements: List[str]
    similarity_score: float
    relevance_score: float
    processing_time_ms: int
    model_used: str
    confidence: float

class MockLangChainService:
    """Mock LangChain service for when dependencies are not available"""
    
    def __init__(self):
        logger.info("Using mock LangChain service (dependencies not available)")
        
    async def process_intent(self, query: str) -> Dict[str, Any]:
        """Mock intent processing"""
        await asyncio.sleep(0.1)  # Simulate processing
        
        # Simple keyword-based intent classification
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["write", "create", "draft", "compose"]):
            category = "content_creation"
            confidence = 0.7
        elif any(word in query_lower for word in ["email", "message", "letter", "communication"]):
            category = "communication"
            confidence = 0.7
        elif any(word in query_lower for word in ["technical", "documentation", "code", "programming"]):
            category = "technical_writing"
            confidence = 0.7
        elif any(word in query_lower for word in ["analyze", "analysis", "research", "data"]):
            category = "analysis"
            confidence = 0.6
        elif any(word in query_lower for word in ["creative", "story", "brainstorm", "idea"]):
            category = "creative"
            confidence = 0.6
        else:
            category = "general"
            confidence = 0.5
            
        return {
            "processed_data": {
                "category": category,
                "confidence": confidence,
                "keywords": query.split()[:5],
                "context": f"Mock classification for: {query[:50]}..."
            },
            "category": category,
            "confidence": confidence,
            "keywords": query.split()[:5],
            "context": f"Mock intent processing - detected {category}",
            "processing_time_ms": 100
        }
    
    async def optimize_prompt(
        self,
        original_prompt,
        user_intent=None,
        context: Dict = None,
        optimization_type: str = "enhancement"
    ) -> MockOptimizationResult:
        """Mock prompt optimization"""
        await asyncio.sleep(0.3)  # Simulate processing
        
        improvements = [
            "Enhanced clarity and specificity",
            "Improved structure and flow",
            "Added actionable elements"
        ]
        
        # Simple optimization - add prefix and structure
        optimized_content = f"[OPTIMIZED] {original_prompt.content}\n\nKey improvements:\n"
        optimized_content += "\n".join(f"• {imp}" for imp in improvements)
        
        return MockOptimizationResult(
            optimized_content=optimized_content,
            improvements=improvements,
            similarity_score=0.8,
            relevance_score=0.7,
            processing_time_ms=300,
            model_used="mock-optimizer",
            confidence=0.6
        )
    
    async def generate_response(self, user_message: str, user_intent=None) -> Dict:
        """Mock response generation"""
        await asyncio.sleep(0.2)
        
        responses = {
            "hello": "Hello! I'm here to help you with prompt optimization and content creation.",
            "help": "I can help you optimize prompts, create content, and provide suggestions.",
            "search": "I can help you search for relevant prompts and templates.",
            "optimize": "I can optimize your prompts for better clarity and effectiveness."
        }
        
        # Find matching response
        message_lower = user_message.lower()
        response = "I understand you're looking for assistance. While I'm in mock mode, I can help with basic prompt optimization and suggestions."
        
        for key, value in responses.items():
            if key in message_lower:
                response = value
                break
        
        return {
            "content": response,
            "confidence": 0.6,
            "suggestions": [
                "Try asking about prompt optimization",
                "Ask for template suggestions",
                "Request content creation help"
            ],
            "processing_time_ms": 200
        }

# Export the mock service
MockLangChainOptimizationService = MockLangChainService