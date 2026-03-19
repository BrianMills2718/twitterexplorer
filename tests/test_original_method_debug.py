"""Debug the original _analyze_round_results_with_llm method to see why findings aren't added"""
import sys
import os

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_original_method_debug():
    """EVIDENCE: Step through the original method line by line"""

    print("=== ORIGINAL METHOD DEBUG ===")

    api_key = "REDACTED_RAPIDAPI_KEY"
    engine = InvestigationEngine(api_key)

    # Patch to add detailed debugging at key points
    original_analyze = engine._analyze_round_results_with_llm

    def debug_original_method(session, round_obj, results):
        print(f"\\n=== ORIGINAL METHOD STEP BY STEP ===")
        print(f"Session findings before: {len(session.accumulated_findings)}")

        # Call original with detailed monitoring
        try:
            print("Calling original method...")
            result = original_analyze(session, round_obj, results)
            print(f"Original method completed")
            print(f"Session findings after: {len(session.accumulated_findings)}")
            return result
        except Exception as e:
            print(f"ERROR in original method: {e}")
            import traceback
            traceback.print_exc()
            raise

    # Also patch the Finding constructor to see if it's being called
    from investigation_engine import Finding
    original_finding_init = Finding.__init__

    def debug_finding_init(self, *args, **kwargs):
        print(f"  FINDING CONSTRUCTOR CALLED: args={args}, kwargs={kwargs}")
        return original_finding_init(self, *args, **kwargs)

    Finding.__init__ = debug_finding_init

    engine._analyze_round_results_with_llm = debug_original_method

    # Run with query that should produce results
    config = InvestigationConfig(max_searches=1, pages_per_search=1)
    result = engine.conduct_investigation("What is Elon Musk saying about AI", config)

    print(f"\\n=== FINAL RESULT ===")
    print(f"Final findings: {len(result.accumulated_findings)}")
    print(f"Final DataPoints: {len(engine.llm_coordinator.graph.nodes) if hasattr(engine.llm_coordinator, 'graph') else 'NO GRAPH'}")

    # Inspect the first few DataPoints to see their content
    if hasattr(engine.llm_coordinator, 'graph'):
        datapoint_nodes = [n for n in engine.llm_coordinator.graph.nodes.values() if 'DataPoint' in str(type(n))]
        print(f"DataPoint nodes found: {len(datapoint_nodes)}")
        for i, dp in enumerate(datapoint_nodes[:2]):
            if hasattr(dp, 'properties'):
                content = dp.properties.get('content', 'NO CONTENT')[:100]
                print(f"  DataPoint {i+1}: {content}...")

if __name__ == "__main__":
    test_original_method_debug()