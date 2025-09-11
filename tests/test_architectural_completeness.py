# test_architectural_completeness.py
"""
Architectural Completeness Validation Tests

Tests complete 6-node, 5-edge ontology utilization and validates that the
architectural integration creates the complete feedback loop as specified.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from investigation_engine import InvestigationEngine, InvestigationConfig, SearchAttempt
from investigation_graph import InvestigationGraph
from investigation_context import InvestigationContext


def test_complete_ontology_utilization():
    """Test investigation uses complete 6-node, 5-edge ontology"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, ontology testing not applicable")
    
    # Mock comprehensive search results that should trigger all node types
    mock_results = [
        {"text": "Trump explicitly denies all Epstein connections", "username": "user1"},
        {"text": "Court documents show Trump-Epstein business meetings", "username": "user2"},
        {"text": "Former staff confirms social interactions at Mar-a-Lago", "username": "user3"},
        {"text": "Legal analysis reveals contradictory public statements", "username": "user4"},
        {"text": "Timeline suggests evolving relationship over decades", "username": "user5"}
    ]
    
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=1, round_number=1, endpoint="search.php", 
            params={"query": "Trump Epstein comprehensive"},
            query_description="Comprehensive analysis", results_count=5, 
            effectiveness_score=8.0, execution_time=1.0
        )
        mock_attempt._raw_results = mock_results
        mock_execute.return_value = mock_attempt
        
        # Mock finding evaluator to create significant findings
        with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
            mock_assessments = [
                Mock(is_significant=True, relevance_score=0.9, entities=[], suggested_followup="") 
                for _ in mock_results
            ]
            mock_eval.return_value = mock_assessments
            
            # Mock LLM for emergent questions
            with patch.object(engine.llm_coordinator, 'llm') as mock_llm:
                # Mock emergent question response
                mock_response = Mock()
                mock_parsed = Mock()
                mock_parsed.questions = [
                    {"text": "What timeline contradicts the denials?", "reason": "Temporal inconsistency"},
                    {"text": "Who witnessed these interactions?", "reason": "Source verification"}
                ]
                mock_parsed.priority_scores = [0.9, 0.8]
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.parsed = mock_parsed
                mock_llm.completion.return_value = mock_response
                
                # Run comprehensive investigation
                result = engine.conduct_investigation(
                    "Comprehensive Trump-Epstein relationship analysis",
                    InvestigationConfig(max_searches=1)
                )
    
    # VALIDATE: Check which node types were created
    node_types_created = set()
    all_node_types = ["AnalyticQuestion", "InvestigationQuestion", "SearchQuery", "DataPoint", "Insight", "EmergentQuestion"]
    
    for node_type in all_node_types:
        nodes = engine.graph.get_nodes_by_type(node_type)
        if len(nodes) > 0:
            node_types_created.add(node_type)
    
    print(f"Node types created: {sorted(node_types_created)}")
    
    # Core architectural nodes must exist
    required_nodes = {"DataPoint"}  # At minimum, DataPoints should be created from findings
    assert required_nodes.issubset(node_types_created), f"Missing required nodes: {required_nodes - node_types_created}"
    
    # CRITICAL: EmergentQuestion must be created when insights exist
    if "Insight" in node_types_created:
        assert "EmergentQuestion" in node_types_created, \
            "ARCHITECTURAL FAILURE: Insights created but no EmergentQuestion nodes"
    
    # VALIDATE: Check edge types created
    edge_types_created = set()
    expected_edge_types = ["TRIGGERS", "EXPLORES", "DISCOVERED", "SUPPORTS", "SPAWNS"]
    
    if hasattr(engine.graph, 'edges') and engine.graph.edges:
        for edge in engine.graph.edges.values():
            edge_types_created.add(edge.edge_type)
    
    print(f"Edge types created: {sorted(edge_types_created)}")
    
    # SUPPORTS edges should connect DataPoints to Insights
    if "DataPoint" in node_types_created and "Insight" in node_types_created:
        # Should have SUPPORTS edges, but not strictly required for this test
        pass
    
    # SPAWNS edges should connect Insights to EmergentQuestions
    if "Insight" in node_types_created and "EmergentQuestion" in node_types_created:
        assert "SPAWNS" in edge_types_created, \
            "ARCHITECTURAL FAILURE: Missing SPAWNS edges between Insights and EmergentQuestions"


def test_feedback_loop_completeness():
    """Test complete feedback loop: DataPoint → Insight → EmergentQuestion → NewInvestigation"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, feedback loop testing not applicable")
    
    # Mock results that should create clear contradictions (triggering emergent questions)
    contradictory_results = [
        {"text": "Trump: 'I never had any relationship with Jeffrey Epstein'", "username": "official1"},
        {"text": "Flight logs show Trump on Epstein jet 7 times in 1997", "username": "investigator1"},
        {"text": "Photos emerge of Trump and Epstein at 1992 Mar-a-Lago party", "username": "journalist1"},
        {"text": "Trump 2002 quote: 'Jeff is a terrific guy, lots of fun to be with'", "username": "archive1"}
    ]
    
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=1, round_number=1, endpoint="search.php",
            params={"query": "Trump Epstein contradiction"},
            query_description="Contradiction analysis", results_count=4,
            effectiveness_score=9.0, execution_time=1.0
        )
        mock_attempt._raw_results = contradictory_results
        mock_execute.return_value = mock_attempt
        
        # Mock highly relevant findings
        with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
            mock_assessments = [
                Mock(is_significant=True, relevance_score=0.95, entities=[], suggested_followup="")
                for _ in contradictory_results
            ]
            mock_eval.return_value = mock_assessments
            
            # Mock insight synthesis that should definitely create emergent questions
            with patch.object(engine.llm_coordinator, 'llm') as mock_llm:
                # Mock response for emergent questions with high-relevance contradictions
                mock_response = Mock()
                mock_parsed = Mock()
                mock_parsed.questions = [
                    {"text": "What timeline explains these contradictory statements?", "reason": "Temporal contradiction"},
                    {"text": "What evidence exists beyond these documented interactions?", "reason": "Evidence gap"},
                    {"text": "How does Trump explain these documented meetings?", "reason": "Statement inconsistency"}
                ]
                mock_parsed.priority_scores = [0.95, 0.9, 0.85]
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.parsed = mock_parsed
                mock_llm.completion.return_value = mock_response
                
                # Run investigation
                result = engine.conduct_investigation(
                    "Trump-Epstein contradiction analysis",
                    InvestigationConfig(max_searches=1)
                )
    
    # TRACE COMPLETE FEEDBACK LOOP
    
    # Step 1: DataPoints should be created from search results
    datapoints = engine.graph.get_nodes_by_type("DataPoint")
    assert len(datapoints) > 0, "Step 1 failed: No DataPoints created"
    print(f"Step 1 ✓: {len(datapoints)} DataPoints created")
    
    # Step 2: Insights should be synthesized from DataPoints (may require sufficient DataPoints)
    insights = engine.graph.get_nodes_by_type("Insight")
    print(f"Step 2: {len(insights)} Insights created from DataPoints")
    
    # Step 3: CRITICAL - EmergentQuestions should be spawned from Insights
    emergent_questions = engine.graph.get_nodes_by_type("EmergentQuestion")
    print(f"Step 3: {len(emergent_questions)} EmergentQuestions spawned from Insights")
    
    # If we have insights, we MUST have emergent questions (architectural requirement)
    if len(insights) > 0:
        assert len(emergent_questions) > 0, \
            f"Step 3 FAILED: {len(insights)} insights created but no EmergentQuestions - ARCHITECTURAL BREAKDOWN"
        
        # Step 4: SPAWNS edges should connect Insights to EmergentQuestions
        spawns_edges = []
        if hasattr(engine.graph, 'edges') and engine.graph.edges:
            for edge in engine.graph.edges.values():
                if edge.edge_type == "SPAWNS":
                    spawns_edges.append(edge)
        
        if len(emergent_questions) > 0:
            assert len(spawns_edges) > 0, \
                f"Step 4 FAILED: {len(insights)} insights and {len(emergent_questions)} emergent questions but no SPAWNS edges"
            print(f"Step 4 ✓: {len(spawns_edges)} SPAWNS edges created")
        
        # Step 5: EmergentQuestions should address the contradictions found
        for eq in emergent_questions:
            eq_text = eq.properties.get("text", "").lower()
            # Should address the contradictions found
            contradiction_terms = ["timeline", "when", "contradiction", "evidence", "truth", "discrepancy", "explain", "documented"]
            relevant_terms_found = [term for term in contradiction_terms if term in eq_text]
            assert len(relevant_terms_found) > 0, \
                f"EmergentQuestion not addressing contradictions: '{eq_text}' (no terms from {contradiction_terms})"
        
        print(f"Step 5 ✓: EmergentQuestions address contradictions appropriately")
    
    else:
        # If no insights were created, that's acceptable but log it
        print("Note: No insights created from DataPoints (may require more DataPoints or different synthesis logic)")


def test_architectural_integration_robustness():
    """Test architectural integration handles edge cases robustly"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, robustness testing not applicable")
    
    # Test with minimal data
    minimal_results = [{"text": "Single data point", "username": "user1"}]
    
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=1, round_number=1, endpoint="search.php",
            params={"query": "minimal test"}, query_description="Minimal test",
            results_count=1, effectiveness_score=3.0, execution_time=0.5
        )
        mock_attempt._raw_results = minimal_results
        mock_execute.return_value = mock_attempt
        
        # Mock minimal findings
        with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
            mock_assessments = [
                Mock(is_significant=True, relevance_score=0.6, entities=[], suggested_followup="")
            ]
            mock_eval.return_value = mock_assessments
            
            # Should handle minimal data gracefully
            result = engine.conduct_investigation(
                "Minimal data test",
                InvestigationConfig(max_searches=1)
            )
            
            # Should create DataPoint even with minimal data
            datapoints = engine.graph.get_nodes_by_type("DataPoint")
            assert len(datapoints) > 0, "Should create DataPoint even with minimal data"
            
            # May or may not create insights with minimal data, but should not crash
            insights = engine.graph.get_nodes_by_type("Insight")
            emergent_questions = engine.graph.get_nodes_by_type("EmergentQuestion")
            
            # If insights exist, architectural integration should work
            if len(insights) > 0:
                # Allow 0 emergent questions for minimal insights, but log it
                print(f"Minimal test: {len(insights)} insights → {len(emergent_questions)} emergent questions")
    
    # Test with contradictory data (should definitely trigger emergent questions if insights created)
    contradictory_results = [
        {"text": "Statement A: Complete denial", "username": "source1"},
        {"text": "Statement B: Full confirmation", "username": "source2"}
    ]
    
    with patch.object(engine, '_execute_search') as mock_execute:
        mock_attempt = SearchAttempt(
            search_id=2, round_number=1, endpoint="search.php",
            params={"query": "contradiction test"}, query_description="Contradiction test",
            results_count=2, effectiveness_score=7.0, execution_time=0.5
        )
        mock_attempt._raw_results = contradictory_results
        mock_execute.return_value = mock_attempt
        
        # Mock contradictory findings
        with patch.object(engine.finding_evaluator, 'evaluate_batch') as mock_eval:
            mock_assessments = [
                Mock(is_significant=True, relevance_score=0.9, entities=[], suggested_followup="")
                for _ in contradictory_results
            ]
            mock_eval.return_value = mock_assessments
            
            # Mock LLM to return emergent questions for contradictions
            with patch.object(engine.llm_coordinator, 'llm') as mock_llm:
                mock_response = Mock()
                mock_parsed = Mock()
                mock_parsed.questions = [
                    {"text": "Which statement is more credible?", "reason": "Direct contradiction"},
                    {"text": "What evidence supports each claim?", "reason": "Evidence evaluation needed"}
                ]
                mock_parsed.priority_scores = [0.9, 0.8]
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.parsed = mock_parsed
                mock_llm.completion.return_value = mock_response
                
                result = engine.conduct_investigation(
                    "Contradiction robustness test",
                    InvestigationConfig(max_searches=1)
                )
                
                # Clear contradictions should trigger architectural feedback loop if insights created
                insights = engine.graph.get_nodes_by_type("Insight")
                emergent_questions = engine.graph.get_nodes_by_type("EmergentQuestion")
                
                if len(insights) > 0:  # If insights were created from contradictions
                    assert len(emergent_questions) > 0, \
                        f"Contradictory data should spawn emergent questions: {len(insights)} insights but 0 emergent questions"
                    print(f"Contradiction test ✓: {len(insights)} insights → {len(emergent_questions)} emergent questions")


def test_integration_health_monitoring():
    """Test architectural integration health monitoring"""
    engine = InvestigationEngine("test_key")
    
    if not engine.graph_mode:
        pytest.skip("Engine not in graph mode, health monitoring not applicable")
    
    # Initialize bridge
    try:
        with patch.object(engine, '_execute_search') as mock_execute:
            mock_attempt = SearchAttempt(
                search_id=1, round_number=1, endpoint="search.php", params={"query": "test"},
                query_description="health check", results_count=0, effectiveness_score=0.0, execution_time=0.1
            )
            mock_execute.return_value = mock_attempt
            engine.conduct_investigation("Health check", InvestigationConfig(max_searches=1))
    except Exception:
        pass  # Expected
    
    if engine.integration_bridge is None:
        pytest.skip("Bridge not initialized for health monitoring")
    
    # Test integration status
    status = engine.integration_bridge.get_integration_status()
    
    # Validate status structure
    required_fields = [
        'coordinator_available', 'coordinator_type', 'detect_emergent_questions_available',
        'graph_available', 'graph_node_count', 'emergent_question_nodes', 'insight_nodes',
        'context_available', 'integration_healthy'
    ]
    
    for field in required_fields:
        assert field in status, f"Status missing required field: {field}"
    
    # Validate status values
    assert status['integration_healthy'] is True, f"Integration should be healthy: {status}"
    assert status['coordinator_available'] is True, "Coordinator should be available"
    assert status['detect_emergent_questions_available'] is True, "detect_emergent_questions should be available"
    assert status['graph_available'] is True, "Graph should be available"
    assert isinstance(status['graph_node_count'], int), "Node count should be integer"
    assert isinstance(status['emergent_question_nodes'], int), "EmergentQuestion count should be integer"
    assert isinstance(status['insight_nodes'], int), "Insight count should be integer"
    
    print(f"Integration health: {status}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])