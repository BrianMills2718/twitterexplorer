"""Debug why _raw_results attribute is missing from SearchAttempt objects"""
import sys
import os

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_raw_results_debug():
    """EVIDENCE: Check if SearchAttempt objects have _raw_results attribute"""

    print("=== RAW RESULTS DEBUG ===")

    api_key = "REDACTED_RAPIDAPI_KEY"
    engine = InvestigationEngine(api_key)

    # Patch the analysis method to examine SearchAttempt objects
    original_analyze = engine._analyze_round_results_with_llm
    debug_info = {}

    def debug_analyze(session, round_obj, results):
        print(f"\n=== ANALYZING {len(results)} RESULTS ===")

        for i, attempt in enumerate(results):
            print(f"  Result {i+1}:")
            print(f"    - Type: {type(attempt)}")
            print(f"    - Endpoint: {getattr(attempt, 'endpoint', 'NO ENDPOINT')}")
            print(f"    - Results count: {getattr(attempt, 'results_count', 'NO RESULTS_COUNT')}")
            print(f"    - Has _raw_results: {hasattr(attempt, '_raw_results')}")

            if hasattr(attempt, '_raw_results'):
                raw_results = getattr(attempt, '_raw_results')
                print(f"    - _raw_results type: {type(raw_results)}")
                print(f"    - _raw_results length: {len(raw_results) if raw_results else 0}")
            else:
                # Check what attributes it does have
                attrs = [attr for attr in dir(attempt) if not attr.startswith('__')]
                print(f"    - Available attributes: {attrs}")

        # Call original method to see what happens
        return original_analyze(session, round_obj, results)

    engine._analyze_round_results_with_llm = debug_analyze

    # Run investigation
    config = InvestigationConfig(max_searches=1, pages_per_search=1)
    result = engine.conduct_investigation("Test raw results debug", config)

    print(f"\n=== FINAL RESULTS ===")
    print(f"Findings: {len(result.accumulated_findings)}")
    print(f"Satisfaction: {result.satisfaction_metrics.overall_satisfaction()}")

    return len(result.accumulated_findings) == 0

if __name__ == "__main__":
    no_findings = test_raw_results_debug()
    if no_findings:
        print("\nCONFIRMED: No findings were created - raw_results issue confirmed")
    else:
        print("\nUNEXPECTED: Findings were created somehow")