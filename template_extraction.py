# apps/ai_services/template_extraction.py
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from django.conf import settings
from django.utils import timezone

# LangChain imports
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    from langchain.llms.base import LLM
    from langchain.embeddings import OpenAIEmbeddings
    from langchain.vectorstores import FAISS
    from langchain_community.llms import DeepSeek
except ImportError:
    # Fallback for basic functionality
    pass

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTemplateData:
    """Data class for extracted template information"""
    title: str
    description: str
    template_content: str
    category: str
    keywords: List[str]
    use_cases: List[str]
    confidence_score: float
    quality_rating: str
    extraction_method: str
    metadata: Dict[str, Any]


class TemplateExtractor:
    """Advanced template extraction using LangChain and AI analysis"""
    
    def __init__(self):
        self.setup_langchain()
        self.setup_extraction_rules()
        
    def setup_langchain(self):
        """Initialize LangChain components"""
        try:
            # Initialize DeepSeek LLM for analysis
            self.llm = DeepSeek(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                model="deepseek-chat",
                temperature=0.1  # Low temperature for consistent analysis
            )
            
            # Text splitter for large content
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=2000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Embeddings for similarity analysis
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
                self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
            else:
                self.embeddings = None
                
        except Exception as e:
            logger.error(f"Failed to initialize LangChain components: {e}")
            self.llm = None
            self.text_splitter = None
            self.embeddings = None
    
    def setup_extraction_rules(self):
        """Setup pattern-based extraction rules"""
        self.template_patterns = [
            # Numbered list patterns
            {
                'name': 'numbered_prompts',
                'pattern': r'\*?\*?\s*(\d+\.)\s*(.+?)(?=\n\s*\*?\*?\s*\d+\.|\n\n|\Z)',
                'confidence': 0.8,
                'category': 'structured_prompts'
            },
            # Bullet point patterns
            {
                'name': 'bullet_prompts',
                'pattern': r'\*\s*\*?\*?(.+?)\*?\*?\s*(.+?)(?=\n\s*\*|\n\n|\Z)',
                'confidence': 0.7,
                'category': 'bullet_prompts'
            },
            # Act as patterns
            {
                'name': 'act_as_prompts',
                'pattern': r'(Act as|You are|As a|Role:|Persona:)\s*(.+?)(?=\n\n|\Z)',
                'confidence': 0.9,
                'category': 'role_playing'
            },
            # Template with placeholders
            {
                'name': 'placeholder_templates',
                'pattern': r'(.+?\[.+?\].+?)(?=\n\n|\Z)',
                'confidence': 0.85,
                'category': 'fill_in_templates'
            },
            # Question-based prompts
            {
                'name': 'question_prompts',
                'pattern': r'((?:What|How|Why|When|Where|Which|Who).+?\?)(?=\n|\Z)',
                'confidence': 0.6,
                'category': 'questions'
            }
        ]
        
        # High-value keywords that indicate quality templates
        self.quality_keywords = [
            'monetization', 'business', 'strategy', 'marketing', 'sales',
            'revenue', 'profit', 'conversion', 'funnel', 'optimization',
            'analysis', 'research', 'planning', 'development', 'growth',
            'content', 'copywriting', 'persuasion', 'psychology', 'targeting'
        ]
        
        # Category mappings
        self.category_mappings = {
            'business': ['business', 'monetization', 'revenue', 'profit', 'sales'],
            'marketing': ['marketing', 'advertising', 'campaign', 'promotion', 'brand'],
            'content': ['content', 'copywriting', 'writing', 'blog', 'article'],
            'analysis': ['analysis', 'research', 'data', 'insights', 'metrics'],
            'strategy': ['strategy', 'planning', 'roadmap', 'goals', 'objectives'],
            'creative': ['creative', 'ideation', 'brainstorm', 'innovation', 'design'],
            'technical': ['technical', 'development', 'coding', 'programming', 'software'],
            'personal': ['personal', 'productivity', 'habits', 'self-improvement', 'goals']
        }
    
    def extract_templates_from_text(self, text: str, source_info: Dict[str, Any] = None) -> List[ExtractedTemplateData]:
        """Main method to extract templates from text"""
        templates = []
        
        # Method 1: Pattern-based extraction
        pattern_templates = self._extract_by_patterns(text)
        templates.extend(pattern_templates)
        
        # Method 2: LangChain AI analysis (if available)
        if self.llm:
            ai_templates = self._extract_by_ai_analysis(text)
            templates.extend(ai_templates)
        
        # Method 3: Semantic analysis (if embeddings available)
        if self.embeddings:
            semantic_templates = self._extract_by_semantic_analysis(text)
            templates.extend(semantic_templates)
        
        # Deduplicate and enhance templates
        templates = self._deduplicate_templates(templates)
        templates = self._enhance_templates(templates)
        
        # Filter by quality and confidence
        templates = self._filter_quality_templates(templates)
        
        return templates
    
    def _extract_by_patterns(self, text: str) -> List[ExtractedTemplateData]:
        """Extract templates using regex patterns"""
        templates = []
        
        for pattern_config in self.template_patterns:
            pattern = pattern_config['pattern']
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                try:
                    if pattern_config['name'] == 'numbered_prompts':
                        number = match.group(1).strip()
                        content = match.group(2).strip()
                        title = f"Prompt Template {number.rstrip('.')}"
                    elif pattern_config['name'] == 'bullet_prompts':
                        content = f"{match.group(1).strip()} {match.group(2).strip()}"
                        title = self._generate_title_from_content(content)
                    elif pattern_config['name'] == 'act_as_prompts':
                        role_indicator = match.group(1)
                        content = f"{role_indicator} {match.group(2).strip()}"
                        title = f"Role: {match.group(2).strip()[:50]}"
                    else:
                        content = match.group(0).strip()
                        title = self._generate_title_from_content(content)
                    
                    if len(content) < 20:  # Skip very short content
                        continue
                        
                    template = ExtractedTemplateData(
                        title=title,
                        description=self._generate_description(content),
                        template_content=content,
                        category=pattern_config['category'],
                        keywords=self._extract_keywords(content),
                        use_cases=self._generate_use_cases(content),
                        confidence_score=pattern_config['confidence'],
                        quality_rating=self._assess_quality(content),
                        extraction_method='pattern',
                        metadata={'pattern_name': pattern_config['name']}
                    )
                    
                    templates.append(template)
                    
                except Exception as e:
                    logger.error(f"Error extracting with pattern {pattern_config['name']}: {e}")
                    continue
        
        return templates
    
    def _extract_by_ai_analysis(self, text: str) -> List[ExtractedTemplateData]:
        """Extract templates using AI analysis with LangChain"""
        if not self.llm:
            return []
        
        templates = []
        
        try:
            # Split text into manageable chunks
            chunks = self.text_splitter.split_text(text)
            
            for chunk in chunks:
                # Create prompt for template extraction
                extraction_prompt = PromptTemplate(
                    input_variables=["text"],
                    template="""
                    Analyze the following text and extract high-quality prompt templates that could be valuable for users:
                    
                    Text: {text}
                    
                    For each template you find, provide:
                    1. A clear title (max 100 characters)
                    2. A description of what it does (max 200 characters)
                    3. The exact template content
                    4. Suggested category
                    5. Key use cases (max 3)
                    6. Quality score (0-1)
                    7. Confidence score (0-1)
                    
                    Focus on templates that are:
                    - Clear and actionable
                    - Professionally useful
                    - Well-structured
                    - Have commercial or business value
                    
                    Return results as JSON array with this structure:
                    {{
                        "templates": [
                            {{
                                "title": "Template Title",
                                "description": "Template description",
                                "content": "Full template content",
                                "category": "business/marketing/content/etc",
                                "use_cases": ["use case 1", "use case 2"],
                                "quality_score": 0.8,
                                "confidence_score": 0.9
                            }}
                        ]
                    }}
                    """
                )
                
                # Create chain and run
                chain = LLMChain(llm=self.llm, prompt=extraction_prompt)
                result = chain.run(text=chunk)
                
                # Parse AI response
                ai_templates = self._parse_ai_response(result)
                templates.extend(ai_templates)
                
        except Exception as e:
            logger.error(f"Error in AI analysis extraction: {e}")
        
        return templates
    
    def _parse_ai_response(self, response: str) -> List[ExtractedTemplateData]:
        """Parse AI response and convert to ExtractedTemplateData objects"""
        templates = []
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                
                for template_data in data.get('templates', []):
                    template = ExtractedTemplateData(
                        title=template_data.get('title', 'AI Extracted Template'),
                        description=template_data.get('description', ''),
                        template_content=template_data.get('content', ''),
                        category=template_data.get('category', 'general'),
                        keywords=self._extract_keywords(template_data.get('content', '')),
                        use_cases=template_data.get('use_cases', []),
                        confidence_score=template_data.get('confidence_score', 0.7),
                        quality_rating=self._score_to_rating(template_data.get('quality_score', 0.5)),
                        extraction_method='ai_analysis',
                        metadata={'ai_generated': True}
                    )
                    templates.append(template)
                    
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
        
        return templates
    
    def _extract_by_semantic_analysis(self, text: str) -> List[ExtractedTemplateData]:
        """Extract templates using semantic similarity analysis"""
        if not self.embeddings:
            return []
        
        # This would implement semantic analysis using vector embeddings
        # For now, return empty list as placeholder
        return []
    
    def _generate_title_from_content(self, content: str) -> str:
        """Generate a title from template content"""
        # Take first meaningful part of content
        first_sentence = content.split('.')[0].strip()
        if len(first_sentence) > 80:
            first_sentence = first_sentence[:77] + "..."
        
        # Remove common prompt starters
        title = re.sub(r'^(Act as|You are|As a|Create|Generate|Write|Develop|Build)\s+', '', first_sentence, flags=re.IGNORECASE)
        
        return title or "Extracted Template"
    
    def _generate_description(self, content: str) -> str:
        """Generate description for template"""
        # Extract first sentence or meaningful description
        sentences = content.split('.')[:2]
        description = '. '.join(sentences).strip()
        
        if len(description) > 200:
            description = description[:197] + "..."
        
        return description or "Professional prompt template"
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content"""
        keywords = []
        content_lower = content.lower()
        
        # Extract quality keywords
        for keyword in self.quality_keywords:
            if keyword in content_lower:
                keywords.append(keyword)
        
        # Extract category-specific keywords
        for category, category_keywords in self.category_mappings.items():
            for keyword in category_keywords:
                if keyword in content_lower and keyword not in keywords:
                    keywords.append(keyword)
        
        # Extract placeholder variables
        placeholders = re.findall(r'\[([^\]]+)\]', content)
        keywords.extend([p.lower().replace(' ', '_') for p in placeholders[:3]])
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _generate_use_cases(self, content: str) -> List[str]:
        """Generate potential use cases for template"""
        use_cases = []
        content_lower = content.lower()
        
        # Business use cases
        if any(word in content_lower for word in ['business', 'revenue', 'profit', 'sales']):
            use_cases.append("Business Strategy")
        
        # Marketing use cases
        if any(word in content_lower for word in ['marketing', 'campaign', 'audience', 'brand']):
            use_cases.append("Marketing Campaigns")
        
        # Content creation
        if any(word in content_lower for word in ['content', 'write', 'blog', 'article']):
            use_cases.append("Content Creation")
        
        # Analysis
        if any(word in content_lower for word in ['analyze', 'research', 'data', 'insights']):
            use_cases.append("Analysis & Research")
        
        # Planning
        if any(word in content_lower for word in ['plan', 'strategy', 'roadmap', 'goals']):
            use_cases.append("Strategic Planning")
        
        return use_cases[:3]  # Limit to 3 use cases
    
    def _assess_quality(self, content: str) -> str:
        """Assess template quality based on content analysis"""
        score = 0
        content_lower = content.lower()
        
        # Length check
        if 50 <= len(content) <= 500:
            score += 2
        elif len(content) > 500:
            score += 1
        
        # Quality keywords
        quality_matches = sum(1 for keyword in self.quality_keywords if keyword in content_lower)
        score += min(quality_matches, 3)
        
        # Structure check
        if '[' in content and ']' in content:  # Has placeholders
            score += 2
        
        # Professional language indicators
        if any(word in content_lower for word in ['professional', 'strategic', 'comprehensive', 'detailed']):
            score += 1
        
        # Actionable language
        if any(word in content_lower for word in ['create', 'develop', 'analyze', 'generate', 'build']):
            score += 1
        
        # Convert score to rating
        if score >= 6:
            return 'high'
        elif score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _score_to_rating(self, score: float) -> str:
        """Convert numeric score to quality rating"""
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _deduplicate_templates(self, templates: List[ExtractedTemplateData]) -> List[ExtractedTemplateData]:
        """Remove duplicate templates based on similarity"""
        unique_templates = []
        seen_content = set()
        
        for template in templates:
            # Simple deduplication based on content similarity
            content_hash = hash(template.template_content.lower().strip())
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_templates.append(template)
        
        return unique_templates
    
    def _enhance_templates(self, templates: List[ExtractedTemplateData]) -> List[ExtractedTemplateData]:
        """Enhance templates with additional metadata and categorization"""
        for template in templates:
            # Enhance category based on content
            if template.category == 'general':
                template.category = self._categorize_content(template.template_content)
            
            # Enhance keywords
            if not template.keywords:
                template.keywords = self._extract_keywords(template.template_content)
            
            # Enhance use cases
            if not template.use_cases:
                template.use_cases = self._generate_use_cases(template.template_content)
        
        return templates
    
    def _categorize_content(self, content: str) -> str:
        """Categorize content based on keywords and patterns"""
        content_lower = content.lower()
        category_scores = {}
        
        for category, keywords in self.category_mappings.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return 'general'
    
    def _filter_quality_templates(self, templates: List[ExtractedTemplateData]) -> List[ExtractedTemplateData]:
        """Filter templates based on quality and confidence thresholds"""
        filtered = []
        
        for template in templates:
            # Minimum confidence threshold
            if template.confidence_score < 0.5:
                continue
            
            # Minimum content length
            if len(template.template_content) < 30:
                continue
            
            # Skip low quality unless high confidence
            if template.quality_rating == 'low' and template.confidence_score < 0.8:
                continue
            
            filtered.append(template)
        
        # Sort by confidence and quality
        filtered.sort(key=lambda t: (t.confidence_score, 1 if t.quality_rating == 'high' else 0), reverse=True)
        
        return filtered


class TemplateAnalyzer:
    """Analyze templates for monetization potential and user value"""
    
    def __init__(self):
        self.monetization_keywords = [
            'business', 'revenue', 'profit', 'sales', 'marketing', 'conversion',
            'funnel', 'strategy', 'planning', 'optimization', 'analysis'
        ]
    
    def analyze_monetization_potential(self, template: ExtractedTemplateData) -> Dict[str, Any]:
        """Analyze template's monetization potential"""
        score = 0
        factors = []
        
        content_lower = template.template_content.lower()
        
        # Check for monetization keywords
        monetization_matches = sum(1 for keyword in self.monetization_keywords if keyword in content_lower)
        if monetization_matches > 0:
            score += monetization_matches * 10
            factors.append(f"Contains {monetization_matches} monetization keywords")
        
        # Quality factor
        quality_multiplier = {'high': 30, 'medium': 20, 'low': 10}
        score += quality_multiplier.get(template.quality_rating, 10)
        factors.append(f"Quality rating: {template.quality_rating}")
        
        # Confidence factor
        score += int(template.confidence_score * 20)
        factors.append(f"Confidence score: {template.confidence_score:.2f}")
        
        # Category factor
        high_value_categories = ['business', 'marketing', 'strategy', 'analysis']
        if template.category in high_value_categories:
            score += 15
            factors.append(f"High-value category: {template.category}")
        
        # Use cases factor
        score += len(template.use_cases) * 5
        factors.append(f"Use cases count: {len(template.use_cases)}")
        
        # Determine potential level
        if score >= 80:
            potential = 'high'
        elif score >= 50:
            potential = 'medium'
        else:
            potential = 'low'
        
        return {
            'potential': potential,
            'score': score,
            'factors': factors,
            'suggested_price_tier': self._suggest_price_tier(potential, template.category),
            'target_audience': self._identify_target_audience(template),
            'monetization_strategies': self._suggest_monetization_strategies(template)
        }
    
    def _suggest_price_tier(self, potential: str, category: str) -> str:
        """Suggest price tier based on potential and category"""
        if potential == 'high':
            return 'premium'
        elif potential == 'medium':
            return 'standard'
        else:
            return 'basic'
    
    def _identify_target_audience(self, template: ExtractedTemplateData) -> List[str]:
        """Identify target audience for template"""
        audiences = []
        content_lower = template.template_content.lower()
        
        if any(word in content_lower for word in ['business', 'entrepreneur', 'startup']):
            audiences.append('Entrepreneurs')
        
        if any(word in content_lower for word in ['marketing', 'advertising', 'campaign']):
            audiences.append('Marketers')
        
        if any(word in content_lower for word in ['content', 'writing', 'blog']):
            audiences.append('Content Creators')
        
        if any(word in content_lower for word in ['analysis', 'research', 'data']):
            audiences.append('Analysts')
        
        return audiences or ['General Users']
    
    def _suggest_monetization_strategies(self, template: ExtractedTemplateData) -> List[str]:
        """Suggest monetization strategies for template"""
        strategies = []
        
        if template.quality_rating == 'high':
            strategies.append('Premium tier access')
            strategies.append('Individual template sales')
        
        if len(template.use_cases) >= 2:
            strategies.append('Bundle with related templates')
        
        if template.category in ['business', 'marketing']:
            strategies.append('Corporate licensing')
            strategies.append('Consultation upsells')
        
        strategies.append('Freemium with advanced features')
        strategies.append('Credit-based usage')
        
        return strategies


# Initialize global extractors
template_extractor = TemplateExtractor()
template_analyzer = TemplateAnalyzer()