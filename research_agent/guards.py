"""
Quality guards for research agent content validation.
"""
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from .contracts import InsightCard, CitationModel, QualityMetrics

logger = logging.getLogger(__name__)


class QualityGuard:
    """Base class for quality validation."""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
    
    def validate(self, card: InsightCard) -> bool:
        """Validate a card. Return True if passes, False if rejected."""
        raise NotImplementedError
    
    def get_reason(self) -> str:
        """Get rejection reason for logging."""
        return f"Failed {self.name} guard"


class CitationGuard(QualityGuard):
    """Ensure cards have sufficient citations."""
    
    def __init__(self, min_citations: int = 1):
        super().__init__("Citation", enabled=True)
        self.min_citations = min_citations
    
    def validate(self, card: InsightCard) -> bool:
        """Check if card has minimum citations."""
        return len(card.citations) >= self.min_citations
    
    def get_reason(self) -> str:
        return f"Insufficient citations (has {len(getattr(self, '_last_card', InsightCard(id='', title='', content='', confidence=0, authority=0)).citations)}, needs {self.min_citations})"


class AuthorityGuard(QualityGuard):
    """Ensure cards meet authority threshold."""
    
    def __init__(self, min_authority: float = 0.6):
        super().__init__("Authority", enabled=True)
        self.min_authority = min_authority
    
    def validate(self, card: InsightCard) -> bool:
        """Check if card meets authority threshold."""
        return card.authority >= self.min_authority
    
    def get_reason(self) -> str:
        return f"Low authority score ({getattr(self, '_last_authority', 0):.2f} < {self.min_authority})"


class ConfidenceGuard(QualityGuard):
    """Ensure cards meet confidence threshold."""
    
    def __init__(self, min_confidence: float = 0.5):
        super().__init__("Confidence", enabled=True)
        self.min_confidence = min_confidence
    
    def validate(self, card: InsightCard) -> bool:
        """Check if card meets confidence threshold."""
        return card.confidence >= self.min_confidence
    
    def get_reason(self) -> str:
        return f"Low confidence score ({getattr(self, '_last_confidence', 0):.2f} < {self.min_confidence})"


class ContentLengthGuard(QualityGuard):
    """Ensure cards have sufficient content."""
    
    def __init__(self, min_length: int = 50, max_length: int = 2000):
        super().__init__("ContentLength", enabled=True)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, card: InsightCard) -> bool:
        """Check if card content is appropriate length."""
        content_length = len(card.content.strip())
        return self.min_length <= content_length <= self.max_length
    
    def get_reason(self) -> str:
        length = len(getattr(self, '_last_content', ''))
        if length < self.min_length:
            return f"Content too short ({length} < {self.min_length})"
        else:
            return f"Content too long ({length} > {self.max_length})"


class DuplicateGuard(QualityGuard):
    """Prevent duplicate or very similar cards."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        super().__init__("Duplicate", enabled=True)
        self.similarity_threshold = similarity_threshold
        self.seen_cards: List[InsightCard] = []
    
    def validate(self, card: InsightCard) -> bool:
        """Check if card is too similar to existing cards."""
        for seen_card in self.seen_cards:
            if self._calculate_similarity(card, seen_card) > self.similarity_threshold:
                return False
        
        self.seen_cards.append(card)
        return True
    
    def _calculate_similarity(self, card1: InsightCard, card2: InsightCard) -> float:
        """Calculate similarity between two cards."""
        # Simple similarity based on title and content overlap
        title_similarity = self._text_similarity(card1.title, card2.title)
        content_similarity = self._text_similarity(card1.content, card2.content)
        
        # Weighted average
        return (title_similarity * 0.4) + (content_similarity * 0.6)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_reason(self) -> str:
        return "Duplicate or highly similar content"


class RelevanceGuard(QualityGuard):
    """Ensure cards are relevant to the original query."""
    
    def __init__(self, query: str, min_relevance: float = 0.3):
        super().__init__("Relevance", enabled=True)
        self.query = query.lower()
        self.min_relevance = min_relevance
        self.query_terms = set(query.lower().split())
    
    def validate(self, card: InsightCard) -> bool:
        """Check if card is relevant to the query."""
        relevance_score = self._calculate_relevance(card)
        return relevance_score >= self.min_relevance
    
    def _calculate_relevance(self, card: InsightCard) -> float:
        """Calculate relevance score based on term overlap."""
        card_text = (card.title + " " + card.content).lower()
        card_terms = set(card_text.split())
        
        if not self.query_terms or not card_terms:
            return 0.0
        
        # Calculate term overlap
        overlap = self.query_terms.intersection(card_terms)
        relevance = len(overlap) / len(self.query_terms)
        
        # Boost score if query terms appear in title
        title_terms = set(card.title.lower().split())
        title_overlap = self.query_terms.intersection(title_terms)
        if title_overlap:
            relevance += 0.2  # Title bonus
        
        return min(relevance, 1.0)
    
    def get_reason(self) -> str:
        return f"Low relevance to query '{self.query[:50]}...'"


class QualityGuardRunner:
    """Orchestrates quality guard validation."""
    
    def __init__(self, query: str = ""):
        """Initialize with configuration from settings."""
        config = getattr(settings, 'RESEARCH', {})
        
        self.guards: List[QualityGuard] = []
        
        # Initialize guards based on configuration
        if config.get('ENABLE_QUALITY_GUARDS', True):
            self.guards.extend([
                CitationGuard(min_citations=1),
                AuthorityGuard(min_authority=config.get('MIN_AUTHORITY_SCORE', 0.6)),
                ConfidenceGuard(min_confidence=config.get('MIN_CONFIDENCE_SCORE', 0.5)),
                ContentLengthGuard(min_length=50, max_length=2000),
                DuplicateGuard(similarity_threshold=0.85),
            ])
            
            if query:
                self.guards.append(RelevanceGuard(query, min_relevance=0.3))
    
    def validate_card(self, card: InsightCard) -> Dict[str, Any]:
        """
        Validate a card against all guards.
        
        Returns:
            Dictionary with validation results
        """
        result = {
            'passed': True,
            'failures': [],
            'guard_results': {}
        }
        
        for guard in self.guards:
            if not guard.enabled:
                continue
                
            try:
                passed = guard.validate(card)
                result['guard_results'][guard.name] = passed
                
                if not passed:
                    result['passed'] = False
                    result['failures'].append(guard.get_reason())
                    
            except Exception as e:
                logger.error(f"Guard {guard.name} failed with error: {e}")
                result['guard_results'][guard.name] = False
                result['passed'] = False
                result['failures'].append(f"Guard error: {str(e)}")
        
        return result
    
    def validate_cards(self, cards: List[InsightCard]) -> Dict[str, Any]:
        """
        Validate multiple cards and return summary.
        
        Returns:
            Validation summary with statistics
        """
        results = {
            'total_cards': len(cards),
            'passed_cards': 0,
            'failed_cards': 0,
            'valid_cards': [],
            'rejected_cards': [],
            'guard_stats': {},
            'failure_reasons': []
        }
        
        # Initialize guard stats
        for guard in self.guards:
            if guard.enabled:
                results['guard_stats'][guard.name] = {'passed': 0, 'failed': 0}
        
        # Validate each card
        for card in cards:
            validation_result = self.validate_card(card)
            
            if validation_result['passed']:
                results['passed_cards'] += 1
                results['valid_cards'].append(card)
            else:
                results['failed_cards'] += 1
                results['rejected_cards'].append({
                    'card_id': card.id,
                    'failures': validation_result['failures']
                })
                results['failure_reasons'].extend(validation_result['failures'])
            
            # Update guard statistics
            for guard_name, passed in validation_result['guard_results'].items():
                if guard_name in results['guard_stats']:
                    if passed:
                        results['guard_stats'][guard_name]['passed'] += 1
                    else:
                        results['guard_stats'][guard_name]['failed'] += 1
        
        return results
    
    def get_quality_metrics(self, cards: List[InsightCard]) -> QualityMetrics:
        """Generate quality metrics for a set of cards."""
        if not cards:
            return QualityMetrics(
                authority_score=0.0,
                confidence_score=0.0,
                citation_count=0,
                content_length=0,
                domain_diversity=0.0,
                freshness_score=0.0
            )
        
        # Calculate averages
        avg_authority = sum(card.authority for card in cards) / len(cards)
        avg_confidence = sum(card.confidence for card in cards) / len(cards)
        total_citations = sum(len(card.citations) for card in cards)
        total_content_length = sum(len(card.content) for card in cards)
        
        # Calculate domain diversity
        domains = set()
        for card in cards:
            for citation in card.citations:
                if citation.domain:
                    domains.add(citation.domain)
        
        domain_diversity = min(len(domains) / len(cards), 1.0) if cards else 0.0
        
        return QualityMetrics(
            authority_score=avg_authority,
            confidence_score=avg_confidence,
            citation_count=total_citations,
            content_length=total_content_length,
            domain_diversity=domain_diversity,
            freshness_score=0.8  # Placeholder - could be calculated from source dates
        )


def validate_card_quality(card: InsightCard, query: str = "") -> bool:
    """
    Quick validation function for a single card.
    
    Args:
        card: The card to validate
        query: Original research query for relevance checking
        
    Returns:
        True if card passes all quality guards
    """
    runner = QualityGuardRunner(query)
    result = runner.validate_card(card)
    return result['passed']


def filter_cards_by_quality(cards: List[InsightCard], query: str = "") -> List[InsightCard]:
    """
    Filter cards to only return those that pass quality guards.
    
    Args:
        cards: List of cards to filter
        query: Original research query
        
    Returns:
        List of cards that pass quality validation
    """
    runner = QualityGuardRunner(query)
    validation_result = runner.validate_cards(cards)
    
    logger.info(f"Quality filtering: {validation_result['passed_cards']}/{validation_result['total_cards']} cards passed")
    
    return validation_result['valid_cards']