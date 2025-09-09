"""
Test LLM-semantic architecture implementation
Validates complete elimination of rule-based logic and 
replacement with LLM-driven semantic processing.
"""

import pytest
from unittest.mock import Mock, patch
from realtime_insight_synthesizer import (
    RealTimeInsightSynthesizer, 
    SemanticGrouping,
    SemanticGroup,
    SynthesisDecision
)
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph
from llm_client import LiteLLMClient


def test_no_hardcoded_rules_remain():
    """Verify complete elimination of rule-based logic"""
    with open('realtime_insight_synthesizer.py', 'r') as f:
        content = f.read()
    
    # Should NOT contain hardcoded patterns
    forbidden_patterns = [
        'synthesis_threshold =',
        'for keyword in',
        'keyword in content',
        'goal_keywords',
        'len(group) * 0.6',  # Hardcoded percentages
        'relevance_count >= len(group)',
        '_classify_content',
        '_group_relevant_to_goal'  # Old rule-based methods
    ]
    
    for pattern in forbidden_patterns:
        assert pattern not in content, f"Found hardcoded rule: {pattern}"


def test_semantic_grouping_uses_llm():
    """Test semantic grouping uses LLM instead of keyword matching"""
    synthesizer = create_test_synthesizer()
    
    # Test with semantically similar but different keywords
    datapoints = [
        create_mock_datapoint("Trump responds to allegations"),
        create_mock_datapoint("Former president addresses controversy"),  # Different words, same meaning
        create_mock_datapoint("Political figure denies connection"),
        create_mock_datapoint("Weather forecast today")  # Unrelated
    ]
    
    mock_grouping = SemanticGrouping(
        groups=[
            SemanticGroup(
                group_theme="Trump allegations response", 
                datapoint_ids=["dp1", "dp2", "dp3"],
                relevance_to_goal=0.9,
                synthesis_worthy=True
            )
        ],
        rationale="Grouped by semantic similarity"
    )
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_grouping
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response):
        result = synthesizer._group_semantically_llm(datapoints)
        
        # Should group semantically similar content
        assert len(result.groups) == 1
        assert result.groups[0].synthesis_worthy == True
        assert "Trump" in result.groups[0].group_theme


def test_synthesis_trigger_uses_llm_decision():
    """Test synthesis trigger uses LLM instead of thresholds"""
    synthesizer = create_test_synthesizer()
    
    mock_decision = SynthesisDecision(
        should_synthesize=True,
        reasoning="Multiple findings show pattern",
        synthesis_potential=0.8
    )
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_decision
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response):
        should_synthesize = synthesizer._should_synthesize_llm(["dp1", "dp2", "dp3"])
        
        assert should_synthesize == True


def test_no_keyword_based_classification():
    """Test that keyword-based classification methods are removed"""
    synthesizer = create_test_synthesizer()
    
    # These methods should not exist anymore
    assert not hasattr(synthesizer, '_classify_content')
    assert not hasattr(synthesizer, '_group_relevant_to_goal')
    
    # Should use LLM-based methods instead
    assert hasattr(synthesizer, '_group_semantically_llm')
    assert hasattr(synthesizer, '_should_synthesize_llm')


def test_fallback_behavior_on_llm_failure():
    """Test graceful degradation when LLM calls fail"""
    synthesizer = create_test_synthesizer()
    
    # Mock LLM failure
    with patch.object(synthesizer.llm, 'completion', side_effect=Exception("LLM failed")):
        # Should not crash but provide reasonable fallback
        result = synthesizer._should_synthesize_llm(["dp1", "dp2", "dp3", "dp4", "dp5", "dp6", "dp7", "dp8"])
        
        # Fallback should be conservative (only when many datapoints)
        assert result == True  # 8 datapoints should trigger fallback
        
        # Test with fewer datapoints
        result_few = synthesizer._should_synthesize_llm(["dp1", "dp2", "dp3"])
        assert result_few == False  # Should not synthesize with few datapoints on error


def test_semantic_understanding_prompt_quality():
    """Test that LLM prompts emphasize semantic understanding"""
    synthesizer = create_test_synthesizer()
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock() 
    mock_response.choices[0].message.parsed = SemanticGrouping(
        groups=[],
        rationale="Test"
    )
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response) as mock_llm:
        synthesizer._group_semantically_llm([])
        
        # Check that prompt emphasizes semantic understanding
        call_args = mock_llm.call_args
        prompt = call_args[1]['messages'][0]['content']
        
        assert "semantic" in prompt.lower()
        assert "understanding" in prompt.lower()
        assert "investigation relevance" in prompt.lower()
        # Should emphasize semantic understanding over keyword approaches
        assert "Use semantic understanding" in prompt


def create_test_synthesizer():
    """Create test synthesizer with mocked dependencies"""
    context = InvestigationContext("Test investigation", [], "twitter")
    context.investigation_id = "test_id"
    context.analytic_question = "Test Trump Epstein investigation"
    graph = InvestigationGraph()
    llm_client = Mock(spec=LiteLLMClient)
    return RealTimeInsightSynthesizer(llm_client, graph, context)


def create_mock_datapoint(content: str, dp_id: str = None):
    """Create mock DataPoint node"""
    mock_dp = Mock()
    mock_dp.id = dp_id or f"dp_{hash(content) % 1000}"
    mock_dp.properties = {"content": content}
    mock_dp.node_type = "DataPoint"
    return mock_dp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])