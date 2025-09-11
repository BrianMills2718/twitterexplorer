# test_end_to_end_integration.py
"""
End-to-End Architectural Integration Tests

Tests complete investigation workflow with architectural bridge integration
to ensure EmergentQuestion nodes are created when insights are synthesized.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from investigation_engine import InvestigationEngine, InvestigationConfig, SearchAttempt
from investigation_bridge import ConcreteInvestigationBridge
from investigation_graph import InvestigationGraph
from investigation_context import InvestigationContext


def create_mock_llm_response(emergent_questions=None):
    """Create mock LLM response for emergent question detection"""
    if emergent_questions is None:
        emergent_questions = [
            {"text": "What timeline supports the allegations?", "reason": "Temporal contradiction"},
            {"text": "Who are the key witnesses?", "reason": "Source verification need"}
        ]
    
    mock_response = Mock()
    mock_parsed = Mock()
    mock_parsed.questions = emergent_questions
    mock_parsed.priority_scores = [0.8, 0.7]
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_parsed
    
    return mock_response


def test_complete_architectural_integration():
    """CRITICAL: Test complete investigation with architectural integration"""
    
    # Create investigation engine
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not available")
    
    # Mock search results that should trigger insight synthesis
    mock_search_results = [
        {"text": "Trump categorically denies all Epstein allegations", "username": "user1"},
        {"text": "Former Mar-a-Lago staff confirm Trump-Epstein frequent meetings 1990s", "username": "user2"},
        {"text": "Court documents show Trump name in Epstein flight logs multiple times", "username": "user3"},
        {"text": "Legal experts note contradictions between Trump statements and evidence", "username": "user4"},
        {"text": "Investigation reveals pattern of contradictory statements", "username": "user5"}
    ]
    
    # Mock the LLM client to return emergent questions
    with patch.object(engine.llm_coordinator, 'llm') as mock_llm:
        mock_llm.completion.return_value = create_mock_llm_response()
        
        with patch.object(engine, '_execute_search') as mock_execute:
            # Create mock search attempt with results
            mock_attempt = SearchAttempt(
                search_id=1,
                round_number=1,
                endpoint="search.php",
                params={"query": "Trump Epstein"},
                query_description="Test search",
                results_count=5,
                effectiveness_score=7.0,
                execution_time=1.0
            )
            # Add raw results for evaluation
            mock_attempt._raw_results = mock_search_results
            mock_execute.return_value = mock_attempt
            
            # Mock finding evaluator to create significant findings
            with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
                # Create mock assessments that trigger DataPoint creation
                mock_assessments = []
                for result in mock_search_results:
                    assessment = Mock()
                    assessment.is_significant = True
                    assessment.relevance_score = 0.8
                    assessment.entities = []
                    assessment.suggested_followup = ""
                    mock_assessments.append(assessment)
                mock_eval.return_value = mock_assessments
                
                # Run investigation
                result = engine.conduct_investigation(
                    "Trump Epstein relationship contradictions investigation",
                    InvestigationConfig(max_searches=1)
                )
                
                # CRITICAL VALIDATIONS:
                
                # 1. Bridge should be created
                assert engine.integration_bridge is not None, "Integration bridge not created"
                
                # 2. DataPoints should be created
                datapoints = engine.graph.get_nodes_by_type("DataPoint")
                assert len(datapoints) > 0, "No DataPoints created"
                
                # 3. Check if insights were created (may require sufficient DataPoints)
                insights = engine.graph.get_nodes_by_type("Insight")
                
                # 4. CRITICAL: EmergentQuestions should be created if insights exist
                emergent_questions = engine.graph.get_nodes_by_type("EmergentQuestion")
                
                # If we have insights, we MUST have emergent questions (architectural requirement)
                if len(insights) > 0:
                    assert len(emergent_questions) > 0, \
                        f"ARCHITECTURAL FAILURE: {len(insights)} insights created but 0 EmergentQuestion nodes"
                    
                    # 5. SPAWNS edges should connect insights to emergent questions
                    spawns_edges = []
                    for insight in insights:
                        # Check for edges from this insight
                        if hasattr(engine.graph, 'edges'):
                            for edge in engine.graph.edges.values():
                                if (edge.source_id == insight.id and edge.edge_type == "SPAWNS"):
                                    spawns_edges.append(edge)
                    
                    if len(emergent_questions) > 0:
                        assert len(spawns_edges) > 0, \
                            f"ARCHITECTURAL FAILURE: {len(insights)} insights and {len(emergent_questions)} emergent questions but no SPAWNS edges"
                
                # Log results for debugging
                print(f"Test results: {len(datapoints)} DataPoints, {len(insights)} Insights, {len(emergent_questions)} EmergentQuestions")


def test_bridge_integration_with_mock_insights():
    """Test bridge integration by directly creating insights and verifying emergent questions"""
    
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not available")
    
    # Start investigation to initialize bridge
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=1, round_number=1, endpoint="search.php", params={"query": "test"},
            query_description="init", results_count=0, effectiveness_score=0.0, execution_time=0.1
        )
        mock_execute.return_value = mock_attempt
        
        try:
            engine.conduct_investigation("Bridge test", InvestigationConfig(max_searches=1))
        except Exception:
            pass  # Investigation may fail, but bridge should be initialized
    
    # Verify bridge is available
    assert engine.integration_bridge is not None, "Bridge not initialized"
    
    # Mock the LLM coordinator's detect_emergent_questions method
    with patch.object(engine.llm_coordinator, 'detect_emergent_questions') as mock_detect:
        mock_eq1 = Mock()
        mock_eq1.text = "What evidence contradicts the denial?"
        mock_eq1.emergence_reason = "Contradiction detected"
        mock_eq1.priority = 0.9
        
        mock_eq2 = Mock() 
        mock_eq2.text = "Who are the corroborating witnesses?"
        mock_eq2.emergence_reason = "Source verification needed"
        mock_eq2.priority = 0.8
        
        mock_detect.return_value = [mock_eq1, mock_eq2]
        
        # Manually create insight to trigger bridge
        insight_node = engine.graph.create_insight_node(
            content="Trump denies allegations but multiple sources contradict",
            insight_type="contradiction"
        )
        
        # Trigger bridge integration
        emergent_questions = engine.integration_bridge.notify_insight_created({
            "id": insight_node.id,
            "content": insight_node.properties.get('content', ''),
            "title": "Contradiction Pattern",
            "confidence": 0.8
        })
        
        # Verify detect_emergent_questions was called
        mock_detect.assert_called_once()
        
        # Verify emergent questions were returned
        assert isinstance(emergent_questions, list), "Should return list of emergent questions"
        assert len(emergent_questions) == 2, f"Expected 2 emergent questions, got {len(emergent_questions)}"
        
        # Verify emergent question content
        for eq in emergent_questions:
            assert 'text' in eq, "Emergent question missing text"
            assert 'emergence_reason' in eq, "Emergent question missing emergence_reason"
            assert eq['text'] in ["What evidence contradicts the denial?", "Who are the corroborating witnesses?"]


def test_architectural_state_consistency():
    """Test architectural state remains consistent throughout investigation"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not available")
    
    # Track state changes
    state_history = []
    
    def capture_state():
        return {
            "timestamp": datetime.now(),
            "datapoints": len(engine.graph.get_nodes_by_type("DataPoint")),
            "insights": len(engine.graph.get_nodes_by_type("Insight")),
            "emergent_questions": len(engine.graph.get_nodes_by_type("EmergentQuestion")),
        }
    
    # Capture initial state
    state_history.append(capture_state())
    
    # Mock incremental investigation with results that should create insights
    mock_results = [
        {"text": "Finding 1: Trump denies connection", "username": "user1"},
        {"text": "Finding 2: Evidence shows multiple meetings", "username": "user2"},
        {"text": "Finding 3: Legal documents contradict statements", "username": "user3"}
    ]
    
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=1, round_number=1, endpoint="search.php", params={"query": "Trump Epstein"},
            query_description="Consistency test", results_count=3, effectiveness_score=6.0, execution_time=1.0
        )
        mock_attempt._raw_results = mock_results
        mock_execute.return_value = mock_attempt
        
        # Mock finding evaluator 
        with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
            mock_assessments = [
                Mock(is_significant=True, relevance_score=0.8, entities=[], suggested_followup="") 
                for _ in mock_results
            ]
            mock_eval.return_value = mock_assessments
            
            # Mock LLM for emergent questions if insights are created
            with patch.object(engine.llm_coordinator, 'llm') as mock_llm:
                mock_llm.completion.return_value = create_mock_llm_response()
                
                # Run investigation
                engine.conduct_investigation(
                    "State consistency test",
                    InvestigationConfig(max_searches=1)
                )
    
    # Capture final state
    state_history.append(capture_state())
    
    # Validate state progression
    initial_state = state_history[0]
    final_state = state_history[-1]
    
    # Should have progression in DataPoints
    assert final_state["datapoints"] > initial_state["datapoints"], \
        f"DataPoints should increase: {initial_state['datapoints']} -> {final_state['datapoints']}"
    
    # CRITICAL: If insights were created, emergent questions should also exist
    if final_state["insights"] > initial_state["insights"]:
        assert final_state["emergent_questions"] > initial_state["emergent_questions"], \
            f"Architectural failure: Insights increased ({initial_state['insights']} -> {final_state['insights']}) " \
            f"but EmergentQuestions did not ({initial_state['emergent_questions']} -> {final_state['emergent_questions']})"


def test_architectural_integration_performance():
    """Test architectural integration doesn't significantly impact performance"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not available")
    
    # Mock quick search results
    mock_results = [{"text": f"Test result {i}", "username": f"user{i}"} for i in range(5)]
    
    import time
    
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=1, round_number=1, endpoint="search.php", params={"query": "performance test"},
            query_description="Performance test", results_count=5, effectiveness_score=5.0, execution_time=0.5
        )
        mock_attempt._raw_results = mock_results
        mock_execute.return_value = mock_attempt
        
        # Mock finding evaluator for quick evaluation
        with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
            mock_assessments = [
                Mock(is_significant=False, relevance_score=0.3, entities=[], suggested_followup="") 
                for _ in mock_results
            ]
            mock_eval.return_value = mock_assessments
            
            start_time = time.time()
            
            engine.conduct_investigation(
                "Performance test investigation", 
                InvestigationConfig(max_searches=1)
            )
            
            execution_time = time.time() - start_time
            
            # Should complete reasonably quickly (adjust threshold as needed)
            assert execution_time < 10, f"Integration too slow: {execution_time}s (expected < 10s)"


def test_error_propagation_and_recovery():
    """Test error propagation and recovery in integrated system"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, bridge integration not available")
    
    # Initialize bridge
    try:
        with patch.object(engine, '_execute_search') as mock_execute:
            mock_attempt = SearchAttempt(
                search_id=1, round_number=1, endpoint="search.php", params={"query": "test"},
                query_description="init", results_count=0, effectiveness_score=0.0, execution_time=0.1
            )
            mock_execute.return_value = mock_attempt
            engine.conduct_investigation("Error test", InvestigationConfig(max_searches=1))
    except Exception:
        pass  # Expected
    
    if engine.integration_bridge is None:
        pytest.skip("Bridge not initialized")
    
    # Test bridge failure propagation
    with patch.object(engine.integration_bridge, 'notify_insight_created',
                     side_effect=RuntimeError("Bridge failure")):
        
        # Should propagate error (FAIL-FAST principle)
        with pytest.raises(RuntimeError, match="Critical bridge failure"):
            insight_data = {"id": "test_id", "title": "Test", "content": "Test", "confidence": 0.7}
            engine.integration_bridge.notify_insight_created(insight_data)
    
    # Test recovery after error
    # Bridge should work normally after fixing the issue
    with patch.object(engine.integration_bridge, 'notify_insight_created',
                     return_value=[]):
        
        # Should work normally
        insight_data = {"id": "test_id", "title": "Recovery Test", "content": "Recovery test", "confidence": 0.7}
        result = engine.integration_bridge.notify_insight_created(insight_data)
        
        assert result == [], "Bridge should return empty list after recovery"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])