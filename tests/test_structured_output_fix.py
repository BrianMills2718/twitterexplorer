"""
Test structured output consistency fixes in realtime_insight_synthesizer.py
Validates that manual JSON parsing has been completely eliminated and 
proper LiteLLM structured output is used throughout.
"""

import pytest
from unittest.mock import Mock, patch
from realtime_insight_synthesizer import (
    RealTimeInsightSynthesizer, 
    InsightSynthesis, 
    SemanticGrouping,
    SemanticGroup,
    SynthesisDecision
)
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph
from llm_client import LiteLLMClient


def test_no_manual_json_parsing():
    """Verify no manual JSON parsing remains in codebase"""
    with open('realtime_insight_synthesizer.py', 'r') as f:
        content = f.read()
    
    # Should NOT contain manual parsing patterns
    forbidden_patterns = [
        're.search',
        'json_match',
        'eval(',
        'json.loads(json_match',  # Specific pattern that was removed
        'json_match.group()'
    ]
    
    for pattern in forbidden_patterns:
        assert pattern not in content, f"Found forbidden manual parsing: {pattern}"
    
    # SHOULD contain structured output usage
    assert 'response_format=' in content
    assert '.message.parsed' in content


def test_structured_output_consistency():
    """Test all LLM calls use proper structured output"""
    synthesizer = create_test_synthesizer()
    
    # Mock structured response
    mock_grouping = SemanticGrouping(
        groups=[
            SemanticGroup(
                group_theme="Test theme",
                datapoint_ids=["dp1", "dp2"],
                relevance_to_goal=0.8,
                synthesis_worthy=True
            )
        ],
        rationale="Test grouping"
    )
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_grouping
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response) as mock_llm:
        result = synthesizer._group_semantically_llm([])
        
        # Verify structured output was used
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args[1]
        assert 'response_format' in call_args
        assert call_args['response_format'] == SemanticGrouping
        
        # Verify structured result returned
        assert isinstance(result, SemanticGrouping)


def test_insight_synthesis_structured_output():
    """Test insight synthesis uses structured output"""
    synthesizer = create_test_synthesizer()
    
    mock_insight = InsightSynthesis(
        title="Test Insight",
        content="Test insight content", 
        confidence_level=0.8,
        pattern_type="trend",
        key_evidence=["Evidence 1"],
        investigation_relevance=0.9
    )
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_insight
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response):
        group = [
            create_mock_datapoint("test content 1"),
            create_mock_datapoint("test content 2")  # Need at least 2 datapoints
        ]
        result = synthesizer._synthesize_group_insight(group)
        
        assert isinstance(result, InsightSynthesis)
        assert result.title == "Test Insight"
        assert result.confidence_level == 0.8


def test_synthesis_decision_structured_output():
    """Test synthesis decision uses structured output"""
    synthesizer = create_test_synthesizer()
    
    mock_decision = SynthesisDecision(
        should_synthesize=True,
        reasoning="Test reasoning",
        synthesis_potential=0.8
    )
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_decision
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response):
        should_synthesize = synthesizer._should_synthesize_llm(["dp1", "dp2", "dp3"])
        
        assert should_synthesize == True


def test_llm_model_consistency():
    """Test all LLM calls use gemini/gemini-2.5-flash model"""
    synthesizer = create_test_synthesizer()
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = Mock()
    
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response) as mock_llm:
        # Test synthesis decision
        synthesizer._should_synthesize_llm(["dp1", "dp2", "dp3"])
        
        # Test semantic grouping  
        synthesizer._group_semantically_llm([])
        
        # Test insight synthesis
        group = [create_mock_datapoint("test content")]
        synthesizer._synthesize_group_insight(group)
        
        # Verify all calls used correct model
        for call in mock_llm.call_args_list:
            args, kwargs = call
            assert kwargs.get('model') == "gemini/gemini-2.5-flash"


def create_test_synthesizer():
    """Create test synthesizer with mocked dependencies"""
    context = InvestigationContext("Test investigation", [], "twitter")
    context.investigation_id = "test_id"
    context.analytic_question = "Test question"
    context.goal_keywords = ["test", "keyword"]
    graph = InvestigationGraph()
    llm_client = Mock(spec=LiteLLMClient)
    return RealTimeInsightSynthesizer(llm_client, graph, context)


def create_mock_datapoint(content: str):
    """Create mock DataPoint node"""
    mock_dp = Mock()
    mock_dp.id = "test_dp"
    mock_dp.properties = {"content": content}
    mock_dp.node_type = "DataPoint"
    return mock_dp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])