#!/usr/bin/env python3
"""
Test script to verify emergent question reduction fix
"""

import os
os.environ['DISABLE_STREAMLIT'] = '1'

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_emergent_question_reduction():
    """Test that the emergent question explosion fix works"""
    print("Testing emergent question reduction fix...")

    # Set up API keys
    rapidapi_key = '7501a19221mshf1eb289b88dc8acp1d30e6jsn04f6eab32db3'
    os.environ['GEMINI_API_KEY'] = 'REDACTED_GEMINI_API_KEY'
    os.environ['OPENAI_API_KEY'] = 'REDACTED_OPENAI_API_KEY'

    # Create engine
    engine = InvestigationEngine.from_config(api_key=rapidapi_key, provider='openai')

    # Configure investigation with limited searches
    config = InvestigationConfig(
        max_searches=3,  # Small number to test quickly
        satisfaction_threshold=0.3,  # Lower threshold for quick completion
        show_search_details=False,
        show_strategy_reasoning=False,
        model_provider='openai'
    )

    query = 'test emergent question generation'
    print(f"Running investigation: {query}")
    print("=" * 50)

    try:
        result = engine.conduct_investigation(query, config)

        print(f"\nInvestigation Complete!")
        print(f"Searches performed: {len(result.search_history)}")
        print(f"Findings discovered: {len(result.accumulated_findings)}")
        print(f"Final satisfaction: {result.satisfaction_metrics.overall_satisfaction():.2f}")

        # Check graph state
        if hasattr(engine, 'graph') and engine.graph:
            insights = engine.graph.get_nodes_by_type('Insight')
            emergent_questions = engine.graph.get_nodes_by_type('EmergentQuestion')
            datapoints = engine.graph.get_nodes_by_type('DataPoint')

            print(f"\nGraph State:")
            print(f"  DataPoints: {len(datapoints)}")
            print(f"  Insights: {len(insights)}")
            print(f"  Emergent Questions: {len(emergent_questions)}")

            if len(insights) > 0:
                ratio = len(emergent_questions) / len(insights)
                print(f"\nQuestion/Insight Ratio: {ratio:.2f} questions per insight")

                if ratio > 5.0:
                    print("WARNING: High question generation ratio detected!")
                    print(f"Expected: ~0.3-1.0 questions per insight")
                    print(f"Actual: {ratio:.2f} questions per insight")
                elif ratio < 2.0:
                    print("GOOD: Reasonable question generation ratio")
                    print("Fix appears to be working correctly")
                else:
                    print("MODERATE: Higher than ideal but manageable ratio")

            print("\nTest completed - emergent question generation analysis complete")
        else:
            print("No graph available for analysis")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_emergent_question_reduction()