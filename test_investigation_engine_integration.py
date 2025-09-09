# test_investigation_engine_integration.py
"""
Test suite for Investigation Engine Integration with Graph Architecture
EVIDENCE: Investigation engine must build graph during execution and demonstrate strategic coherence
"""

import pytest
from unittest.mock import Mock, patch
from investigation_engine import InvestigationEngine, InvestigationConfig
from investigation_graph import InvestigationGraph
from graph_aware_llm_coordinator import GraphAwareLLMCoordinator

def test_investigation_engine_graph_integration():
    """EVIDENCE: Investigation engine must build graph during execution"""
    
    # Create engine with mocked initialization
    engine = create_mock_investigation_engine()
    
    # Verify it's using graph mode
    assert engine.graph_mode == True
    assert isinstance(engine.llm_coordinator, GraphAwareLLMCoordinator)
    
    # Start the investigation to initialize the graph
    engine.llm_coordinator.start_investigation("find different takes on trump epstein drama")
    
    # Mock streamlit components to avoid UI calls  
    with patch('streamlit.container'), \
         patch('streamlit.empty'), \
         patch('streamlit.markdown'), \
         patch('streamlit.info'), \
         patch('investigation_engine.api_client') as mock_api:
        
        # Mock API response
        mock_api.execute_api_step.return_value = {
            'data': {
                'timeline': [
                    {'text': 'Trump tweet: I barely knew Jeffrey Epstein'},
                    {'text': 'Another relevant tweet about the situation'}
                ]
            }
        }
        
        # Conduct investigation that should build graph
        result = engine.conduct_investigation(
            "find different takes on trump epstein drama",
            config=InvestigationConfig(max_searches=3)
        )
        
        # Investigation must have built comprehensive graph
        graph = engine.llm_coordinator.graph
        assert len(graph.nodes) >= 3  # At least some nodes created
        
        # Graph must contain analytic question (created at start)
        analytic_nodes = graph.get_nodes_by_type("AnalyticQuestion")
        assert len(analytic_nodes) >= 1

def test_strategic_coherence_validation():
    """EVIDENCE: Investigation must demonstrate strategic coherence vs baseline"""
    engine = InvestigationEngine("test_api_key")
    
    # Mock components
    mock_graph = InvestigationGraph()
    mock_llm_client = create_mock_llm_client_with_coherent_responses()
    graph_coordinator = GraphAwareLLMCoordinator(mock_llm_client, mock_graph)
    engine.llm_coordinator = graph_coordinator
    
    with patch('streamlit.container'), \
         patch('streamlit.empty'), \
         patch('streamlit.markdown'), \
         patch('streamlit.info'), \
         patch('investigation_engine.api_client') as mock_api:
        
        # Mock high-relevance API responses
        mock_api.execute_api_step.return_value = {
            'data': {
                'timeline': [
                    {'text': 'Trump statement: I barely knew Jeffrey Epstein'},
                    {'text': 'Court documents reveal Epstein connections'},
                    {'text': 'Public reaction to Trump Epstein news'}
                ]
            }
        }
        
        # New graph-based investigation
        result = engine.conduct_investigation(
            "find me different takes on the current trump epstein drama",  # Same query that failed in baseline
            config=InvestigationConfig(max_searches=10)
        )
        
        # Evidence of strategic improvement
        graph = engine.llm_coordinator.graph
        
        # Measure coherence indicators
        thread_connectivity = measure_thread_connectivity(graph)
        gap_coverage_rate = measure_gap_coverage_rate(graph)
        redundancy_rate = measure_investigation_redundancy(graph)
        
        # Must demonstrate strategic improvement
        assert thread_connectivity > 0.6  # Strong thread connectivity
        assert gap_coverage_rate > 0.5  # Good gap coverage
        assert redundancy_rate < 0.4  # Low redundancy
        
        # Must avoid baseline failure patterns
        failed_patterns = graph.get_failed_patterns()
        baseline_pattern_found = any("find different" in pattern.lower() for pattern in failed_patterns)
        
        # Should NOT repeat the baseline failure pattern
        assert not baseline_pattern_found or len(failed_patterns) == 0

def test_graph_persistence_across_rounds():
    """EVIDENCE: Graph must maintain context across investigation rounds"""
    engine = InvestigationEngine("test_api_key")
    
    # Setup with graph coordinator
    mock_graph = InvestigationGraph()
    mock_llm_client = create_mock_progressive_llm_client()
    graph_coordinator = GraphAwareLLMCoordinator(mock_llm_client, mock_graph)
    engine.llm_coordinator = graph_coordinator
    
    with patch('streamlit.container'), \
         patch('streamlit.empty'), \
         patch('streamlit.markdown'), \
         patch('streamlit.info'), \
         patch('investigation_engine.api_client') as mock_api:
        
        # Mock different responses for different rounds
        responses = [
            {'data': {'timeline': [{'text': 'Round 1: Trump denies connection'}]}},
            {'data': {'timeline': [{'text': 'Round 2: Public questions denial'}]}}, 
            {'data': {'timeline': [{'text': 'Round 3: New evidence emerges'}]}}
        ]
        
        mock_api.execute_api_step.side_effect = responses
        
        # Run investigation
        result = engine.conduct_investigation(
            "trump epstein investigation",
            config=InvestigationConfig(max_searches=6)  # 2 searches per round
        )
        
        graph = engine.llm_coordinator.graph
        
        # Graph must accumulate context across rounds
        data_points = graph.get_nodes_by_type("DataPoint")
        assert len(data_points) >= 3  # Should have data from all rounds
        
        # Later rounds should reference earlier findings
        insights = graph.get_nodes_by_type("Insight")
        assert len(insights) > 0  # Should generate insights from accumulated data

def test_emergent_question_handling():
    """EVIDENCE: System must handle emergent questions during investigation"""
    engine = InvestigationEngine("test_api_key")
    
    # Setup
    mock_graph = InvestigationGraph()
    mock_llm_client = create_mock_emergent_question_client()
    graph_coordinator = GraphAwareLLMCoordinator(mock_llm_client, mock_graph)
    engine.llm_coordinator = graph_coordinator
    
    with patch('streamlit.container'), \
         patch('streamlit.empty'), \
         patch('streamlit.markdown'), \
         patch('streamlit.info'), \
         patch('investigation_engine.api_client') as mock_api:
        
        # Mock contradictory results that should spawn emergent questions
        mock_api.execute_api_step.return_value = {
            'data': {
                'timeline': [
                    {'text': 'Trump: I never met Epstein'},
                    {'text': 'Photo evidence shows Trump at Epstein party'},
                    {'text': 'Flight logs show Trump on Epstein plane'}
                ]
            }
        }
        
        result = engine.conduct_investigation(
            "trump epstein relationship",
            config=InvestigationConfig(max_searches=4)
        )
        
        graph = engine.llm_coordinator.graph
        
        # Should generate emergent questions from contradictions
        emergent_questions = graph.get_nodes_by_type("EmergentQuestion")
        assert len(emergent_questions) > 0
        
        # Questions should address contradictions
        question_texts = [q.properties.get("text", "") for q in emergent_questions]
        contradiction_addressed = any("contradiction" in text.lower() or "photo" in text.lower() 
                                    for text in question_texts)
        assert contradiction_addressed

# Helper functions for test data and measurements
def create_mock_investigation_engine():
    """Create investigation engine with mocked components for testing"""
    # Create mock components
    mock_graph = InvestigationGraph()
    mock_llm_client = create_mock_llm_client()
    graph_coordinator = GraphAwareLLMCoordinator(mock_llm_client, mock_graph)
    
    # Create engine instance without initialization
    engine = object.__new__(InvestigationEngine)
    engine.rapidapi_key = "test_api_key"
    engine.llm_coordinator = graph_coordinator
    engine.graph_mode = True
    
    return engine

def create_mock_llm_client():
    """Create basic mock LLM client"""
    from graph_aware_llm_coordinator import StrategicDecision
    from llm_client import InvestigationEvaluation
    
    mock_llm = Mock()
    
    # Mock strategic decision
    mock_decision = StrategicDecision(
        decision_type="gap_filling",
        reasoning="Strategic investigation approach",
        searches=[{
            "endpoint": "timeline.php",
            "parameters": {"screenname": "realDonaldTrump", "count": 20},
            "reasoning": "Get direct statements"
        }],
        expected_outcomes=["Direct user statements"],
        context_utilization=0.8,
        strategic_coherence_score=0.7
    )
    
    # Mock evaluation response
    mock_evaluation = InvestigationEvaluation(
        relevance_score=7.5,
        information_value=6.0,
        key_insights=["Trump maintains distance from Epstein"],
        remaining_gaps=["Public reaction analysis needed"],
        should_continue=True
    )
    
    # Setup response cycling
    responses = [mock_decision, mock_evaluation]
    call_count = [0]
    
    def get_response(*args, **kwargs):
        response_index = call_count[0] % len(responses)
        call_count[0] += 1
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.parsed = responses[response_index]
        return mock_response
    
    mock_llm.completion.side_effect = get_response
    
    return mock_llm

def create_mock_llm_client_with_coherent_responses():
    """Create mock LLM client with strategically coherent responses"""
    from graph_aware_llm_coordinator import StrategicDecision
    
    mock_llm = Mock()
    
    # Strategic responses that avoid baseline failures
    strategic_decisions = [
        StrategicDecision(
            decision_type="direct_source",
            reasoning="Focus on direct source access - timeline search for Trump's actual statements",
            searches=[{
                "endpoint": "timeline.php",
                "parameters": {"screenname": "realDonaldTrump", "count": 20},
                "reasoning": "Get Trump's direct statements about Epstein"
            }],
            expected_outcomes=["Direct statements from Trump"],
            context_utilization=0.9,
            strategic_coherence_score=0.8
        ),
        StrategicDecision(
            decision_type="public_reaction",
            reasoning="Analyze public reaction and discourse around the issue",
            searches=[{
                "endpoint": "hashtag.php", 
                "parameters": {"hashtag": "TrumpEpstein", "result_type": "latest"},
                "reasoning": "Get public reactions and discussions"
            }],
            expected_outcomes=["Public sentiment and reactions"],
            context_utilization=0.85,
            strategic_coherence_score=0.75
        )
    ]
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    
    # Cycle through strategic decisions
    def get_decision(*args, **kwargs):
        decision_index = getattr(get_decision, 'call_count', 0)
        get_decision.call_count = (decision_index + 1) % len(strategic_decisions)
        mock_response.choices[0].message.parsed = strategic_decisions[decision_index]
        return mock_response
    
    mock_llm.completion.side_effect = get_decision
    
    return mock_llm

def create_mock_progressive_llm_client():
    """Create mock LLM client that builds progressive understanding"""
    mock_llm = Mock()
    
    # Progressive responses that build on previous findings
    decisions = [
        # Round 1: Initial exploration
        {"reasoning": "Initial exploration of Trump's direct statements", "endpoint": "timeline.php"},
        # Round 2: Build on findings
        {"reasoning": "Building on initial findings, explore public reactions", "endpoint": "search.php"},
        # Round 3: Synthesize understanding  
        {"reasoning": "Synthesizing findings, explore contradictory evidence", "endpoint": "hashtag.php"}
    ]
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    
    def get_progressive_decision(*args, **kwargs):
        from graph_aware_llm_coordinator import StrategicDecision
        
        call_count = getattr(get_progressive_decision, 'call_count', 0)
        get_progressive_decision.call_count = call_count + 1
        
        decision_data = decisions[call_count % len(decisions)]
        
        mock_decision = StrategicDecision(
            decision_type="progressive",
            reasoning=decision_data["reasoning"],
            searches=[{
                "endpoint": decision_data["endpoint"],
                "parameters": {"query": f"progressive search {call_count}"},
                "reasoning": decision_data["reasoning"]
            }],
            expected_outcomes=[f"Progressive understanding round {call_count}"],
            context_utilization=0.8,
            strategic_coherence_score=0.7
        )
        
        mock_response.choices[0].message.parsed = mock_decision
        return mock_response
    
    mock_llm.completion.side_effect = get_progressive_decision
    return mock_llm

def create_mock_emergent_question_client():
    """Create mock LLM client that handles emergent questions"""
    mock_llm = Mock()
    
    # Mock response that includes emergent question detection
    from graph_aware_llm_coordinator import StrategicDecision
    
    mock_decision = StrategicDecision(
        decision_type="contradiction_resolution",
        reasoning="Detected contradiction in evidence - need to investigate further",
        searches=[{
            "endpoint": "search.php",
            "parameters": {"query": "Trump Epstein photo evidence verification"},
            "reasoning": "Investigate contradictory photo evidence"
        }],
        expected_outcomes=["Resolution of contradictory evidence"],
        context_utilization=0.9,
        strategic_coherence_score=0.8
    )
    
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.parsed = mock_decision
    mock_llm.completion.return_value = mock_response
    
    return mock_llm

def measure_thread_connectivity(graph: InvestigationGraph) -> float:
    """Measure how well investigation threads are connected"""
    disconnected_threads = graph.get_disconnected_threads()
    total_nodes = len(graph.nodes)
    
    if total_nodes == 0:
        return 0.0
    
    # Higher connectivity = fewer disconnected threads
    if len(disconnected_threads) <= 1:
        return 1.0  # All connected
    
    # Calculate based on largest connected component
    largest_component_size = max(len(thread) for thread in disconnected_threads) if disconnected_threads else 0
    return largest_component_size / total_nodes

def measure_gap_coverage_rate(graph: InvestigationGraph) -> float:
    """Measure how well information gaps are being addressed"""
    gaps = graph.get_information_gaps()
    investigation_questions = graph.get_nodes_by_type("InvestigationQuestion")
    
    if not gaps:
        return 1.0  # No gaps = perfect coverage
    
    # Check how many gaps have corresponding investigation questions
    gaps_addressed = 0
    for gap in gaps:
        gap_keywords = gap.lower().split()[:3]  # First 3 words
        for question in investigation_questions:
            question_text = question.properties.get("text", "").lower()
            if any(keyword in question_text for keyword in gap_keywords):
                gaps_addressed += 1
                break
    
    return gaps_addressed / len(gaps)

def measure_investigation_redundancy(graph: InvestigationGraph) -> float:
    """Measure redundancy in investigation approach"""
    search_nodes = graph.get_nodes_by_type("SearchQuery")
    
    if len(search_nodes) <= 1:
        return 0.0
    
    # Count duplicate queries
    query_counts = {}
    for search in search_nodes:
        query = search.properties.get("parameters", {}).get("query", "")
        query_counts[query] = query_counts.get(query, 0) + 1
    
    # Calculate redundancy rate
    duplicate_searches = sum(max(0, count - 1) for count in query_counts.values())
    return duplicate_searches / len(search_nodes)