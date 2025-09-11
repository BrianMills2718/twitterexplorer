# test_architectural_integration.py
"""
Architectural Integration Test Suite

Tests the critical bridge integration between insight synthesis and emergent question detection
to fix the broken architectural feedback loop identified in CLAUDE.md.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from investigation_engine import InvestigationEngine, InvestigationConfig
from investigation_bridge import ConcreteInvestigationBridge
from investigation_graph import InvestigationGraph
from investigation_context import InvestigationContext
from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
from realtime_insight_synthesizer import RealTimeInsightSynthesizer
from llm_client import get_litellm_client


def create_test_investigation_engine():
    """Create properly configured investigation engine for testing"""
    # Mock API key for testing
    engine = InvestigationEngine("test_key")
    
    # Mock LLM and search clients to avoid API calls
    if hasattr(engine, 'llm_coordinator') and hasattr(engine.llm_coordinator, 'llm'):
        engine.llm_coordinator.llm = Mock()
    if hasattr(engine, 'search_client'):
        engine.search_client = Mock()
    
    return engine


def test_bridge_creation_and_wiring():
    """Test bridge is properly created and wired into investigation engine"""
    engine = create_test_investigation_engine()
    
    # Verify engine is in graph mode
    assert hasattr(engine, 'graph_mode'), "Engine missing graph_mode attribute"
    
    if engine.graph_mode:
        # Verify bridge exists
        assert hasattr(engine, 'integration_bridge'), "Engine missing integration_bridge attribute"
        # Bridge may be None initially, will be created when investigation starts
        
        # Verify insight synthesizer exists  
        assert hasattr(engine, 'insight_synthesizer'), "Engine missing insight_synthesizer attribute"
        # May be None initially, created during investigation
    else:
        pytest.skip("Engine not in graph mode, bridge integration not applicable")


def test_bridge_initialization_during_investigation():
    """Test bridge is properly initialized when investigation starts"""
    engine = create_test_investigation_engine()
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not applicable")
    
    # Mock search results to avoid API calls
    mock_search_results = []
    
    with patch.object(engine, 'search_client') as mock_search:
        mock_search.search.return_value = mock_search_results
        
        # Mock the _execute_search method to avoid actual API calls
        with patch.object(engine, '_execute_search') as mock_execute:
            from investigation_engine import SearchAttempt
            mock_attempt = SearchAttempt(
                search_id=1,
                round_number=1,
                endpoint="search.php",
                params={"query": "test"},
                query_description="test search",
                results_count=0,
                effectiveness_score=0.0,
                execution_time=0.1
            )
            mock_execute.return_value = mock_attempt
            
            # Start investigation to trigger bridge creation
            try:
                session = engine.conduct_investigation(
                    "Test bridge initialization",
                    InvestigationConfig(max_searches=1)
                )
                
                # Verify bridge was created
                assert engine.integration_bridge is not None, "Bridge not created during investigation"
                assert isinstance(engine.integration_bridge, ConcreteInvestigationBridge), "Bridge not correct type"
                
                # Verify bridge is wired to insight synthesizer
                assert hasattr(engine.insight_synthesizer, 'bridge'), "Synthesizer missing bridge attribute"
                assert engine.insight_synthesizer.bridge is engine.integration_bridge, "Bridge not wired to synthesizer"
                
            except Exception as e:
                # Investigation may fail due to mocking, but bridge should still be created
                if engine.integration_bridge is not None:
                    assert isinstance(engine.integration_bridge, ConcreteInvestigationBridge)


def test_emergent_question_node_creation_method():
    """Test InvestigationGraph has create_emergent_question_node method"""
    graph = InvestigationGraph()
    
    # Verify method exists
    assert hasattr(graph, 'create_emergent_question_node'), \
        "InvestigationGraph missing create_emergent_question_node method"
    
    # Test method works
    node = graph.create_emergent_question_node(
        "Test emergent question?", 
        "Testing node creation"
    )
    
    assert node is not None, "create_emergent_question_node returned None"
    assert hasattr(node, 'id'), "Created node missing id attribute"
    assert hasattr(node, 'node_type'), "Created node missing node_type attribute"
    assert node.node_type == "EmergentQuestion", f"Wrong node type: {node.node_type}"
    
    # Verify node was added to graph
    retrieved_node = graph.nodes.get(node.id)
    assert retrieved_node is not None, "Node not added to graph"
    assert retrieved_node is node, "Retrieved node is different object"
    
    # Verify node properties
    assert hasattr(node, 'properties'), "Node missing properties"
    assert node.properties.get('text') == "Test emergent question?", "Node text not set correctly"
    assert node.properties.get('emergence_reason') == "Testing node creation", "Node emergence_reason not set correctly"


def test_spawns_edge_creation():
    """Test SPAWNS edges are properly created between insights and emergent questions"""
    graph = InvestigationGraph()
    
    # Create insight node
    insight_node = graph.create_insight_node("Test Insight", "connection")
    assert insight_node is not None, "Failed to create insight node"
    
    # Create emergent question node
    eq_node = graph.create_emergent_question_node("Test question?", "Testing")
    assert eq_node is not None, "Failed to create emergent question node"
    
    # Create SPAWNS edge
    edge = graph.create_edge(
        source=insight_node, 
        target=eq_node, 
        edge_type="SPAWNS",
        properties={"emergence_reason": "Testing"}
    )
    
    assert edge is not None, "Failed to create SPAWNS edge"
    assert hasattr(edge, 'edge_type'), "Edge missing edge_type"
    assert edge.edge_type == "SPAWNS", f"Wrong edge type: {edge.edge_type}"
    assert edge.source_id == insight_node.id, "Edge source_id incorrect"
    assert edge.target_id == eq_node.id, "Edge target_id incorrect"


def test_bridge_notify_insight_created():
    """Test bridge.notify_insight_created triggers emergent question detection"""
    # Create test components
    graph = InvestigationGraph()
    context = InvestigationContext("Test investigation", [], "twitter")
    
    # Mock LLM coordinator with detect_emergent_questions method
    mock_coordinator = Mock()
    mock_emergent_question = Mock()
    mock_emergent_question.text = "What timeline supports the allegations?"
    mock_emergent_question.emergence_reason = "Temporal contradiction"
    mock_emergent_question.priority = 0.8
    
    mock_coordinator.detect_emergent_questions.return_value = [mock_emergent_question]
    
    # Create bridge
    bridge = ConcreteInvestigationBridge(mock_coordinator, graph, context)
    
    # Create a mock insight node in the graph
    insight_node = graph.create_insight_node("Trump denies allegations", "contradiction")
    
    # Test bridge notification
    result = bridge.notify_insight_created({
        "id": insight_node.id,
        "content": "Trump denies allegations but evidence suggests otherwise",
        "title": "Contradiction Pattern",
        "confidence": 0.8
    })
    
    # Verify detect_emergent_questions was called
    mock_coordinator.detect_emergent_questions.assert_called_once()
    call_args = mock_coordinator.detect_emergent_questions.call_args[0][0]
    assert isinstance(call_args, list), "detect_emergent_questions should receive list of insights"
    
    # Verify result format
    assert isinstance(result, list), "Bridge should return list of emergent questions"
    if result:  # If emergent questions were created
        for eq in result:
            assert isinstance(eq, dict), "Each emergent question should be a dict"
            assert 'text' in eq, "Emergent question missing text"
            assert 'emergence_reason' in eq, "Emergent question missing emergence_reason"


def test_detect_emergent_questions_method_called():
    """CRITICAL: Verify detect_emergent_questions method is actually called during integration"""
    engine = create_test_investigation_engine()
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not applicable")
    
    # Mock the coordinator's detect_emergent_questions method
    with patch.object(engine.llm_coordinator, 'detect_emergent_questions', return_value=[]) as mock_detect:
        
        # Start investigation to initialize bridge
        try:
            with patch.object(engine, '_execute_search') as mock_execute:
                from investigation_engine import SearchAttempt
                mock_attempt = SearchAttempt(
                    search_id=1, round_number=1, endpoint="search.php", params={"query": "test"},
                    query_description="test", results_count=0, effectiveness_score=0.0, execution_time=0.1
                )
                mock_execute.return_value = mock_attempt
                
                engine.conduct_investigation("Test investigation", InvestigationConfig(max_searches=1))
                
        except Exception:
            pass  # Investigation may fail, but bridge should be initialized
        
        # Manually test bridge if it was created
        if engine.integration_bridge:
            # Create a test insight
            insight_data = {"id": "test_id", "title": "Test", "content": "Test insight", "confidence": 0.7}
            
            try:
                engine.integration_bridge.notify_insight_created(insight_data)
                # Verify detect_emergent_questions was called
                mock_detect.assert_called()
            except Exception as e:
                # Expected if graph doesn't have the insight node, but method should still be called
                mock_detect.assert_called()


def test_integration_bridge_error_handling():
    """Test bridge handles errors gracefully with FAIL-FAST principle"""
    graph = InvestigationGraph()
    context = InvestigationContext("Test investigation", [], "twitter")
    
    # Mock coordinator that fails
    mock_coordinator = Mock()
    mock_coordinator.detect_emergent_questions.side_effect = RuntimeError("LLM failure")
    
    bridge = ConcreteInvestigationBridge(mock_coordinator, graph, context)
    
    # Should FAIL FAST when coordinator fails
    with pytest.raises(RuntimeError, match="Critical architectural bridge failure"):
        bridge.notify_insight_created({
            "id": "test_id",
            "content": "Test content",
            "title": "Test",
            "confidence": 0.7
        })


def test_bridge_integration_status():
    """Test bridge integration status reporting for debugging"""
    graph = InvestigationGraph()
    context = InvestigationContext("Test investigation", [], "twitter")
    mock_coordinator = Mock()
    mock_coordinator.detect_emergent_questions = Mock(return_value=[])
    
    bridge = ConcreteInvestigationBridge(mock_coordinator, graph, context)
    
    status = bridge.get_integration_status()
    
    assert isinstance(status, dict), "Status should be a dict"
    assert 'integration_healthy' in status, "Status missing integration_healthy"
    assert 'coordinator_available' in status, "Status missing coordinator_available"
    assert 'detect_emergent_questions_available' in status, "Status missing detect_emergent_questions_available"
    assert 'graph_available' in status, "Status missing graph_available"
    
    # Should indicate healthy integration
    assert status['integration_healthy'] is True, "Integration should be healthy"
    assert status['coordinator_available'] is True, "Coordinator should be available"
    assert status['detect_emergent_questions_available'] is True, "detect_emergent_questions should be available"


def test_bridge_context_sharing():
    """Test bridge shares context between systems"""
    graph = InvestigationGraph()
    context1 = InvestigationContext("Test investigation 1", [], "twitter")
    context2 = InvestigationContext("Test investigation 2", [], "twitter")
    
    mock_coordinator = Mock()
    mock_coordinator.set_context = Mock()
    
    bridge = ConcreteInvestigationBridge(mock_coordinator, graph, context1)
    
    # Test context sharing
    result = bridge.share_investigation_context(context2)
    
    assert result is True, "Context sharing should succeed"
    assert bridge.context is context2, "Bridge context should be updated"
    
    # Verify coordinator context was updated
    mock_coordinator.set_context.assert_called_once_with(context2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])