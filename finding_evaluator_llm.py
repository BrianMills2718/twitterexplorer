"""LLM-based evaluator to identify DataPoint-worthy findings from search results"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
# litellm imported via llm_client

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

class LLMFindingEvaluator:
    """Uses LLM to evaluate search results and identify significant findings"""
    
    def __init__(self, llm_client=None, model_manager=None):
        if llm_client is None:
            from llm_client import get_litellm_client
            self.llm_client = get_litellm_client()
        else:
            self.llm_client = llm_client
        
        # Initialize model manager
        if model_manager is None:
            from llm_model_manager import LLMModelManager
            self.model_manager = LLMModelManager()
        else:
            self.model_manager = model_manager
        
    def evaluate_finding(self, result: Dict[str, Any], investigation_goal: str) -> FindingAssessment:
        """
        Use LLM to assess if a search result contains significant information worth preserving
        
        Args:
            result: Raw search result with 'text', 'source', 'metadata'
            investigation_goal: The original investigation query
            
        Returns:
            FindingAssessment with LLM-based significance determination
        """
        
        evaluation_prompt = f"""
        You are evaluating whether a search result contains significant information for an investigation.
        
        Investigation Goal: {investigation_goal}
        
        Search Result:
        {result.get('text', '')}
        
        Source: {result.get('source', 'unknown')}
        
        Evaluate this result and determine:
        1. is_significant: Is this finding worth preserving as a DataPoint? (true/false)
        2. relevance_score: How relevant is this to the investigation goal? (0.0-1.0)
        3. specificity_score: How specific and actionable is the information? (0.0-1.0)
        4. entities: What key entities are mentioned? (people, dates, places, amounts, organizations)
        5. key_claims: What are the main factual claims? (list up to 3)
        6. suggested_followup: What follow-up investigation would be valuable? (optional)
        7. reasoning: Brief explanation of your assessment
        
        Criteria for significance:
        - Contains specific, verifiable information (dates, names, amounts, events)
        - Directly relates to the investigation goal
        - Not generic content like "click here" or "read more"
        - Provides new information or evidence
        
        Return as JSON with these exact fields.
        """
        
        try:
            # Use configured model instead of hardcoded
            model = self.model_manager.get_model_for_operation("finding_evaluator")
            response = self.llm_client.completion(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert investigation analyst evaluating evidence."},
                    {"role": "user", "content": evaluation_prompt}
                ]
            )
            
            # Parse LLM response - strip markdown formatting if present
            content = response.choices[0].message.content.strip()
            if content.startswith('```') and content.endswith('```'):
                content = content[3:-3]
            if content.startswith('json'):
                content = content[4:]
            evaluation = json.loads(content.strip())
            
            return FindingAssessment(
                is_significant=evaluation.get('is_significant', False),
                relevance_score=float(evaluation.get('relevance_score', 0.0)),
                specificity_score=float(evaluation.get('specificity_score', 0.0)),
                entities=evaluation.get('entities', {}),
                key_claims=evaluation.get('key_claims', []),
                suggested_followup=evaluation.get('suggested_followup'),
                reasoning=evaluation.get('reasoning', 'No reasoning provided')
            )
            
        except Exception as e:
            # FAIL-FAST: Surface errors immediately per CLAUDE.md principles
            raise RuntimeError(f"LLM evaluation failed - investigation cannot continue: {str(e)}") from e
    
    def evaluate_batch(self, results: List[Dict[str, Any]], investigation_goal: str) -> List[FindingAssessment]:
        """
        Evaluate multiple findings in a single LLM call for efficiency
        
        Args:
            results: List of raw search results
            investigation_goal: The original investigation query
            
        Returns:
            List of FindingAssessments
        """
        
        if not results:
            return []
        
        # FAIL-FAST: No graceful degradation per CLAUDE.md principles
        if not self.llm_client:
            raise RuntimeError("No LLM client available - investigation cannot continue")
        
        # Simplified prompt to avoid JSON formatting issues
        results_summary = []
        for i, r in enumerate(results[:10]):  # Limit to prevent token overflow
            text = r.get('text', '') if isinstance(r, dict) else str(r)
            text_preview = text[:200] + "..." if len(text) > 200 else text
            results_summary.append(f"Result {i}: {text_preview}")
        
        batch_prompt = f"""Investigation: {investigation_goal}

Evaluate these {len(results_summary)} Twitter results. For each, determine if it contains significant information worth preserving as a DataPoint.

{chr(10).join(results_summary)}

Return JSON array with {len(results_summary)} evaluations:
[
  {{"is_significant": true/false, "relevance_score": 0.0-1.0, "reasoning": "brief explanation"}},
  {{"is_significant": true/false, "relevance_score": 0.0-1.0, "reasoning": "brief explanation"}}
]

Only mark as significant if directly relevant to: {investigation_goal}"""
        
        try:
            # Use configured model instead of hardcoded
            model = self.model_manager.get_model_for_operation("finding_evaluator")
            response = self.llm_client.completion(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert investigation analyst evaluating evidence."},
                    {"role": "user", "content": batch_prompt}
                ]
            )
            
            # Parse batch response - strip markdown formatting if present
            content = response.choices[0].message.content.strip()
            if content.startswith('```') and content.endswith('```'):
                content = content[3:-3]
            if content.startswith('json'):
                content = content[4:]
            batch_evaluation = json.loads(content.strip())
            
            # Handle both formats: direct list or dict with 'evaluations' key
            if isinstance(batch_evaluation, list):
                evaluations = batch_evaluation
            else:
                evaluations = batch_evaluation.get('evaluations', [])
            
            assessments = []
            for i, eval_data in enumerate(evaluations):
                assessments.append(FindingAssessment(
                    is_significant=eval_data.get('is_significant', False),
                    relevance_score=float(eval_data.get('relevance_score', 0.0)),
                    specificity_score=0.5,  # Default value since not in simplified format
                    entities={},  # Simplified - no entities extraction
                    key_claims=[],  # Simplified - no key claims extraction
                    suggested_followup=None,  # Simplified - no followup suggestions
                    reasoning=eval_data.get('reasoning', 'No reasoning provided')
                ))
            
            # Fill in any missing evaluations
            while len(assessments) < len(results):
                assessments.append(FindingAssessment(
                    is_significant=False,
                    relevance_score=0.0,
                    specificity_score=0.0,
                    entities={},
                    key_claims=[],
                    suggested_followup=None,
                    reasoning="Not evaluated"
                ))
            
            return assessments
            
        except Exception as e:
            # FAIL-FAST: Surface errors immediately per CLAUDE.md principles
            raise RuntimeError(f"LLM batch evaluation failed - investigation cannot continue: {str(e)}") from e