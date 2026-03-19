"""Test with a specific query that should generate significant findings"""
import sys
import os

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_specific_query_debug():
    """EVIDENCE: Test with a query that should produce significant findings"""

    print("=== SPECIFIC QUERY DEBUG ===")

    api_key = "REDACTED_RAPIDAPI_KEY"
    engine = InvestigationEngine(api_key)

    # Use a targeted query that should generate significant results
    specific_query = "What is Elon Musk saying about artificial intelligence"

    # Run investigation with query that should match content
    config = InvestigationConfig(max_searches=1, pages_per_search=1)
    result = engine.conduct_investigation(specific_query, config)

    print(f"\n=== RESULTS ===")
    print(f"Query: {specific_query}")
    print(f"Findings: {len(result.accumulated_findings)}")
    print(f"DataPoints: {len(engine.llm_coordinator.graph.nodes) if hasattr(engine.llm_coordinator, 'graph') else 'NO GRAPH'}")
    print(f"Satisfaction: {result.satisfaction_metrics.overall_satisfaction()}")

    # Show first few findings if any
    for i, finding in enumerate(result.accumulated_findings[:3]):
        print(f"  Finding {i+1}: {finding.content[:100]}...")

    return len(result.accumulated_findings) > 0

def test_with_manual_significant_data():
    """EVIDENCE: Test with manually created 'significant' data"""

    print("\n=== MANUAL SIGNIFICANT DATA TEST ===")

    from finding_evaluator_llm import LLMFindingEvaluator

    evaluator = LLMFindingEvaluator()

    # Create data that should be considered significant
    test_data = [
        {'text': 'Elon Musk announced new AI safety measures for X platform today', 'source': 'timeline.php'},
        {'text': 'Breaking: Musk reveals X platform will integrate advanced AI features', 'source': 'search.php'},
        {'text': 'Major update from @elonmusk about artificial intelligence integration', 'source': 'timeline.php'}
    ]

    query = "What is Elon Musk saying about artificial intelligence"

    try:
        assessments = evaluator.evaluate_batch(test_data, query)
        print(f"Evaluated {len(assessments)} results")

        significant_count = sum(1 for a in assessments if a.is_significant)
        print(f"Significant results: {significant_count}/{len(assessments)}")

        for i, assessment in enumerate(assessments):
            print(f"  Result {i+1}: is_significant={assessment.is_significant}, relevance={assessment.relevance_score}")

        return significant_count > 0

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing with specific query...")
    has_findings = test_specific_query_debug()

    print("\nTesting with manual significant data...")
    has_significant = test_with_manual_significant_data()

    if has_findings:
        print("\n✅ SUCCESS: Integration working with real query")
    elif has_significant:
        print("\n⚠️ PARTIAL: LLM evaluation works, but real data not significant")
    else:
        print("\n❌ ISSUE: Both tests failed")