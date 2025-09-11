# test_litellm_integration.py
"""
Test suite for LiteLLM Integration with Structured Output
EVIDENCE: LiteLLM must return structured JSON from gemini-2.5-flash
"""

import pytest
import os
from pydantic import BaseModel
from typing import List, Dict, Any

# Import will fail until implemented
try:
    from llm_client import get_litellm_client, LiteLLMClient
    from investigation_graph import InvestigationGraph
except ImportError:
    pytest.skip("LLM client not implemented yet", allow_module_level=True)

class StrategicDecision(BaseModel):
    decision_type: str
    reasoning: str  
    searches: List[Dict[str, Any]]
    expected_outcomes: List[str]

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_litellm_structured_output():
    """EVIDENCE: LiteLLM must return structured JSON from gemini-2.5-flash"""
    
    llm_client = get_litellm_client()  # Load from .env
    
    response = llm_client.completion(
        model="gemini/gemini-2.5-flash",
        messages=[{"role": "user", "content": "Generate strategic decision for Trump Epstein investigation"}],
        response_format=StrategicDecision
    )
    
    decision = response.choices[0].message.parsed
    assert isinstance(decision, StrategicDecision)
    assert decision.decision_type in ["gap_filling", "thread_connecting", "deep_dive", "pivot"]
    assert len(decision.searches) > 0

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set")
def test_llm_graph_context_processing():
    """EVIDENCE: LLM must handle large graph context without errors"""
    graph = create_large_test_graph(50)  # Realistic size test
    context = graph.get_strategic_context_for_llm()
    
    llm_client = get_litellm_client()
    response = llm_client.completion(
        model="gemini/gemini-2.5-flash", 
        messages=[{"role": "user", "content": f"Analyze this investigation context: {context}"}]
    )
    
    assert response.choices[0].message.content is not None
    assert len(response.choices[0].message.content) > 100

def test_llm_client_initialization():
    """EVIDENCE: LLM client must initialize correctly"""
    # Test with mock API key for basic initialization
    client = LiteLLMClient("test-api-key")
    assert client is not None
    assert hasattr(client, 'completion')

def create_large_test_graph(node_count: int) -> InvestigationGraph:
    """Create large test graph for performance testing"""
    graph = InvestigationGraph()
    
    # Main analytic question
    analytic_q = graph.create_analytic_question_node("large scale investigation test")
    
    # Create many investigation questions
    investigation_questions = []
    for i in range(node_count // 5):
        q = graph.create_investigation_question_node(f"investigation question {i}")
        investigation_questions.append(q)
        
    # Create many search queries
    for i in range(node_count // 3):
        s = graph.create_search_query_node("search.php", {"query": f"search query {i}"})
        
    # Create many data points
    for i in range(node_count // 2):
        d = graph.create_data_point_node(f"data point {i}", {"source": "test", "id": i})
        
    return graph