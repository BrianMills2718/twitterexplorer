# investigation_context.py
"""
Investigation Context System - Goal-Aware Processing Foundation

Provides investigation context that propagates goal awareness through the 
processing chain to ensure all operations stay relevant to the investigation objective.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Callable
from datetime import datetime
import re


@dataclass 
class InvestigationContext:
    """Context object that propagates goal awareness through processing chain"""
    analytic_question: str
    investigation_scope: str
    goal_keywords: List[str] = None
    relevance_threshold: float = 0.5
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
            
        # Extract goal keywords from analytic question
        if not self.goal_keywords:
            self.goal_keywords = self._extract_goal_keywords()
            
    def _extract_goal_keywords(self) -> List[str]:
        """Extract key terms from analytic question for relevance filtering"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b[a-zA-Z]{3,}\b', self.analytic_question.lower())
        
        # Enhanced stop words list including generic query words
        stop_words = {
            'the', 'and', 'but', 'for', 'are', 'have', 'this', 'that', 'with', 'what', 'about', 
            'how', 'when', 'where', 'why', 'who', 'which', 'from', 'they', 'them', 'than', 
            'would', 'could', 'should', 'will', 'can', 'may', 'might', 'been', 'being', 'was',
            'were', 'said', 'says', 'get', 'got', 'make', 'made', 'take', 'took', 'give', 'gave',
            # Generic query words that shouldn't be core keywords
            'find', 'different', 'current', 'recent', 'latest', 'takes', 'ways', 'more', 'some',
            'any', 'all', 'most', 'many', 'few', 'other', 'another', 'same', 'new', 'old',
            'good', 'bad', 'big', 'small', 'long', 'short', 'high', 'low', 'first', 'last',
            'next', 'previous', 'best', 'worst', 'better', 'worse'
        }
        filtered_words = [w for w in words if w not in stop_words]
        
        # Prioritize proper nouns and specific terms (capitalized in original)
        original_words = re.findall(r'\b[A-Z][a-zA-Z]{2,}\b', self.analytic_question)
        proper_nouns = [w.lower() for w in original_words if w.lower() not in stop_words]
        
        # Combine with priority to proper nouns
        final_keywords = proper_nouns + [w for w in filtered_words if w not in proper_nouns]
        
        # Return top 5 keywords, prioritizing proper nouns
        return final_keywords[:5] if len(final_keywords) >= 5 else final_keywords
        
    def is_relevant_to_goal(self, content: str) -> bool:
        """Check if content is relevant to investigation goal"""
        if not content:
            return False
            
        content_lower = content.lower()
        
        # Check if any goal keywords appear in content
        keyword_matches = sum(1 for keyword in self.goal_keywords if keyword in content_lower)
        
        # Content relevant if contains at least 1 goal keyword
        return keyword_matches > 0
        
    def calculate_goal_relevance_score(self, content: str) -> float:
        """Calculate 0-1 relevance score based on goal alignment"""
        if not content:
            return 0.0
            
        content_lower = content.lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in self.goal_keywords if keyword in content_lower)
        
        # Calculate score based on keyword density
        if len(self.goal_keywords) == 0:
            return 0.5  # Neutral if no keywords
            
        return min(matches / len(self.goal_keywords), 1.0)
        
    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        return f"Investigation: {self.analytic_question}\nFocus Areas: {', '.join(self.goal_keywords)}\nScope: {self.investigation_scope}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize context to dictionary"""
        return {
            "analytic_question": self.analytic_question,
            "goal_keywords": self.goal_keywords,
            "investigation_scope": self.investigation_scope,
            "relevance_threshold": self.relevance_threshold,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InvestigationContext':
        """Deserialize context from dictionary"""
        if "created_at" in data and data["created_at"]:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)