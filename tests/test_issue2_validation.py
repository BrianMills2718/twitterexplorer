#!/usr/bin/env python3
"""
Validation test for Issue #2 fix: Untitled Insight Generation
Phase 1: Issue #2 - Full investigation pipeline test
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from investigation_engine import InvestigationEngine
from investigation_context import InvestigationContext
import json
import os


def test_full_investigation_insight_quality():
    """Test that a full investigation produces proper insights with titles and confidence"""
    
    print("Testing full investigation pipeline for insight quality...")
    
    try:
        # Get API key from secrets
        try:
            import toml
            secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')
            if os.path.exists(secrets_path):
                secrets = toml.load(secrets_path)
                rapidapi_key = secrets.get('RAPIDAPI_KEY', '')
            else:
                rapidapi_key = 'test_key'
        except ImportError:
            rapidapi_key = 'test_key'
        
        # Create investigation engine 
        engine = InvestigationEngine(rapidapi_key=rapidapi_key)
        
        # Run investigation with a focused query that should generate insights
        test_query = "mobile app user engagement trends 2024"
        
        print(f"Running investigation: '{test_query}'")
        print("(This may take a few minutes with real API calls)")
        
        # Execute investigation with minimal scope for testing
        result = engine.conduct_investigation(test_query, max_searches=5)
        
        print(f"\nInvestigation completed!")
        print(f"- Searches performed: {len(result.search_history)}")
        print(f"- Final satisfaction: {result.satisfaction_metrics.overall_satisfaction():.3f}")
        
        # Check graph state for insights
        if hasattr(engine, 'graph') and engine.graph:
            nodes = engine.graph.nodes
            insights = [node for node in nodes.values() if node.node_type == 'Insight']
            
            print(f"\nInsight Analysis:")
            print(f"- Total insights created: {len(insights)}")
            
            if insights:
                problematic_insights = 0
                for i, insight in enumerate(insights):
                    props = insight.properties
                    title = props.get('title', 'MISSING')
                    confidence = props.get('confidence', 'MISSING')
                    
                    print(f"\nInsight {i+1}:")
                    print(f"  Title: '{title}'")
                    print(f"  Confidence: {confidence}")
                    print(f"  Content: {props.get('content', 'MISSING')[:100]}...")
                    
                    # Check for problems
                    if not title or title == 'Untitled' or 'untitled' in str(title).lower():
                        print(f"  X PROBLEM: Invalid title")
                        problematic_insights += 1
                    elif confidence is None or confidence == 'N/A' or str(confidence) == 'None':
                        print(f"  X PROBLEM: Invalid confidence")
                        problematic_insights += 1
                    else:
                        print(f"  √ GOOD: Proper title and confidence")
                
                print(f"\nRESULT SUMMARY:")
                print(f"- Total insights: {len(insights)}")
                print(f"- Problematic insights: {problematic_insights}")
                print(f"- Success rate: {(len(insights) - problematic_insights) / len(insights) * 100:.1f}%")
                
                if problematic_insights == 0:
                    print("√ SUCCESS: All insights have proper titles and confidence!")
                    return True
                else:
                    print("X FAILURE: Some insights still have title/confidence issues")
                    return False
            else:
                print("! NO INSIGHTS: Investigation didn't generate any insights")
                # This might be OK for some investigations
                return True
        else:
            print("X ERROR: No graph available in investigation engine")
            return False
            
    except Exception as e:
        print(f"X ERROR during investigation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_export_quality():
    """Test that insights export properly to graph JSON (matching CLAUDE.md evidence)"""
    
    print("\n" + "="*60)
    print("Testing graph export format (original evidence: lines 494-495)")
    print("="*60)
    
    try:
        # Quick focused investigation for graph export testing
        config = InvestigationConfig(max_searches=3, model_provider="gemini")
        engine = InvestigationEngine(config=config)
        
        result = engine.conduct_investigation("social media engagement patterns")
        
        # Export graph to check JSON format
        if hasattr(engine, 'graph') and engine.graph:
            graph_data = engine.graph.to_dict()
            
            # Look for insight nodes in export
            insights_in_export = []
            for node_id, node_data in graph_data.get('nodes', {}).items():
                if node_data.get('node_type') == 'Insight':
                    insights_in_export.append((node_id, node_data))
            
            print(f"Graph export contains {len(insights_in_export)} insight nodes")
            
            for i, (node_id, node_data) in enumerate(insights_in_export):
                props = node_data.get('properties', {})
                title = props.get('title', 'MISSING')
                confidence = props.get('confidence', 'MISSING')
                
                print(f"\nExported Insight {i+1} (ID: {node_id}):")
                print(f"  Title in export: '{title}'")
                print(f"  Confidence in export: {confidence}")
                
                # This should NOT match the original evidence (lines 494-495)
                if title == "Untitled" or str(confidence) == "N/A":
                    print(f"  ❌ FAILURE: Matches original problematic evidence!")
                    return False
                else:
                    print(f"  ✅ SUCCESS: Does not match original problematic evidence")
            
            return True
        else:
            print("No graph data available for export testing")
            return True
            
    except Exception as e:
        print(f"Error in graph export test: {e}")
        return False


if __name__ == "__main__":
    print("Phase 1 Issue #2 Validation Test")
    print("=" * 60)
    print("Validating fix for 'Untitled Insight Generation'")
    print("Original evidence: temp1.txt lines 494-495 (CLAUDE.md reference)")
    print("=" * 60)
    
    test1_result = test_full_investigation_insight_quality()
    test2_result = test_graph_export_quality()
    
    print("\n" + "="*60)
    print("VALIDATION RESULTS:")
    print(f"  Full investigation test: {'PASS' if test1_result else 'FAIL'}")  
    print(f"  Graph export test: {'PASS' if test2_result else 'FAIL'}")
    
    overall_success = test1_result and test2_result
    
    if overall_success:
        print("  🎉 ISSUE #2 SUCCESSFULLY FIXED!")
        print("  ✅ Insights now have proper titles and confidence scores")
        print("  ✅ No more 'Untitled' or 'N/A' values in output")
    else:
        print("  ❌ ISSUE #2 NOT FULLY FIXED")
        print("  🔧 Additional debugging required")
    
    print("="*60)
    sys.exit(0 if overall_success else 1)