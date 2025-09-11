#!/usr/bin/env python3
"""
Simple focused test to debug insight creation issue
Phase 1: Issue #2 - Untitled Insight Generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from realtime_insight_synthesizer import RealTimeInsightSynthesizer, InsightSynthesis
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph
from llm_client import get_litellm_client


def test_direct_insight_creation():
    """Test insight creation directly without complex pipeline"""
    
    print("Testing direct insight creation...")
    
    # Initialize components
    context = InvestigationContext(
        analytic_question="Test investigation about user engagement patterns",
        investigation_scope="social_media_analysis"
    )
    
    graph = InvestigationGraph()
    llm_client = get_litellm_client()
    
    # Create synthesizer with a simple investigation_id instead of complex logger
    synthesizer = RealTimeInsightSynthesizer(
        llm_client=llm_client,
        graph=graph, 
        context=context
    )
    
    # Create test InsightSynthesis object directly
    test_insight = InsightSynthesis(
        title="Mobile Evening Visual Engagement Peak",
        content="Analysis reveals that mobile users show highest engagement with visual content during evening hours, with 3x higher interaction rates compared to desktop users. This pattern suggests optimal posting times and content strategies.",
        confidence_level=0.85,
        pattern_type="trend", 
        key_evidence=[
            "Mobile users show 3x higher interaction rates",
            "Peak engagement occurs during evening hours 6-9 PM",
            "Video content receives 65% more engagement than static images"
        ],
        investigation_relevance=0.92
    )
    
    print(f"Created test InsightSynthesis:")
    print(f"  Title: '{test_insight.title}'")
    print(f"  Confidence: {test_insight.confidence_level}")
    print(f"  Pattern: {test_insight.pattern_type}")
    
    # Create a dummy supporting DataPoint node
    dp_wrapper = graph.create_datapoint_node(
        content="Test datapoint for insight creation",
        source="test_source", 
        relevance_score=0.9,
        confidence_score=0.8
    )
    
    supporting_node = graph.nodes[dp_wrapper.id]  # Access actual node using wrapper's id
    
    print(f"Created supporting DataPoint: {dp_wrapper.id}")
    
    try:
        # Call the _create_insight_node method directly
        insight_node = synthesizer._create_insight_node(test_insight, [supporting_node])
        
        print(f"Created insight node: {insight_node.id}")
        print(f"Node properties:")
        for key, value in insight_node.properties.items():
            print(f"  {key}: {value}")
            
        # Check if it was added to graph
        if insight_node.id in graph.nodes:
            print("SUCCESS: Insight node added to graph")
            
            # Check properties in graph
            stored_node = graph.nodes[insight_node.id]
            print("Properties in graph:")
            for key, value in stored_node.properties.items():
                print(f"  {key}: {value}")
                
            # Specifically check for title and confidence
            title = stored_node.properties.get('title')
            confidence = stored_node.properties.get('confidence')
            
            print(f"\nCRITICAL CHECK:")
            print(f"  Title property: '{title}' (type: {type(title)})")
            print(f"  Confidence property: {confidence} (type: {type(confidence)})")
            
            if title and title != "Untitled" and confidence is not None:
                print("SUCCESS: Title and confidence properly set!")
                return True
            else:
                print("FAILURE: Title or confidence missing/incorrect")
                return False
        else:
            print("ERROR: Insight node not found in graph")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Phase 1 Issue #2 Simple Debug Test")
    print("=" * 50)
    
    success = test_direct_insight_creation()
    
    print(f"\nRESULT: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)