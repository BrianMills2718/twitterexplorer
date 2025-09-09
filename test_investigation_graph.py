# test_investigation_graph.py
"""
Test suite for Investigation Graph Architecture
EVIDENCE: Graph must create and store all node types from ontology with relationships
"""

import pytest
import json
from datetime import datetime
from typing import Dict, List

from investigation_graph import (
    Node, Edge, InvestigationGraph,
    InvestigationContext
)

def test_investigation_graph_node_creation():
    """EVIDENCE: Graph must create and store all node types from ontology"""
    graph = InvestigationGraph()
    
    # Create nodes from ontology design
    analytic_q = graph.create_analytic_question_node("find me different takes on trump epstein drama")
    investigation_q = graph.create_investigation_question_node("What did Trump say about Epstein?")
    search_q = graph.create_search_query_node("timeline.php", {"screenname": "realDonaldTrump"})
    
    assert len(graph.nodes) == 3
    assert analytic_q.node_type == "AnalyticQuestion"
    assert investigation_q.parent_analytic_question == analytic_q.id
    assert search_q.endpoint == "timeline.php"
    assert search_q.parameters["screenname"] == "realDonaldTrump"

def test_investigation_graph_edge_creation():
    """EVIDENCE: Graph must create relationships between nodes"""
    graph = InvestigationGraph()
    
    analytic_q = graph.create_analytic_question_node("trump epstein investigation")
    investigation_q = graph.create_investigation_question_node("what statements did trump make?")
    
    edge = graph.create_edge(analytic_q, investigation_q, "MOTIVATES", {"relevance_strength": 0.9})
    
    assert edge.edge_type == "MOTIVATES"
    assert edge.properties["relevance_strength"] == 0.9
    assert len(graph.edges) == 1

def test_strategic_context_generation():
    """EVIDENCE: Graph must generate LLM-ready strategic context"""
    graph = populate_test_investigation_graph()  # Helper with realistic data
    
    context = graph.get_strategic_context_for_llm()
    
    assert "ORIGINAL GOAL:" in context
    assert "INFORMATION GAPS:" in context  
    assert "DISCONNECTED THREADS:" in context
    assert len(context) < 50000  # Must fit in context window

def test_information_gap_identification():
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

def test_graph_serialization():
    """EVIDENCE: Graph must serialize to/from JSON for persistence"""
    graph = populate_test_investigation_graph()
    
    # Serialize to JSON
    json_str = graph.to_json()
    parsed = json.loads(json_str)
    
    assert "nodes" in parsed
    assert "edges" in parsed
    assert "analytic_question" in parsed
    
    # Recreate from JSON
    new_graph = InvestigationGraph()
    new_graph.from_json(json_str)
    
    assert len(new_graph.nodes) == len(graph.nodes)
    assert len(new_graph.edges) == len(graph.edges)

def test_node_type_creation():
    """EVIDENCE: Graph must support all node types from ontology"""
    graph = InvestigationGraph()
    
    # Test all node types
    analytic = graph.create_analytic_question_node("main question")
    investigation = graph.create_investigation_question_node("sub question")
    search = graph.create_search_query_node("search.php", {"query": "test"})
    data = graph.create_data_point_node("sample tweet text", {"source": "twitter", "timestamp": "2025-08-09"})
    insight = graph.create_insight_node("key finding from analysis", "pattern")
    emergent = graph.create_emergent_question_node("new question emerged", "contradiction found")
    
    assert analytic.node_type == "AnalyticQuestion"
    assert investigation.node_type == "InvestigationQuestion"
    assert search.node_type == "SearchQuery"
    assert data.node_type == "DataPoint"
    assert insight.node_type == "Insight"
    assert emergent.node_type == "EmergentQuestion"

def test_failed_pattern_detection():
    """EVIDENCE: Graph must track and identify failed search patterns"""
    graph = InvestigationGraph()
    
    # Add failed searches
    search1 = graph.create_search_query_node("search.php", {"query": "find different 2024"})
    search2 = graph.create_search_query_node("search.php", {"query": "find different 2024"})
    search3 = graph.create_search_query_node("search.php", {"query": "find different 2024"})
    
    # Mark as failed (low effectiveness)
    search1.properties["effectiveness_score"] = 1.0
    search2.properties["effectiveness_score"] = 1.2
    search3.properties["effectiveness_score"] = 0.8
    
    failed_patterns = graph.get_failed_patterns()
    
    assert len(failed_patterns) > 0
    assert any("find different 2024" in pattern for pattern in failed_patterns)

# Helper function for test data
def populate_test_investigation_graph() -> InvestigationGraph:
    """Create a realistic test investigation graph"""
    graph = InvestigationGraph()
    
    # Main analytic question
    analytic_q = graph.create_analytic_question_node("find different takes on trump epstein drama")
    
    # Investigation questions
    q1 = graph.create_investigation_question_node("What did Trump say about Epstein?")
    q2 = graph.create_investigation_question_node("What is the public reaction?")
    
    # Search queries
    s1 = graph.create_search_query_node("timeline.php", {"screenname": "realDonaldTrump"})
    s2 = graph.create_search_query_node("search.php", {"query": "Trump Epstein statements"})
    
    # Data points
    d1 = graph.create_data_point_node("Trump tweet: 'I barely knew Jeffrey Epstein'", 
                                      {"source": "twitter", "timestamp": "2025-08-08"})
    
    # Insights
    i1 = graph.create_insight_node("Trump consistently denies close relationship", "pattern")
    
    # Create relationships
    graph.create_edge(analytic_q, q1, "MOTIVATES", {"priority": 0.9})
    graph.create_edge(q1, s1, "OPERATIONALIZES", {})
    graph.create_edge(s1, d1, "GENERATES", {})
    graph.create_edge(d1, i1, "SUPPORTS", {"confidence": 0.8})
    
    return graph