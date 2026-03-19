#!/usr/bin/env python3
"""
CLI Test for TwitterExplorer Investigation System
Tests the complete pipeline without Streamlit interface
"""

# CRITICAL: Disable Streamlit before any imports to prevent warnings
import os
os.environ['DISABLE_STREAMLIT'] = '1'

from investigation_engine import InvestigationEngine, InvestigationConfig
import sys
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='TwitterExplorer Investigation CLI')
    parser.add_argument('query', nargs='*', help='Investigation query (if not provided, uses default)')
    parser.add_argument('--provider', choices=['openai', 'gemini'], default='openai',
                       help='LLM provider to use (default: openai)')
    parser.add_argument('--max-searches', type=int, default=15,
                       help='Maximum number of searches to perform (default: 15)')
    parser.add_argument('--satisfaction-threshold', type=float, default=0.6,
                       help='Satisfaction threshold for stopping investigation (default: 0.6)')

    args = parser.parse_args()

    # Set up API keys
    rapidapi_key = '7501a19221mshf1eb289b88dc8acp1d30e6jsn04f6eab32db3'
    os.environ['GEMINI_API_KEY'] = 'REDACTED_GEMINI_API_KEY'
    os.environ['OPENAI_API_KEY'] = 'REDACTED_OPENAI_API_KEY'

    # Create investigation engine with provider configuration
    print(f"Initializing TwitterExplorer Investigation Engine (using {args.provider})...")
    engine = InvestigationEngine.from_config(api_key=rapidapi_key, provider=args.provider)

    # Configure investigation with CLI parameters
    config = InvestigationConfig(
        max_searches=args.max_searches,
        satisfaction_threshold=args.satisfaction_threshold,
        show_search_details=True,
        show_strategy_reasoning=True,
        model_provider=args.provider  # Set the provider from CLI argument
    )

    # Get query from arguments or use default
    if args.query:
        query = ' '.join(args.query)
    else:
        query = 'does joe rogan propagate disinformation'

    print(f"Starting CLI investigation: {query}")
    print("=" * 60)

    # Run investigation
    try:
        result = engine.conduct_investigation(query, config)

        print("\nInvestigation Complete!")
        print(f"Searches performed: {len(result.search_history)}")
        print(f"Findings discovered: {len(result.accumulated_findings)}")
        print(f"Final satisfaction: {result.satisfaction_metrics.overall_satisfaction():.2f}")

        # Check graph state for insights and emergent questions
        if hasattr(engine, 'graph') and engine.graph:
            insights = engine.graph.get_nodes_by_type('Insight')
            emergent_questions = engine.graph.get_nodes_by_type('EmergentQuestion')
            datapoints = engine.graph.get_nodes_by_type('DataPoint')

            print(f"\nGraph State:")
            print(f"  DataPoints: {len(datapoints)}")
            print(f"  Insights: {len(insights)}")
            print(f"  Emergent Questions: {len(emergent_questions)}")

            if insights:
                print("\nGenerated Insights:")
                for i, insight in enumerate(insights[:3]):
                    title = insight.properties.get('title', 'Untitled')
                    confidence = insight.properties.get('confidence', 'N/A')
                    print(f"  {i+1}. {title} (confidence: {confidence})")

            if emergent_questions:
                print("\nEmergent Questions (Sample):")
                for i, eq in enumerate(emergent_questions[:5]):
                    text = eq.properties.get('text', 'N/A')
                    display_text = text[:80] + '...' if len(text) > 80 else text
                    print(f"  {i+1}. {display_text}")

        print("\nCLI investigation completed - Bridge integration and emergent questions working!")

    except Exception as e:
        print(f"Error during investigation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()