"""Evaluator to identify DataPoint-worthy findings from search results"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

@dataclass
class FindingAssessment:
    """Assessment of whether a finding is DataPoint-worthy"""
    is_significant: bool
    relevance_score: float
    specificity_score: float
    entities: Dict[str, List[str]]
    key_claims: List[str]
    suggested_followup: Optional[str]
    reasoning: str

class FindingEvaluator:
    """Evaluates search results to identify significant findings"""
    
    def __init__(self):
        # Indicators of specific, actionable information
        self.SPECIFICITY_PATTERNS = {
            'dates': r'\b(?:19|20)\d{2}[-/](?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b',
            'money': r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand|M|B|K))?|\b\d+(?:\.\d+)?\s*(?:million|billion|thousand)\s*(?:dollars|USD)?',
            'percentages': r'\b\d+\.?\d*\s*%',
            'quotes': r'"[^"]{10,}"',
            'numbers': r'\b\d{3,}\b'
        }
        
        # Indicators of generic/unhelpful content
        self.GENERIC_INDICATORS = [
            'click here', 'read more', 'subscribe', 'follow us',
            'no results found', 'search again', 'try different',
            'coming soon', 'under construction', 'lorem ipsum'
        ]
        
    def evaluate_finding(self, result: Dict[str, Any], investigation_goal: str) -> FindingAssessment:
        """
        Assess if a search result contains significant information worth preserving
        
        Args:
            result: Raw search result with 'text', 'source', 'metadata'
            investigation_goal: The original investigation query
            
        Returns:
            FindingAssessment with significance determination
        """
        text = result.get('text', '').lower()
        
        # Check for generic/unhelpful content
        if any(indicator in text for indicator in self.GENERIC_INDICATORS):
            return FindingAssessment(
                is_significant=False,
                relevance_score=0.0,
                specificity_score=0.0,
                entities={},
                key_claims=[],
                suggested_followup=None,
                reasoning="Contains generic/unhelpful content"
            )
        
        # Extract entities and specific information
        entities = self._extract_entities(result.get('text', ''))
        specificity_score = self._calculate_specificity(result.get('text', ''), entities)
        relevance_score = self._calculate_relevance(result.get('text', ''), investigation_goal)
        
        # Determine significance
        is_significant = (specificity_score > 0.3 and relevance_score > 0.4) or (specificity_score > 0.6)
        
        # Extract key claims if significant
        key_claims = self._extract_key_claims(result.get('text', '')) if is_significant else []
        
        # Suggest follow-up if patterns detected
        suggested_followup = self._suggest_followup(entities, key_claims) if is_significant else None
        
        return FindingAssessment(
            is_significant=is_significant,
            relevance_score=relevance_score,
            specificity_score=specificity_score,
            entities=entities,
            key_claims=key_claims,
            suggested_followup=suggested_followup,
            reasoning=self._generate_reasoning(specificity_score, relevance_score, entities)
        )
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text"""
        entities = {}
        
        # Extract dates
        date_matches = re.findall(self.SPECIFICITY_PATTERNS['dates'], text)
        if date_matches:
            # Handle tuple results from regex groups
            clean_dates = []
            for d in date_matches:
                if isinstance(d, tuple):
                    # Find first non-empty match in tuple
                    for item in d:
                        if item:
                            clean_dates.append(str(item))
                            break
                else:
                    clean_dates.append(str(d))
            if clean_dates:
                entities['dates'] = list(set(clean_dates))
        
        # Extract money amounts
        money_matches = re.findall(self.SPECIFICITY_PATTERNS['money'], text)
        if money_matches:
            entities['amounts'] = list(set(money_matches))
        
        # Extract quoted text
        quote_matches = re.findall(self.SPECIFICITY_PATTERNS['quotes'], text)
        if quote_matches:
            entities['quotes'] = quote_matches[:3]  # Limit to 3 quotes
        
        # Extract proper nouns (simple heuristic - words that are capitalized)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        if proper_nouns:
            entities['names'] = list(set(proper_nouns))[:10]  # Limit to 10 names
        
        return entities
    
    def _calculate_specificity(self, text: str, entities: Dict) -> float:
        """Calculate how specific and detailed the information is"""
        score = 0.0
        
        # Check for specific patterns
        for pattern_type, pattern in self.SPECIFICITY_PATTERNS.items():
            if re.search(pattern, text):
                score += 0.2
        
        # Boost for multiple entity types
        score += len(entities) * 0.1
        
        # Boost for longer, detailed text
        if len(text) > 200:
            score += 0.1
        if len(text) > 500:
            score += 0.1
            
        return min(1.0, score)
    
    def _calculate_relevance(self, text: str, goal: str) -> float:
        """Calculate relevance to investigation goal"""
        text_lower = text.lower()
        goal_lower = goal.lower()
        
        # Extract key terms from goal
        goal_terms = [term for term in goal_lower.split() if len(term) > 3]
        
        # Count matching terms
        matches = sum(1 for term in goal_terms if term in text_lower)
        
        # Calculate relevance score
        if goal_terms:
            relevance = matches / len(goal_terms)
        else:
            relevance = 0.5  # Default if no terms extracted
            
        return min(1.0, relevance)
    
    def _extract_key_claims(self, text: str) -> List[str]:
        """Extract key factual claims from text"""
        claims = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Look for sentences with specific information
            if any(re.search(pattern, sentence) for pattern in self.SPECIFICITY_PATTERNS.values()):
                claims.append(sentence.strip())
                if len(claims) >= 3:  # Limit to 3 key claims
                    break
                    
        return claims
    
    def _suggest_followup(self, entities: Dict, claims: List[str]) -> Optional[str]:
        """Suggest follow-up searches based on findings"""
        if entities.get('dates'):
            return f"Search for events around {entities['dates'][0]}"
        elif entities.get('names'):
            return f"Investigate {entities['names'][0]} further"
        elif entities.get('amounts'):
            return f"Verify financial information: {entities['amounts'][0]}"
        return None
    
    def _generate_reasoning(self, specificity: float, relevance: float, entities: Dict) -> str:
        """Generate human-readable reasoning for the assessment"""
        if specificity < 0.3:
            return "Too generic, lacks specific information"
        elif relevance < 0.4:
            return "Not relevant to investigation goal"
        elif entities:
            return f"Contains specific entities: {', '.join(entities.keys())}"
        else:
            return f"Specificity: {specificity:.1f}, Relevance: {relevance:.1f}"