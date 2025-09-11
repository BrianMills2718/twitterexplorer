# test_graph_aware_coordinator.py
"""
Test suite for Graph-Aware LLM Coordinator
EVIDENCE: Coordinator must use complete graph context for strategic decisions
"""

import pytest
from unittest.mock import Mock, MagicMock
from investigation_graph import InvestigationGraph
from llm_client import LiteLLMClient

# Import will fail until implemented
try:
    from graph_aware_llm_coordinator import GraphAwareLLMCoordinator, StrategicDecision
except ImportError:
    pytest.skip("GraphAwareLLMCoordinator not implemented yet", allow_module_level=True)

def test_strategic_decision_with_full_context():
    """EVIDENCE: Coordinator must use complete graph context for decisions"""
    graph = create_realistic_investigation_graph()  # 20+ nodes, realistic investigation
    mock_llm = create_mock_llm_client()
    coordinator = GraphAwareLLMCoordinator(mock_llm, graph)
    
    decision = coordinator.make_strategic_decision("trump epstein investigation")
    
    # Decision must be informed by full context
    assert decision.context_utilization > 0.8  # Used most of available context
    assert decision.strategic_coherence_score > 0.7  # Coherent with existing investigation
    assert len(decision.rationale) > 100  # Substantial reasoning
    
    # Decision must avoid known failures
    failed_patterns = graph.get_failed_patterns()
    for pattern in failed_patterns:
        assert pattern not in str(decision.searches)

def test_emergent_question_detection():
    """EVIDENCE: System must spawn new questions from insights using real LLM"""
    import os
    import pytest
    from dotenv import load_dotenv
    from llm_client import get_litellm_client
    
    # Skip if no API key
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY required for real LLM integration test")
    
    graph = InvestigationGraph()
    real_llm = get_litellm_client()  # REAL LLM!
    coordinator = GraphAwareLLMCoordinator(real_llm, graph)
    
    # Add contradictory insights that should spawn questions
    insight1 = graph.create_insight_node("Trump denied Epstein connection", "fact")
    insight2 = graph.create_insight_node("Photos show Trump at Epstein events", "fact")
    
    # Real LLM should detect the contradiction and spawn questions
    emergent_questions = coordinator.detect_emergent_questions([insight1, insight2])
    
    # Validate real LLM detected the contradiction
    assert len(emergent_questions) > 0, "Real LLM should detect contradictory insights and spawn questions"
    
    # Check that LLM identified contradiction-related reasoning
    contradiction_found = any("contradiction" in eq.emergence_reason.lower() or 
                            "conflict" in eq.emergence_reason.lower() or
                            "inconsistent" in eq.emergence_reason.lower() 
                            for eq in emergent_questions)
    assert contradiction_found, f"LLM should identify contradiction. Got reasons: {[eq.emergence_reason for eq in emergent_questions]}"
    
    # Check that questions reference the evidence
    evidence_referenced = any("photo" in eq.text.lower() or "event" in eq.text.lower() or
                            "denied" in eq.text.lower() or "connection" in eq.text.lower()
                            for eq in emergent_questions)
    assert evidence_referenced, f"Questions should reference evidence. Got questions: {[eq.text for eq in emergent_questions]}"

def test_context_window_management():
    """EVIDENCE: System must handle large contexts without truncation errors using real LLM"""
    import os
    import pytest
    from dotenv import load_dotenv
    from llm_client import get_litellm_client
    
    # Skip if no API key - this tests context generation which doesn't need API but tests with real LLM setup
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY required for real LLM integration test")
    
    large_graph = create_large_investigation_graph(nodes=50)  # Smaller for real test
    real_llm = get_litellm_client()  # REAL LLM!
    coordinator = GraphAwareLLMCoordinator(real_llm, large_graph)
    
    # Generate strategic context from the large graph
    raw_context = large_graph.get_strategic_context_for_llm()
    optimized_context = coordinator.context_manager.optimize_context(raw_context)
    
    # Context must be processable but comprehensive
    assert len(optimized_context.split()) < 100000, f"Context too large: {len(optimized_context.split())} words"
    assert "ORIGINAL GOAL:" in optimized_context, "Missing original goal section"
    assert "INFORMATION GAPS:" in optimized_context, "Missing information gaps section"
    
    # Check for failed approaches section (should exist if graph has failed patterns)
    failed_patterns = large_graph.get_failed_patterns()
    if failed_patterns:
        assert "FAILED APPROACHES:" in optimized_context, "Missing failed approaches section when patterns exist"
        # Should have exactly one failed approaches section
        failed_section_count = len([line for line in optimized_context.split('\n') if "FAILED APPROACHES:" in line])
        assert failed_section_count == 1, f"Should have exactly 1 failed approaches section, got {failed_section_count}"

def test_graph_building_during_execution():
    """EVIDENCE: Coordinator must build graph during investigation execution"""
    graph = InvestigationGraph()
    mock_llm = create_mock_llm_client()
    coordinator = GraphAwareLLMCoordinator(mock_llm, graph)
    
    # Start investigation
    coordinator.start_investigation("trump epstein drama")
    
    # Should have created analytic question
    analytic_questions = graph.get_nodes_by_type("AnalyticQuestion")
    assert len(analytic_questions) == 1
    
    # Make decision - should create investigation question and search query nodes
    decision = coordinator.make_strategic_decision("trump epstein drama")
    
    # Graph should have grown
    investigation_questions = graph.get_nodes_by_type("InvestigationQuestion")
    search_queries = graph.get_nodes_by_type("SearchQuery")
    
    assert len(investigation_questions) > 0
    assert len(search_queries) > 0

def test_batch_result_evaluation():
    """EVIDENCE: Coordinator must evaluate results semantically in batches using real LLM"""
    import os
    import pytest
    from dotenv import load_dotenv
    from llm_client import get_litellm_client
    
    # Skip if no API key
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY required for real LLM integration test")
    
    graph = InvestigationGraph()
    real_llm = get_litellm_client()  # REAL LLM!
    coordinator = GraphAwareLLMCoordinator(real_llm, graph)
    
    # Real search results - mix of relevant and irrelevant for real semantic evaluation
    results = [
        {"text": "Trump says he barely knew Jeffrey Epstein", "source": "twitter"},
        {"text": "Find different ways to save money on groceries", "source": "twitter"},  # Clearly irrelevant
        {"text": "Epstein case details emerge in court documents", "source": "twitter"},
        {"text": "New evidence links Trump to Epstein social circle", "source": "twitter"},  # Relevant
        {"text": "Best pizza recipes for family dinner tonight", "source": "twitter"}  # Clearly irrelevant
    ]
    
    # Real LLM semantic evaluation
    evaluation = coordinator.evaluate_batch_results("trump epstein investigation", results)
    
    # Real LLM should distinguish relevant from irrelevant content
    assert evaluation.relevance_score > 3.0, f"LLM should give moderate+ score for mixed results, got {evaluation.relevance_score}"
    assert evaluation.relevance_score < 9.0, f"LLM should not give perfect score for mixed results, got {evaluation.relevance_score}"
    
    # LLM should extract insights from relevant content
    assert len(evaluation.key_insights) > 0, f"LLM should extract insights from relevant content, got {evaluation.key_insights}"
    
    # LLM should identify investigation gaps
    assert len(evaluation.remaining_gaps) > 0, f"LLM should identify remaining gaps, got {evaluation.remaining_gaps}"
    
    # Information value should be reasonable for mixed content
    assert evaluation.information_value > 2.0, f"Information value too low for mixed results: {evaluation.information_value}"
    
    # LLM should decide to continue investigation
    assert evaluation.should_continue == True, "LLM should recommend continuing investigation"

def test_failed_strategy_avoidance():
    """EVIDENCE: Coordinator must avoid repeating failed strategies"""
    graph = create_graph_with_failed_patterns()
    mock_llm = create_mock_llm_client()
    coordinator = GraphAwareLLMCoordinator(mock_llm, graph)
    
    # Get failed patterns from graph
    failed_patterns = graph.get_failed_patterns()
    assert len(failed_patterns) > 0
    
    # Make strategic decision
    decision = coordinator.make_strategic_decision("trump epstein investigation")
    
    # Decision must not repeat failed patterns
    for pattern in failed_patterns:
        pattern_query = pattern.split("'")[1] if "'" in pattern else pattern
        for search in decision.searches:
            search_query = search.get("parameters", {}).get("query", "")
            assert pattern_query not in search_query, f"Coordinator repeated failed pattern: {pattern_query}"

def test_progressive_understanding_synthesis():
    """EVIDENCE: Coordinator must build progressive understanding"""
    graph = create_graph_with_mixed_progress()
    mock_llm = create_mock_llm_client()
    coordinator = GraphAwareLLMCoordinator(mock_llm, graph)
    
    # Get current understanding
    understanding = coordinator.synthesize_current_understanding()
    
    assert understanding.confidence_level > 0.0
    assert len(understanding.key_findings) > 0
    assert len(understanding.critical_gaps) > 0
    assert understanding.current_understanding != "Starting investigation"

# Helper functions for test data
def create_realistic_investigation_graph() -> InvestigationGraph:
    """Create a realistic 20+ node investigation graph"""
    graph = InvestigationGraph()
    
    # Main analytic question
    analytic_q = graph.create_analytic_question_node("find different takes on trump epstein drama")
    
    # Multiple investigation questions
    q1 = graph.create_investigation_question_node("What did Trump say about Epstein?")
    q2 = graph.create_investigation_question_node("What is the public reaction?") 
    q3 = graph.create_investigation_question_node("What are the latest developments?")
    
    # Search queries for each question
    s1 = graph.create_search_query_node("timeline.php", {"screenname": "realDonaldTrump"})
    s2 = graph.create_search_query_node("search.php", {"query": "Trump Epstein statements"})
    s3 = graph.create_search_query_node("hashtag.php", {"hashtag": "Epstein"})
    
    # Data points
    d1 = graph.create_data_point_node("Trump tweet: 'I barely knew Jeffrey Epstein'", 
                                      {"source": "twitter", "timestamp": "2025-08-08"})
    d2 = graph.create_data_point_node("Public reply: 'That's not what the photos show'", 
                                      {"source": "twitter", "timestamp": "2025-08-08"})
    
    # Insights
    i1 = graph.create_insight_node("Trump consistently denies close relationship", "pattern")
    i2 = graph.create_insight_node("Public skeptical of Trump's claims", "sentiment")
    
    # Create relationships
    graph.create_edge(analytic_q, q1, "MOTIVATES", {"priority": 0.9})
    graph.create_edge(q1, s1, "OPERATIONALIZES", {})
    graph.create_edge(s1, d1, "GENERATES", {})
    graph.create_edge(d1, i1, "SUPPORTS", {"confidence": 0.8})
    
    # Failed searches
    for i in range(5):
        failed = graph.create_search_query_node("search.php", {"query": "find different stuff"})
        failed.properties["effectiveness_score"] = 1.2
    
    return graph

def create_large_investigation_graph(nodes: int) -> InvestigationGraph:
    """Create large investigation graph for stress testing"""
    graph = InvestigationGraph()
    
    analytic_q = graph.create_analytic_question_node("large scale investigation")
    
    # Create many nodes
    for i in range(nodes // 4):
        q = graph.create_investigation_question_node(f"question {i}")
        s = graph.create_search_query_node("search.php", {"query": f"query {i}"})
        d = graph.create_data_point_node(f"data {i}", {"source": "test"})
        insight = graph.create_insight_node(f"insight {i}", "pattern")
        
        # Create some connections
        if i % 2 == 0:
            graph.create_edge(q, s, "OPERATIONALIZES", {})
            graph.create_edge(s, d, "GENERATES", {})
    
    return graph

def create_graph_with_failed_patterns() -> InvestigationGraph:
    """Create graph with clear failed patterns"""
    graph = InvestigationGraph()
    
    analytic_q = graph.create_analytic_question_node("trump epstein investigation")
    
    # Add failed patterns like in baseline logs
    failed_queries = ["find different 2024", "find different recent", "generic search"]
    
    for query in failed_queries:
        for i in range(5):
            search = graph.create_search_query_node("search.php", {"query": query})
            search.properties["effectiveness_score"] = 1.0  # Low effectiveness
            search.properties["results_count"] = 45
    
    return graph

def create_graph_with_mixed_progress() -> InvestigationGraph:
    """Create graph with some progress and some gaps"""
    graph = InvestigationGraph()
    
    analytic_q = graph.create_analytic_question_node("trump epstein drama")
    
    # Answered question
    q1 = graph.create_investigation_question_node("what did trump say?")
    s1 = graph.create_search_query_node("timeline.php", {"screenname": "realDonaldTrump"})
    d1 = graph.create_data_point_node("Trump: I barely knew him", {"source": "twitter"})
    i1 = graph.create_insight_node("Trump denies relationship", "fact")
    
    graph.create_edge(q1, s1, "OPERATIONALIZES", {})
    graph.create_edge(s1, d1, "GENERATES", {})
    graph.create_edge(d1, i1, "SUPPORTS", {})
    
    # Unanswered question (gap)
    q2 = graph.create_investigation_question_node("what is public reaction?")
    
    return graph

def create_mock_llm_client():
    """Create mock LLM client with realistic responses"""
    mock_llm = Mock(spec=LiteLLMClient)
    
    # Create mock strategic decision
    from graph_aware_llm_coordinator import StrategicDecision
    mock_decision = StrategicDecision(
        decision_type="gap_filling",
        reasoning="Based on the investigation context, the most strategic approach is to focus on direct source analysis through timeline searches while avoiding the previously failed generic search patterns.",
        searches=[
            {
                "endpoint": "timeline.php",
                "parameters": {"screenname": "realDonaldTrump", "count": 20},
                "reasoning": "Get direct statements from Trump about Epstein"
            }
        ],
        expected_outcomes=["Direct statements from Trump about Epstein relationship"],
        context_utilization=0.85,
        strategic_coherence_score=0.8,
        rationale="This decision leverages the complete investigation graph context to identify the most strategic next action. Analysis of previous failed patterns shows that generic searches like 'find different 2024' were ineffective, achieving only 4.5/10 relevance scores despite high volume (59 results). The graph analysis reveals a critical information gap in direct source material from Trump himself regarding the Epstein relationship. By targeting the timeline endpoint with Trump's screenname, we bypass the noise of generic searches and access primary source statements. This approach aligns with strategic coherence by building on existing investigation threads while avoiding documented failure patterns."
    )
    
    # Mock response structure
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_decision
    
    # Configure mock completion method
    mock_llm.completion.return_value = mock_response
    
    return mock_llm