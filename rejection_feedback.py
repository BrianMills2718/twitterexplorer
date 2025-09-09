"""Rejection feedback mechanism for investigation improvement"""
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json

@dataclass
class RejectionFeedback:
    """Tracks what was rejected and why for strategy improvement"""
    round_number: int
    total_evaluated: int
    total_accepted: int
    total_rejected: int
    rejection_rate: float
    
    # Sample rejections to inform next strategy
    rejection_samples: List[Dict[str, Any]] = field(default_factory=list)
    rejection_themes: List[str] = field(default_factory=list)  # Common patterns
    
    def to_strategy_context(self) -> str:
        """Convert rejection info to context for next strategy"""
        if not self.rejection_samples:
            return ""
        
        context = f"Previous round rejected {self.rejection_rate:.0%} of results as irrelevant.\n"
        
        if self.rejection_themes:
            context += f"Common irrelevant themes: {', '.join(self.rejection_themes[:5])}\n"
        
        context += "Examples of rejected content:\n"
        for i, sample in enumerate(self.rejection_samples[:3], 1):
            text_preview = sample.get('text', '')[:50]
            reason = sample.get('reason', 'No reason provided')[:100]
            context += f"  {i}. '{text_preview}...' - Rejected because: {reason}\n"
        
        context += "\nPlease refine the next search to avoid similar irrelevant results."
        return context

def analyze_rejections(results_evaluated: List[Dict], 
                       assessments: List['FindingAssessment'],
                       investigation_goal: str) -> RejectionFeedback:
    """Analyze what was rejected to inform future searches"""
    
    total = len(assessments)
    accepted = sum(1 for a in assessments if a.is_significant)
    rejected = total - accepted
    
    rejection_feedback = RejectionFeedback(
        round_number=0,  # Will be set by caller
        total_evaluated=total,
        total_accepted=accepted,
        total_rejected=rejected,
        rejection_rate=rejected/total if total > 0 else 0
    )
    
    # Collect rejection samples
    for result, assessment in zip(results_evaluated, assessments):
        if not assessment.is_significant:
            rejection_feedback.rejection_samples.append({
                'text': result.get('text', '')[:100],
                'reason': assessment.reasoning[:150],
                'relevance_score': assessment.relevance_score
            })
    
    # Identify common themes in rejections (simple keyword analysis)
    if rejection_feedback.rejection_samples:
        # Extract common words from rejected content
        rejected_texts = ' '.join([s['text'].lower() for s in rejection_feedback.rejection_samples])
        
        # Simple theme detection - could be enhanced with better NLP
        irrelevant_keywords = []
        
        # Check for common off-topic patterns
        if 'recipe' in rejected_texts or 'cooking' in rejected_texts:
            irrelevant_keywords.append('cooking/recipes')
        if 'sports' in rejected_texts or 'game' in rejected_texts:
            irrelevant_keywords.append('sports')
        if 'weather' in rejected_texts:
            irrelevant_keywords.append('weather')
        if 'sale' in rejected_texts or 'discount' in rejected_texts:
            irrelevant_keywords.append('promotional content')
            
        # Check if results are too old
        if any('2020' in s['text'] or '2021' in s['text'] or '2022' in s['text'] 
               for s in rejection_feedback.rejection_samples[:5]):
            irrelevant_keywords.append('outdated content')
        
        rejection_feedback.rejection_themes = irrelevant_keywords
    
    return rejection_feedback