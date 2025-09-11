#!/usr/bin/env python3
"""
Debug insight synthesis pipeline with full response logging
Phase 1: Issue #2 - Untitled Insight Generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
from realtime_insight_synthesizer import RealTimeInsightSynthesizer, InsightSynthesis
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph
from llm_client import get_litellm_client


def test_insight_pipeline_debug():
    """Debug the complete insight synthesis pipeline with full logging"""
    
    print("Debugging insight synthesis pipeline...")
    
    # Initialize components
    context = InvestigationContext(
        analytic_question="Test investigation about user engagement patterns",
        investigation_scope="social_media_analysis"
    )
    
    graph = InvestigationGraph()
    llm_client = get_litellm_client()
    
    synthesizer = RealTimeInsightSynthesizer(
        context=context,
        graph=graph,
        llm_client=llm_client
    )
    
    # Create test DataPoint nodes to trigger insight synthesis
    print("\nStep 1: Adding test DataPoint nodes...")
    test_findings = [
        {"content": "Users engage 65% more with video content than static images", "relevance": 0.9, "confidence": 0.8},
        {"content": "Peak engagement occurs during evening hours 6-9 PM", "relevance": 0.85, "confidence": 0.9}, 
        {"content": "Mobile users show 3x higher interaction rates on visual posts", "relevance": 0.9, "confidence": 0.85}
    ]
    
    datapoint_ids = []
    for i, finding in enumerate(test_findings):
        datapoint_id = graph.create_datapoint_node(
            content=finding["content"],
            source=f"test_source_{i}",
            relevance_score=finding["relevance"],
            confidence_score=finding["confidence"]
        )
        datapoint_ids.append(datapoint_id)
        print(f"  Created DataPoint {i+1}: {finding['content'][:50]}...")
    
    # Trigger insight synthesis process
    print(f"\nStep 2: Triggering insight synthesis for {len(datapoint_ids)} DataPoints...")
    
    # Add debugging to the synthesizer by monkey-patching the LLM call
    original_llm_completion = synthesizer.llm.completion
    
    def debug_llm_completion(*args, **kwargs):
        print("DEBUG: LLM completion called with:")
        print(f"  Model: {args[0] if args else 'not specified'}")
        print(f"  Response format: {kwargs.get('response_format', 'not specified')}")
        
        # Make the actual call
        response = original_llm_completion(*args, **kwargs)
        
        # Log the response
        print("DEBUG: LLM response received:")
        if response.choices and response.choices[0].message:
            if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                parsed = response.choices[0].message.parsed
                print(f"  Parsed object type: {type(parsed)}")
                if isinstance(parsed, InsightSynthesis):
                    print(f"  Title: '{parsed.title}'")
                    print(f"  Confidence: {parsed.confidence_level}")
                    print(f"  Pattern: {parsed.pattern_type}")
                    print(f"  Content length: {len(parsed.content)}")
                    print(f"  Evidence count: {len(parsed.key_evidence)}")
                else:
                    print(f"  Parsed content: {str(parsed)[:200]}...")
            else:
                content = response.choices[0].message.content
                print(f"  Raw content: {content[:200] if content else 'None'}...")
        
        return response
    
    synthesizer.llm.completion = debug_llm_completion
    
    # Attempt insight synthesis by processing each datapoint
    print("\nStep 3: Running insight synthesis...")
    try:
        insights_created = []
        for datapoint_id in datapoint_ids:
            result = synthesizer.process_new_datapoint(datapoint_id)
            if result:
                insights_created.extend(result)
        
        # Check graph state for created insights
        print("\nStep 4: Checking graph state for insights...")
        nodes = graph.get_all_nodes()
        insights = [node for node in nodes.values() if node.get('node_type') == 'Insight']
        
        print(f"Found {len(insights)} insight nodes:")
        for i, insight in enumerate(insights):
            props = insight.get('properties', {})
            print(f"  Insight {i+1}:")
            print(f"    Title: '{props.get('title', 'MISSING')}'")
            print(f"    Confidence: {props.get('confidence', 'MISSING')}")
            print(f"    Content: {props.get('content', 'MISSING')[:100]}...")
            print(f"    All properties: {list(props.keys())}")
            
        return len(insights) > 0 and all(
            props.get('title') and props.get('title') != 'Untitled' 
            for insight in insights 
            for props in [insight.get('properties', {})]
        )
        
    except Exception as e:
        print(f"ERROR during insight synthesis: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_synthesis():
    """Test the _synthesize_group_insight method directly"""
    
    print("\n" + "="*60)
    print("TESTING: Direct insight synthesis method")
    print("="*60)
    
    # Initialize components
    context = InvestigationContext(
        analytic_question="Test investigation about user engagement patterns",
        investigation_scope="social_media_analysis"
    )
    
    graph = InvestigationGraph()
    llm_client = get_litellm_client()
    
    synthesizer = RealTimeInsightSynthesizer(
        context=context,
        graph=graph,
        llm_client=llm_client
    )
    
    # Test data
    content_items = [
        "Users engage 65% more with video content than static images",
        "Peak engagement occurs during evening hours 6-9 PM", 
        "Mobile users show 3x higher interaction rates on visual posts"
    ]
    
    group_datapoints = ["test_dp_1", "test_dp_2", "test_dp_3"]
    
    print(f"Testing synthesis with {len(content_items)} content items...")
    
    try:
        # Create actual node objects for the method
        test_nodes = []
        for i, content in enumerate(content_items):
            node_id = graph.create_datapoint_node(
                content=content,
                source=f"test_source_{i}",
                relevance_score=0.9,
                confidence_score=0.8
            )
            node = graph.get_node(node_id)
            test_nodes.append(node)
        
        # Call the method directly
        insight_result = synthesizer._synthesize_group_insight(test_nodes)
        
        print(f"Synthesis returned insight result: {insight_result}")
        
        # The method returns InsightSynthesis object, not node ID
        if insight_result:
            print(f"InsightSynthesis object created:")
            print(f"  Title: '{insight_result.title}'")
            print(f"  Confidence: {insight_result.confidence_level}")
            print(f"  Pattern: {insight_result.pattern_type}")
            print(f"  Content: {insight_result.content[:100]}...")
        
        # Check if any insight nodes were created in graph
        nodes = graph.get_all_nodes()
        insights = [node for node in nodes.values() if node.get('node_type') == 'Insight']
        if insights:
            for i, insight_node in enumerate(insights):
                props = insight_node.get('properties', {})
                print(f"Insight node {i+1} properties:")
                for key, value in props.items():
                    print(f"  {key}: {value}")
        else:
            print("No insight nodes created in graph")
        
        return True
        
    except Exception as e:
        print(f"ERROR in direct synthesis: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Phase 1 Issue #2 Debugging: Insight Synthesis Pipeline")
    print("="*60)
    
    success1 = test_insight_pipeline_debug()
    success2 = test_direct_synthesis()
    
    print("\n" + "="*60)
    print("DEBUGGING RESULTS:")
    print(f"  Pipeline test: {'PASS' if success1 else 'FAIL'}")
    print(f"  Direct synthesis: {'PASS' if success2 else 'FAIL'}")
    
    if success1 and success2:
        print("  CONCLUSION: Insight synthesis pipeline is working correctly")
    else:
        print("  CONCLUSION: Issues found in insight synthesis pipeline")
    
    sys.exit(0 if (success1 and success2) else 1)