"""
Enhanced LangChain Service for Template-Aware AI Processing
Integrates LangChain with template creation and optimization workflows
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

from django.conf import settings
from django.core.cache import cache

# LangChain imports
try:
    from langchain.llms import OpenAI
    from langchain.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage, AIMessage
    from langchain.prompts import ChatPromptTemplate, PromptTemplate
    from langchain.chains import LLMChain, ConversationChain
    from langchain.memory import ConversationBufferMemory
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.agents import initialize_agent, AgentType
    from langchain.tools import Tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class TemplateAwareLangChainService:
    """
    LangChain service with template creation and optimization capabilities
    """
    
    def __init__(self):
        self.enabled = LANGCHAIN_AVAILABLE and self._check_api_keys()
        self.llm = None
        self.chat_model = None
        self.embeddings = None
        self.memory = {}  # Session-based memory
        self._initialize_models()
        
        # Template-specific prompts
        self.template_analysis_prompt = self._create_template_analysis_prompt()
        self.template_generation_prompt = self._create_template_generation_prompt()
        self.prompt_optimization_prompt = self._create_prompt_optimization_prompt()
    
    def _check_api_keys(self) -> bool:
        """Check if required API keys are available"""
        langchain_settings = getattr(settings, 'LANGCHAIN_SETTINGS', {})
        openai_key = langchain_settings.get('OPENAI_API_KEY')
        deepseek_key = langchain_settings.get('DEEPSEEK_API_KEY')
        
        return bool(openai_key or deepseek_key)
    
    def _initialize_models(self):
        """Initialize LangChain models"""
        try:
            if not self.enabled:
                return
            
            langchain_settings = getattr(settings, 'LANGCHAIN_SETTINGS', {})
            
            # Try OpenAI first, then fallback to other models
            if langchain_settings.get('OPENAI_API_KEY'):
                self.llm = OpenAI(
                    openai_api_key=langchain_settings['OPENAI_API_KEY'],
                    temperature=0.7,
                    max_tokens=1000
                )
                self.chat_model = ChatOpenAI(
                    openai_api_key=langchain_settings['OPENAI_API_KEY'],
                    temperature=0.7,
                    model_name="gpt-3.5-turbo"
                )
                self.embeddings = OpenAIEmbeddings(
                    openai_api_key=langchain_settings['OPENAI_API_KEY']
                )
                
            logger.info("LangChain models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChain models: {e}")
            self.enabled = False
    
    def _create_template_analysis_prompt(self) -> PromptTemplate:
        """Create prompt template for analyzing conversations for template potential"""
        return PromptTemplate(
            input_variables=["conversation", "user_intent"],
            template="""
            Analyze the following conversation to determine if it would make a good reusable template:
            
            Conversation:
            {conversation}
            
            User Intent: {user_intent}
            
            Please analyze:
            1. Is this conversation suitable for creating a reusable template?
            2. What would be the main template category (Writing, Business, Marketing, etc.)?
            3. What key fields/variables should be extractable?
            4. What would be a good title for this template?
            5. How confident are you this would be useful as a template (0-1)?
            
            Respond in JSON format:
            {{
                "suitable_for_template": boolean,
                "confidence": float,
                "suggested_title": string,
                "suggested_category": string,
                "suggested_fields": [list of field objects],
                "reasoning": string
            }}
            """
        )
    
    def _create_template_generation_prompt(self) -> PromptTemplate:
        """Create prompt template for generating templates from conversations"""
        return PromptTemplate(
            input_variables=["conversation", "title", "category"],
            template="""
            Convert the following conversation into a reusable template:
            
            Conversation:
            {conversation}
            
            Template Title: {title}
            Category: {category}
            
            Create a template that:
            1. Extracts the main structure and pattern from the conversation
            2. Identifies variable fields that users can customize
            3. Provides clear instructions and examples
            4. Maintains the effective elements from the original conversation
            
            Generate:
            1. Template content with placeholders for variables
            2. Field definitions (name, type, placeholder, required)
            3. Usage instructions
            4. Example values
            
            Respond in JSON format:
            {{
                "template_content": string,
                "fields": [{{
                    "name": string,
                    "label": string,
                    "type": string,
                    "placeholder": string,
                    "required": boolean,
                    "description": string
                }}],
                "instructions": string,
                "examples": [string],
                "tags": [string]
            }}
            """
        )
    
    def _create_prompt_optimization_prompt(self) -> PromptTemplate:
        """Create prompt template for optimizing user prompts"""
        return PromptTemplate(
            input_variables=["original_prompt", "context", "goal"],
            template="""
            Optimize the following prompt to make it more effective:
            
            Original Prompt:
            {original_prompt}
            
            Context: {context}
            Goal: {goal}
            
            Please optimize by:
            1. Making the prompt more specific and clear
            2. Adding context where helpful
            3. Structuring it for better AI responses
            4. Maintaining the original intent
            5. Making it more actionable
            
            Provide:
            1. Optimized prompt
            2. List of improvements made
            3. Explanation of changes
            4. Alternative variations
            
            Respond in JSON format:
            {{
                "optimized_prompt": string,
                "improvements": [string],
                "explanation": string,
                "alternatives": [string],
                "confidence": float
            }}
            """
        )
    
    async def analyze_conversation_for_template(self, conversation: List[Dict], user_intent: str = "") -> Dict[str, Any]:
        """Analyze conversation to determine template potential"""
        try:
            if not self.enabled:
                return self._fallback_conversation_analysis(conversation)
            
            # Format conversation for analysis
            conversation_text = self._format_conversation_for_analysis(conversation)
            
            # Run analysis
            chain = LLMChain(llm=self.llm, prompt=self.template_analysis_prompt)
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                chain.run, 
                {
                    "conversation": conversation_text,
                    "user_intent": user_intent
                }
            )
            
            # Parse JSON response
            try:
                analysis = json.loads(result.strip())
                return analysis
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LangChain analysis response: {result}")
                return self._fallback_conversation_analysis(conversation)
            
        except Exception as e:
            logger.error(f"LangChain conversation analysis error: {e}")
            return self._fallback_conversation_analysis(conversation)
    
    async def generate_template_from_conversation(self, conversation: List[Dict], title: str, category: str) -> Dict[str, Any]:
        """Generate a structured template from conversation"""
        try:
            if not self.enabled:
                return self._fallback_template_generation(conversation, title, category)
            
            conversation_text = self._format_conversation_for_analysis(conversation)
            
            chain = LLMChain(llm=self.llm, prompt=self.template_generation_prompt)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                chain.run,
                {
                    "conversation": conversation_text,
                    "title": title,
                    "category": category
                }
            )
            
            try:
                template_data = json.loads(result.strip())
                return template_data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse template generation response: {result}")
                return self._fallback_template_generation(conversation, title, category)
            
        except Exception as e:
            logger.error(f"LangChain template generation error: {e}")
            return self._fallback_template_generation(conversation, title, category)
    
    async def optimize_prompt(self, original_prompt: str, context: Dict[str, Any] = None, goal: str = "") -> Dict[str, Any]:
        """Optimize a user prompt for better AI responses"""
        try:
            if not self.enabled:
                return self._fallback_prompt_optimization(original_prompt)
            
            context_str = json.dumps(context) if context else "No additional context"
            
            chain = LLMChain(llm=self.llm, prompt=self.prompt_optimization_prompt)
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                chain.run,
                {
                    "original_prompt": original_prompt,
                    "context": context_str,
                    "goal": goal or "General improvement"
                }
            )
            
            try:
                optimization_result = json.loads(result.strip())
                return optimization_result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse optimization response: {result}")
                return self._fallback_prompt_optimization(original_prompt)
            
        except Exception as e:
            logger.error(f"LangChain prompt optimization error: {e}")
            return self._fallback_prompt_optimization(original_prompt)
    
    async def process_intent(self, query: str) -> Dict[str, Any]:
        """Process user intent with LangChain"""
        try:
            if not self.enabled:
                return self._fallback_intent_processing(query)
            
            # Simple intent analysis using LangChain
            prompt = f"""
            Analyze the following user query and determine:
            1. Primary intent/goal
            2. Category (Writing, Business, Marketing, Education, Technology, Creative, General)
            3. Key entities/topics mentioned
            4. Suggested next actions
            5. Template recommendations if applicable
            
            Query: {query}
            
            Respond in JSON format with: intent, category, entities, suggestions, template_recommendations
            """
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.llm,
                prompt
            )
            
            try:
                intent_data = json.loads(result.strip())
                return intent_data
            except json.JSONDecodeError:
                return self._fallback_intent_processing(query)
            
        except Exception as e:
            logger.error(f"LangChain intent processing error: {e}")
            return self._fallback_intent_processing(query)
    
    async def get_template_suggestions(self, user_history: List[Dict], current_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get AI-powered template suggestions based on user history and context"""
        try:
            if not self.enabled:
                return self._fallback_template_suggestions()
            
            # Analyze user patterns and suggest relevant templates
            history_text = json.dumps(user_history[-10:])  # Last 10 interactions
            context_text = json.dumps(current_context)
            
            prompt = f"""
            Based on user history and current context, suggest relevant templates:
            
            User History: {history_text}
            Current Context: {context_text}
            
            Suggest 3-5 templates that would be most helpful, including:
            1. Template title and description
            2. Why it's relevant to the user
            3. Expected benefits
            4. Confidence score
            
            Respond in JSON format with array of suggestions.
            """
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self.llm,
                prompt
            )
            
            try:
                suggestions = json.loads(result.strip())
                return suggestions if isinstance(suggestions, list) else []
            except json.JSONDecodeError:
                return self._fallback_template_suggestions()
            
        except Exception as e:
            logger.error(f"LangChain template suggestions error: {e}")
            return self._fallback_template_suggestions()
    
    def _format_conversation_for_analysis(self, conversation: List[Dict]) -> str:
        """Format conversation for LangChain processing"""
        formatted = []
        for msg in conversation:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            formatted.append(f"[{role.upper()}] {content}")
        
        return "\n".join(formatted)
    
    def _fallback_conversation_analysis(self, conversation: List[Dict]) -> Dict[str, Any]:
        """Fallback analysis when LangChain is not available"""
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        # Simple heuristic analysis
        total_length = sum(len(msg.get('content', '')) for msg in conversation)
        has_structure = len(user_messages) >= 2
        
        return {
            "suitable_for_template": has_structure and total_length > 100,
            "confidence": 0.6 if has_structure else 0.3,
            "suggested_title": user_messages[0].get('content', '')[:50] + "..." if user_messages else "Conversation Template",
            "suggested_category": "General",
            "suggested_fields": [
                {
                    "name": "main_input",
                    "label": "Main Input",
                    "type": "textarea",
                    "placeholder": "Enter your main request here...",
                    "required": True,
                    "description": "Primary input field"
                }
            ],
            "reasoning": "Basic analysis based on conversation length and structure"
        }
    
    def _fallback_template_generation(self, conversation: List[Dict], title: str, category: str) -> Dict[str, Any]:
        """Fallback template generation"""
        content_parts = []
        fields = []
        
        user_messages = [msg for msg in conversation if msg.get('role') == 'user']
        
        for i, msg in enumerate(user_messages):
            content = msg.get('content', '')
            content_parts.append(f"**Step {i+1}:** {{user_input_{i+1}}}")
            fields.append({
                "name": f"user_input_{i+1}",
                "label": f"Input {i+1}",
                "type": "textarea",
                "placeholder": content[:100] + "..." if len(content) > 100 else content,
                "required": True,
                "description": f"User input for step {i+1}"
            })
        
        return {
            "template_content": "\n\n".join(content_parts),
            "fields": fields,
            "instructions": f"Fill in the fields below to use this {category.lower()} template",
            "examples": [msg.get('content', '')[:100] for msg in user_messages[:2]],
            "tags": [category.lower(), "conversation", "generated"]
        }
    
    def _fallback_prompt_optimization(self, original_prompt: str) -> Dict[str, Any]:
        """Fallback prompt optimization"""
        return {
            "optimized_prompt": f"Please help me with the following: {original_prompt}",
            "improvements": ["Added polite request structure", "Made more explicit"],
            "explanation": "Basic optimization applied - added politeness and clarity",
            "alternatives": [
                f"I need assistance with: {original_prompt}",
                f"Could you help me understand: {original_prompt}",
                f"Please provide guidance on: {original_prompt}"
            ],
            "confidence": 0.5
        }
    
    def _fallback_intent_processing(self, query: str) -> Dict[str, Any]:
        """Fallback intent processing"""
        query_lower = query.lower()
        
        # Simple keyword-based categorization
        categories = {
            'writing': ['write', 'essay', 'article', 'content', 'blog'],
            'business': ['business', 'strategy', 'plan', 'proposal'],
            'marketing': ['marketing', 'campaign', 'social', 'brand'],
            'education': ['learn', 'teach', 'study', 'course'],
            'technology': ['code', 'program', 'software', 'tech'],
            'creative': ['creative', 'design', 'art', 'brainstorm']
        }
        
        detected_category = 'general'
        for category, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_category = category
                break
        
        return {
            "intent": "assistance_request",
            "category": detected_category.title(),
            "entities": [],
            "suggestions": [f"I can help you with {detected_category} tasks"],
            "template_recommendations": [],
            "confidence": 0.5
        }
    
    def _fallback_template_suggestions(self) -> List[Dict[str, Any]]:
        """Fallback template suggestions"""
        return [
            {
                "title": "General Purpose Template",
                "description": "A versatile template for various tasks",
                "relevance": "Good starting point for any project",
                "confidence": 0.5
            },
            {
                "title": "Writing Assistant Template",
                "description": "Help with writing tasks and content creation",
                "relevance": "Useful for content creation needs",
                "confidence": 0.4
            }
        ]

# Service instance
_langchain_service = None

def get_langchain_service() -> TemplateAwareLangChainService:
    """Get singleton LangChain service instance"""
    global _langchain_service
    if _langchain_service is None:
        _langchain_service = TemplateAwareLangChainService()
    return _langchain_service