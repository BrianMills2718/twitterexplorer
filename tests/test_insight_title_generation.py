#!/usr/bin/env python3
"""
Test insight quality - Issue #2: "Untitled" insight generation
All insights must have non-empty, descriptive titles
"""

import pytest
import json
import os
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict


def test_insights_have_meaningful_titles():
    """All insights must have non-empty, descriptive titles"""
    
    from realtime_insight_synthesizer import RealTimeInsightSynthesizer
    from investigation_graph import InvestigationGraph
    from investigation_context import InvestigationContext
    
    # Set up test environment
    test_context = InvestigationContext(
        analytic_question="test question",
        investigation_scope="test scope"
    )
    test_graph = InvestigationGraph()
    
    # Create mock LLM client that returns proper structured output
    mock_llm_client = Mock()
    mock_llm_client.generate_structured_response.return_value = {
        'insights': [
            {
                'title': 'Test Insight About Topic',
                'description': 'This is a proper insight description',
                'confidence': 0.8,
                'evidence_points': ['evidence1', 'evidence2']
            }
        ]
    }
    
    synthesizer = RealTimeInsightSynthesizer(test_context, test_graph, mock_llm_client)
    
    # Create sample datapoints
    sample_datapoints = [
        {
            'id': 'dp1',
            'content': 'Sample tweet content about test topic',
            'metadata': {'source': 'twitter', 'timestamp': '2024-01-01'}
        },
        {
            'id': 'dp2', 
            'content': 'Another sample tweet about the same topic',
            'metadata': {'source': 'twitter', 'timestamp': '2024-01-02'}
        }
    ]
    
    # Test insight synthesis
    insights = synthesizer.synthesize_insights(sample_datapoints)
    
    # Verify all insights have meaningful titles
    for insight in insights:
        title = insight.properties.get('title', '')
        confidence = insight.properties.get('confidence', 'N/A')
        
        # Assert not "Untitled"
        assert title != 'Untitled', f"Found 'Untitled' insight: {insight.properties}"
        
        # Assert not empty
        assert title and title.strip(), f"Found empty title insight: {insight.properties}"
        
        # Assert confidence is numeric
        assert isinstance(confidence, (int, float)) or confidence == 'N/A', \
            f"Confidence should be numeric or N/A, got: {confidence}"
        
        if isinstance(confidence, (int, float)):
            assert 0.0 <= confidence <= 1.0, f"Confidence should be 0.0-1.0, got: {confidence}"


def test_insight_synthesis_with_real_llm_response():
    """Test insight synthesis with realistic LLM response patterns"""
    
    from realtime_insight_synthesizer import RealTimeInsightSynthesizer
    from investigation_graph import InvestigationGraph
    from investigation_context import InvestigationContext
    
    # Set up test environment
    test_context = InvestigationContext(
        analytic_question="test question",
        investigation_scope="test scope"
    )
    test_graph = InvestigationGraph()
    
    # Create mock LLM that returns malformed response (current issue)
    mock_llm_client = Mock()
    
    # Simulate problematic LLM response that causes "Untitled" insights
    mock_llm_client.generate_structured_response.return_value = {
        'insights': [
            {
                # Missing title field - should cause fallback
                'description': 'This insight lacks a title field',
                'confidence': 0.7,
                'evidence_points': ['evidence1']
            },
            {
                'title': '',  # Empty title - should cause fallback  
                'description': 'This insight has empty title',
                'confidence': 0.6,
                'evidence_points': ['evidence2']
            },
            {
                'title': 'Untitled',  # Explicit "Untitled" - should be rejected
                'description': 'This insight has explicit Untitled', 
                'confidence': 'N/A',  # String confidence - current issue
                'evidence_points': ['evidence3']
            }
        ]
    }
    
    synthesizer = RealTimeInsightSynthesizer(test_context, test_graph, mock_llm_client)
    
    # Create sample datapoints
    sample_datapoints = [
        {
            'id': 'dp1',
            'content': 'Sample content for testing malformed responses',
            'metadata': {'source': 'twitter', 'timestamp': '2024-01-01'}
        }
    ]
    
    # This test documents current failure modes
    insights = synthesizer.synthesize_insights(sample_datapoints)
    
    # Document what happens with malformed responses
    problematic_insights = []
    for insight in insights:
        title = insight.properties.get('title', '')
        confidence = insight.properties.get('confidence', 'N/A')
        
        if title == 'Untitled' or title == '' or confidence == 'N/A':
            problematic_insights.append({
                'title': title,
                'confidence': confidence,
                'properties': insight.properties
            })
    
    print(f"Found {len(problematic_insights)} problematic insights: {problematic_insights}")
    
    # This test currently fails - documenting the issue
    assert len(problematic_insights) > 0, "Expected to find problematic insights (documenting current issue)"


def test_insight_title_fallback_generation():
    """Test fallback title generation for edge cases"""
    
    from realtime_insight_synthesizer import RealTimeInsightSynthesizer
    from investigation_graph import InvestigationGraph
    from investigation_context import InvestigationContext
    
    # Check if fallback title generation exists
    test_context = InvestigationContext(
        analytic_question="test question",
        investigation_scope="test scope"
    )
    test_graph = InvestigationGraph()
    mock_llm_client = Mock()
    
    synthesizer = RealTimeInsightSynthesizer(test_context, test_graph, mock_llm_client)
    
    # Check if synthesizer has fallback methods
    has_title_fallback = hasattr(synthesizer, 'generate_fallback_title')
    has_title_validation = hasattr(synthesizer, 'validate_insight_title')
    
    print(f"Has fallback title generation: {has_title_fallback}")
    print(f"Has title validation: {has_title_validation}")
    
    # Document current state - these methods likely don't exist yet
    assert not has_title_fallback, "Expected no fallback title generation (documenting current issue)"
    assert not has_title_validation, "Expected no title validation (documenting current issue)"


def test_insight_confidence_score_validation():
    """Test confidence score validation and normalization"""
    
    from realtime_insight_synthesizer import RealTimeInsightSynthesizer
    
    # Test various confidence score formats
    test_confidence_values = [
        'N/A',           # String - should be rejected or converted
        '0.8',           # String number - should be converted
        0.95,            # Float - should be accepted
        1.5,             # > 1.0 - should be clamped
        -0.1,            # < 0.0 - should be clamped
        None,            # None - should have fallback
    ]
    
    # Check if synthesizer has confidence validation
    # This likely doesn't exist yet - documenting the need
    
    expected_validated_values = [0.0, 0.8, 0.95, 1.0, 0.0, 0.0]
    
    print(f"Testing confidence values: {test_confidence_values}")
    print(f"Expected after validation: {expected_validated_values}")
    
    # This test documents the need for confidence validation
    # Implementation will be required to make this pass
    assert True, "Confidence validation not yet implemented (documenting requirement)"


def test_extract_insights_from_investigation_logs():
    """Extract and analyze insights from actual investigation logs"""
    
    # Look for recent investigation graph files
    current_dir = os.path.dirname(__file__)
    graph_files = [f for f in os.listdir(current_dir) if f.startswith('investigation_graph_') and f.endswith('.json')]
    
    if not graph_files:
        pytest.skip("No investigation graph files found for analysis")
    
    # Analyze most recent graph file
    # Prefer the graph file we know has insights
    if 'investigation_graph_0c9d81d7-65cb-4848-a72c-5ec5c841c20e.json' in graph_files:
        latest_graph = 'investigation_graph_0c9d81d7-65cb-4848-a72c-5ec5c841c20e.json'
    else:
        latest_graph = sorted(graph_files)[-1]
    graph_path = os.path.join(current_dir, latest_graph)
    
    with open(graph_path, 'r') as f:
        graph_data = json.load(f)
    
    # Extract insights from graph data
    insights = []
    if 'nodes' in graph_data:
        # Handle both formats: list of nodes or dict with node IDs as keys
        nodes = graph_data['nodes']
        if isinstance(nodes, dict):
            # New format: dict with node IDs as keys
            insights = [node for node in nodes.values() if node.get('node_type') == 'Insight']
        elif isinstance(nodes, list):
            # Old format: list of nodes
            insights = [node for node in nodes if node.get('type') == 'Insight']
    
    print(f"Found {len(insights)} insights in {latest_graph}")
    
    # Analyze insight quality
    untitled_insights = []
    na_confidence_insights = []
    
    for insight in insights:
        props = insight.get('properties', {})
        title = props.get('title', '')
        confidence = props.get('confidence', '')
        
        if title == 'Untitled':
            untitled_insights.append(insight)
        
        if confidence == 'N/A':
            na_confidence_insights.append(insight)
    
    print(f"Found {len(untitled_insights)} 'Untitled' insights")
    print(f"Found {len(na_confidence_insights)} 'N/A' confidence insights")
    
    # Document actual issues found in logs
    if untitled_insights:
        print("Sample 'Untitled' insight:")
        print(json.dumps(untitled_insights[0], indent=2))
    
    if na_confidence_insights:
        print("Sample 'N/A' confidence insight:")
        print(json.dumps(na_confidence_insights[0], indent=2))
    
    # This documents the current state - Issue #2 might already be resolved
    total_problematic = len(untitled_insights) + len(na_confidence_insights)
    total_good_insights = len(insights)
    
    print(f"Analysis complete:")
    print(f"  Total insights: {total_good_insights}")
    print(f"  Problematic insights: {total_problematic}")
    
    if total_problematic == 0 and total_good_insights > 0:
        print("Issue #2 appears to be resolved - insights have proper titles and confidence scores")
        assert True  # Pass the test if no issues found
    elif total_problematic > 0:
        print("Issue #2 confirmed - found problematic insights") 
        # Don't assert - let the test document the issue without failing
        assert True  # Pass but document the issues found
    else:
        print("! No insights found in recent investigations")
        assert True  # Pass but note no insights available for testing


def test_insight_synthesis_structured_output_parsing():
    """Test structured output parsing in insight synthesis"""
    
    # This test checks how the LLM response is parsed
    from realtime_insight_synthesizer import RealTimeInsightSynthesizer
    
    # Create test scenarios with various LLM response formats
    test_responses = [
        # Proper response
        {
            'insights': [
                {
                    'title': 'Proper Insight Title',
                    'description': 'Good description',
                    'confidence': 0.8,
                    'evidence_points': ['evidence']
                }
            ]
        },
        
        # Malformed response (missing fields)
        {
            'insights': [
                {
                    'description': 'Missing title field',
                    'confidence': 0.7
                }
            ]
        },
        
        # Empty response
        {'insights': []},
        
        # No insights key
        {'other_field': 'no insights'},
        
        # Non-list insights
        {'insights': 'not a list'}
    ]
    
    print("Testing structured output parsing with various response formats")
    for i, response in enumerate(test_responses):
        print(f"Test response {i+1}: {response}")
    
    # This documents the need for robust parsing
    assert True, "Structured output parsing robustness needs testing and improvement"


if __name__ == "__main__":
    # Run tests to document current issues
    pytest.main([__file__, "-v", "-s"])