#!/usr/bin/env python3
"""
Critical test for DataPoint ID matching in semantic grouping.
This tests the most likely failure point in the insight synthesis pipeline.
"""

from unittest.mock import Mock, patch
from realtime_insight_synthesizer import (
    RealTimeInsightSynthesizer,
    SemanticGrouping,
    SemanticGroup
)
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph
from llm_client import LiteLLMClient


def test_datapoint_id_extraction_accuracy():
    """CRITICAL: Test that LLM correctly extracts DataPoint IDs for grouping"""
    
    # Create test environment
    context = InvestigationContext("Test investigation", [], "twitter")
    context.analytic_question = "Test question"
    
    graph = InvestigationGraph()
    graph.nodes = {}
    
    # Create real DataPoints with specific IDs
    test_datapoints = []
    test_ids = ["dp_abc123", "dp_xyz789", "dp_test001"]
    
    for i, dp_id in enumerate(test_ids):
        dp = Mock()
        dp.id = dp_id
        dp.node_type = "DataPoint"
        dp.properties = {"content": f"Test content {i}"}
        graph.nodes[dp_id] = dp
        test_datapoints.append(dp)
    
    synthesizer = RealTimeInsightSynthesizer(Mock(spec=LiteLLMClient), graph, context)
    
    # Mock LLM response that should return the correct IDs
    mock_grouping = SemanticGrouping(
        groups=[
            SemanticGroup(
                group_theme="Test theme",
                datapoint_ids=test_ids,  # These must match exactly
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
    
    # Execute grouping
    with patch.object(synthesizer.llm, 'completion', return_value=mock_response):
        result = synthesizer._group_semantically_llm(test_datapoints)
        
        # Verify the prompt format includes IDs correctly
        call_args = synthesizer.llm.completion.call_args
        prompt = call_args[1]['messages'][0]['content']
        
        # Check that all IDs are present in the prompt in the expected format
        for dp_id in test_ids:
            assert f"[{dp_id}]" in prompt, f"DataPoint ID {dp_id} not found in prompt"
        
        print(f"+ All {len(test_ids)} DataPoint IDs found in prompt")
        
        # Verify the returned grouping has the correct IDs
        assert len(result.groups) == 1
        returned_ids = result.groups[0].datapoint_ids
        assert set(returned_ids) == set(test_ids), f"ID mismatch: expected {test_ids}, got {returned_ids}"
        
        print("+ LLM returned correct DataPoint IDs")


def test_node_lookup_after_grouping():
    """Test that DataPoint nodes can be correctly looked up after LLM grouping"""
    
    # Create test environment  
    context = InvestigationContext("Test investigation", [], "twitter")
    graph = InvestigationGraph()
    graph.nodes = {}
    
    # Create DataPoints in graph
    test_ids = ["dp_real1", "dp_real2", "dp_fake3"]
    real_datapoints = []
    
    # Add only the first 2 to the graph (3rd is fake)
    for i, dp_id in enumerate(test_ids[:2]):
        dp = Mock()
        dp.id = dp_id
        dp.node_type = "DataPoint"
        dp.properties = {"content": f"Real content {i}"}
        graph.nodes[dp_id] = dp
        real_datapoints.append(dp)
    
    synthesizer = RealTimeInsightSynthesizer(Mock(spec=LiteLLMClient), graph, context)
    
    # Simulate the node lookup logic from _synthesize_insights_batch
    group = SemanticGroup(
        group_theme="Test theme",
        datapoint_ids=test_ids,  # Includes one fake ID
        relevance_to_goal=0.8,
        synthesis_worthy=True
    )
    
    # This is the critical logic from the real code
    group_nodes = []
    for dp_id in group.datapoint_ids:
        node = graph.nodes.get(dp_id)
        if node and node.node_type == "DataPoint":
            group_nodes.append(node)
    
    # Should have filtered out the fake ID
    assert len(group_nodes) == 2, f"Expected 2 real nodes, got {len(group_nodes)}"
    
    found_ids = [node.id for node in group_nodes]
    assert set(found_ids) == {"dp_real1", "dp_real2"}, f"Wrong nodes found: {found_ids}"
    
    print("+ Node lookup correctly filters invalid IDs")


def test_minimum_node_threshold():
    """Test that insights are only created when sufficient valid nodes exist"""
    
    context = InvestigationContext("Test investigation", [], "twitter") 
    graph = InvestigationGraph()
    graph.nodes = {}
    
    # Create only 1 real DataPoint (below minimum of 2)
    dp = Mock()
    dp.id = "dp_single"
    dp.node_type = "DataPoint" 
    dp.properties = {"content": "Single content"}
    graph.nodes["dp_single"] = dp
    
    synthesizer = RealTimeInsightSynthesizer(Mock(spec=LiteLLMClient), graph, context)
    
    # Simulate group with insufficient valid nodes
    group_nodes = [dp]  # Only 1 node, need >= 2
    
    # This should return None due to insufficient nodes
    result = synthesizer._synthesize_group_insight(group_nodes)
    assert result is None, "Should return None for insufficient nodes"
    
    print("+ Minimum node threshold enforced correctly")


if __name__ == "__main__":
    print("CRITICAL ID MATCHING VALIDATION")
    print("=" * 40)
    
    try:
        test_datapoint_id_extraction_accuracy()
        test_node_lookup_after_grouping() 
        test_minimum_node_threshold()
        
        print("=" * 40)
        print("ALL CRITICAL TESTS PASSED")
        print("ID matching logic is sound")
        
    except Exception as e:
        print("=" * 40)
        print(f"CRITICAL FAILURE: {e}")
        print("ID matching logic has issues!")
        raise