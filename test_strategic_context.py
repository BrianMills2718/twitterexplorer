# test_strategic_context.py
"""
Test suite for Strategic Context Generation
EVIDENCE: Strategic context must enable coherent decision making with gap identification
"""

import pytest
import json
from investigation_graph import InvestigationGraph

def test_strategic_context_coherence():
    """EVIDENCE: Strategic context must enable coherent decision making"""
    # Use realistic investigation data
    graph = create_graph_from_baseline_scenario()  
    
    context = graph.get_strategic_context_for_llm()
    
    # Context must include key strategic elements
    assert "ORIGINAL GOAL:" in context
    assert "INFORMATION GAPS:" in context  
    assert "DISCONNECTED THREADS:" in context
    assert "STRATEGIC COHERENCE DECISION POINT:" in context
    
    # Context must be LLM-processable 
    assert len(context.split()) < 15000  # Reasonable token count
    assert "FAILED APPROACHES" in context  # Clear failure documentation

def test_gap_identification_algorithm():
    """EVIDENCE: System must identify actual information gaps"""
    graph = InvestigationGraph()
    
    # Create scenario with obvious gaps
    analytic_q = graph.create_analytic_question_node("trump epstein investigation")
    investigation_q1 = graph.create_investigation_question_node("what did trump say?")
    # Notice: no investigation_q2 for "what did epstein say?" - gap!
    
    gaps = graph.get_information_gaps()
    
    assert len(gaps) > 0
    assert any("epstein" in gap.lower() for gap in gaps)

def test_thread_connectivity_analysis():
    """EVIDENCE: System must detect disconnected investigation threads"""  
    graph = InvestigationGraph()
    
    # Create disconnected threads
    thread1_q = graph.create_investigation_question_node("trump statements")
    thread1_search = graph.create_search_query_node("timeline.php", {"screenname": "realDonaldTrump"})
    graph.create_edge(thread1_q, thread1_search, "OPERATIONALIZES", {})
    
    thread2_q = graph.create_investigation_question_node("epstein background") 
    thread2_search = graph.create_search_query_node("search.php", {"query": "epstein biography"})
    graph.create_edge(thread2_q, thread2_search, "OPERATIONALIZES", {})
    
    # No edges between thread1 and thread2 = disconnected
    
    disconnected = graph.get_disconnected_threads()
    assert len(disconnected) >= 2
    assert any("trump" in str(thread) for thread in disconnected)
    assert any("epstein" in str(thread) for thread in disconnected)

def test_failed_pattern_detection():
    """EVIDENCE: System must identify repeated failed strategies"""
    graph = InvestigationGraph()
    
    # Simulate the actual failed pattern from logs: "find different 2024" repeated 40+ times
    for i in range(45):
        search = graph.create_search_query_node("search.php", {"query": "find different 2024"})
        search.properties["effectiveness_score"] = 1.2  # Low effectiveness like in logs
    
    failed_patterns = graph.get_failed_patterns()
    
    assert len(failed_patterns) > 0
    found_pattern = any("find different 2024" in pattern for pattern in failed_patterns)
    assert found_pattern, f"Failed to detect repeated pattern. Found patterns: {failed_patterns}"

def test_context_size_management():
    """EVIDENCE: Strategic context must fit in LLM context windows"""
    # Create large graph scenario
    graph = create_large_investigation_graph()
    
    context = graph.get_strategic_context_for_llm()
    
    # Context must be manageable size
    word_count = len(context.split())
    assert word_count < 15000, f"Context too large: {word_count} words"
    assert word_count > 100, f"Context too small: {word_count} words"
    
    # Must still contain essential elements
    assert "ORIGINAL GOAL:" in context
    assert "INFORMATION GAPS:" in context
    assert "DISCONNECTED THREADS:" in context

def test_baseline_log_pattern_detection():
    """EVIDENCE: System must detect actual patterns from baseline investigation logs"""
    graph = create_graph_from_baseline_logs()
    
    failed_patterns = graph.get_failed_patterns()
    
    # Should detect the "find different" pattern that was repeated 40+ times
    assert len(failed_patterns) > 0
    
    # Check for specific baseline failure pattern
    baseline_pattern_found = any(
        "find different" in pattern.lower() 
        for pattern in failed_patterns
    )
    assert baseline_pattern_found, f"Failed to detect baseline pattern. Patterns: {failed_patterns}"

def test_strategic_coherence_requirements():
    """EVIDENCE: Context must provide coherent strategic guidance"""
    graph = create_realistic_mixed_progress_graph()
    
    context = graph.get_strategic_context_for_llm()
    
    # Must provide clear strategic guidance elements
    required_elements = [
        "ORIGINAL GOAL:",
        "INVESTIGATION PROGRESS:",
        "CURRENT INFORMATION GAPS:",
        "DISCONNECTED THREADS:",
        "FAILED APPROACHES",
        "STRATEGIC COHERENCE DECISION POINT:"
    ]
    
    for element in required_elements:
        assert element in context, f"Missing strategic element: {element}"
    
    # Context must be actionable
    assert "what is the most strategically coherent next action?" in context.lower()

def create_graph_from_baseline_scenario() -> InvestigationGraph:
    """Create graph representing the baseline failure scenario"""
    graph = InvestigationGraph()
    
    # Original analytic question
    analytic_q = graph.create_analytic_question_node("find me different takes on the current trump epstein drama")
    
    # Add the repeated failed searches
    for i in range(40):
        search = graph.create_search_query_node("search.php", {"query": "find different 2024"})
        search.properties["effectiveness_score"] = 1.2
        search.properties["results_count"] = 59
        search.properties["execution_time"] = 5.8
    
    return graph

def create_graph_from_baseline_logs() -> InvestigationGraph:
    """Create graph from actual baseline log patterns"""
    graph = InvestigationGraph()
    
    # Main goal from logs
    analytic_q = graph.create_analytic_question_node("find me different takes on the current trump epstein drama")
    
    # Failed search patterns from actual logs
    failed_queries = [
        "find different 2024",
        "find different recent", 
        "find different current",
        "different takes trump epstein"
    ]
    
    for query in failed_queries:
        for i in range(10):  # Each pattern repeated multiple times
            search = graph.create_search_query_node("search.php", {"query": query})
            search.properties["effectiveness_score"] = 1.5  # Low effectiveness from logs
            search.properties["results_count"] = 45
    
    return graph

def create_large_investigation_graph() -> InvestigationGraph:
    """Create large graph for context size testing"""
    graph = InvestigationGraph()
    
    # Main analytic question
    analytic_q = graph.create_analytic_question_node("comprehensive trump epstein investigation")
    
    # Many investigation questions
    for i in range(20):
        q = graph.create_investigation_question_node(f"investigation aspect {i}: what about topic {i}?")
        
        # Each has searches
        for j in range(3):
            s = graph.create_search_query_node("search.php", {"query": f"query {i}_{j}"})
            graph.create_edge(q, s, "OPERATIONALIZES", {})
            
            # Each search has data points
            for k in range(5):
                d = graph.create_data_point_node(f"data from search {i}_{j}_{k}", {"source": "twitter"})
                graph.create_edge(s, d, "GENERATES", {})
    
    return graph

def create_realistic_mixed_progress_graph() -> InvestigationGraph:
    """Create graph with mixed progress for strategic coherence testing"""
    graph = InvestigationGraph()
    
    # Main goal
    analytic_q = graph.create_analytic_question_node("trump epstein drama investigation")
    
    # Some questions answered, some not
    q1 = graph.create_investigation_question_node("what did trump say about epstein?")
    s1 = graph.create_search_query_node("timeline.php", {"screenname": "realDonaldTrump"})
    graph.create_edge(q1, s1, "OPERATIONALIZES", {})
    d1 = graph.create_data_point_node("Trump tweet: I barely knew him", {"source": "twitter"})
    graph.create_edge(s1, d1, "GENERATES", {})
    i1 = graph.create_insight_node("Trump maintains distance from Epstein", "pattern")
    graph.create_edge(d1, i1, "SUPPORTS", {})
    
    # Unanswered question (gap)
    q2 = graph.create_investigation_question_node("what is the public reaction?")
    # No searches or data for q2 = gap
    
    # Failed searches
    for i in range(5):
        failed_search = graph.create_search_query_node("search.php", {"query": "find different stuff"})
        failed_search.properties["effectiveness_score"] = 0.8
    
    return graph