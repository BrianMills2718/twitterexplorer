#!/usr/bin/env python3
"""
Test gpt-5-mini structured output capability for InsightSynthesis schema
Phase 1: Issue #2 - Untitled Insight Generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_insight_synthesizer import InsightSynthesis
from llm_client import get_litellm_client
from investigation_context import InvestigationContext


def test_gpt5_structured_output():
    """Test gpt-5-mini generates proper structured output for InsightSynthesis"""
    
    print("Testing gpt-5-mini structured output for InsightSynthesis...")
    
    # Initialize LLM client with API keys loaded
    llm_client = get_litellm_client()
    
    # Create test context
    context = InvestigationContext(
        analytic_question="Test investigation about user behavior patterns",
        investigation_scope="social_media_analysis"
    )
    
    # Test content items for insight synthesis
    test_content = [
        "Users frequently engage with visual content over text-based posts",
        "Peak engagement times are during evening hours between 6-8 PM",
        "Mobile users show 40% higher interaction rates than desktop users"
    ]
    
    # Create synthesis prompt similar to realtime_insight_synthesizer.py:358
    prompt = f"""
INVESTIGATION: {context.analytic_question}

RELATED FINDINGS:
{chr(10).join(f"- {content}" for content in test_content)}

TASK: Synthesize ONE key insight connecting these findings.

REQUIREMENTS:
- title: Create a concise, descriptive title (5-10 words) that captures the main insight
- content: Detailed explanation of the insight and its significance  
- confidence_level: Rate your confidence 0.0-1.0 based on evidence strength
- pattern_type: Choose from: "contradiction", "trend", "connection", "implication"
- key_evidence: List 2-3 specific evidence snippets supporting the insight
- investigation_relevance: Rate 0.0-1.0 relevance to investigation goal

Focus on:
- Patterns advancing understanding of: "{context.analytic_question}"
- Contradictions or conflicts between sources
- Significant implications for investigation goal
- Emerging themes relevant to investigation

EXAMPLES of good titles:
- "Mobile-First Visual Engagement Pattern"
- "Evening Peak Drives User Behavior" 
- "Visual Content Dominates Engagement"

IGNORE: Content unrelated to "{context.analytic_question}"
"""

    try:
        # Test structured output generation
        response = llm_client.completion(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=InsightSynthesis
        )
        
        # Validate response structure
        assert response.choices, "No response choices returned"
        assert response.choices[0].message.parsed, "No parsed response in message"
        
        insight = response.choices[0].message.parsed
        
        # Validate InsightSynthesis fields
        assert isinstance(insight, InsightSynthesis), f"Response not InsightSynthesis: {type(insight)}"
        assert insight.title, f"Empty title: '{insight.title}'"
        assert insight.title.strip() != "", "Title is whitespace only"
        assert "untitled" not in insight.title.lower(), f"Title contains 'untitled': {insight.title}"
        assert insight.content, f"Empty content: '{insight.content}'"
        assert isinstance(insight.confidence_level, (int, float)), f"Invalid confidence type: {type(insight.confidence_level)}"
        assert 0.0 <= insight.confidence_level <= 1.0, f"Confidence out of range: {insight.confidence_level}"
        assert insight.pattern_type in ["contradiction", "trend", "connection", "implication"], f"Invalid pattern type: {insight.pattern_type}"
        assert isinstance(insight.key_evidence, list), f"Key evidence not list: {type(insight.key_evidence)}"
        assert len(insight.key_evidence) > 0, "Empty key evidence list"
        assert isinstance(insight.investigation_relevance, (int, float)), f"Invalid relevance type: {type(insight.investigation_relevance)}"
        assert 0.0 <= insight.investigation_relevance <= 1.0, f"Relevance out of range: {insight.investigation_relevance}"
        
        print("SUCCESS: gpt-5-mini structured output test passed!")
        print(f"Generated insight:")
        print(f"  Title: '{insight.title}'")
        print(f"  Confidence: {insight.confidence_level}")
        print(f"  Pattern: {insight.pattern_type}")
        print(f"  Evidence count: {len(insight.key_evidence)}")
        print(f"  Relevance: {insight.investigation_relevance}")
        
        return True
        
    except Exception as e:
        print(f"FAILURE: gpt-5-mini structured output test failed: {e}")
        print(f"Error type: {type(e)}")
        return False


if __name__ == "__main__":
    success = test_gpt5_structured_output()
    sys.exit(0 if success else 1)