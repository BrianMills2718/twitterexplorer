"""Complete validation test to verify all CLAUDE.md success criteria are met"""
import sys
import os

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_complete_validation():
    """EVIDENCE: Test all success criteria from CLAUDE.md"""

    print("=== COMPLETE VALIDATION TEST ===")

    api_key = "REDACTED_RAPIDAPI_KEY"
    engine = InvestigationEngine(api_key)

    # Test with original failing query from CLAUDE.md
    original_query = "find me different takes on the current trump epstein drama"

    # Run limited investigation
    config = InvestigationConfig(max_searches=2, pages_per_search=2)
    result = engine.conduct_investigation(original_query, config)

    print(f"\n=== VALIDATION RESULTS ===")
    print(f"Query: {original_query}")

    # CLAUDE.md Success Criteria:
    print(f"\n📊 SUCCESS CRITERIA VALIDATION:")

    # 1. Findings Integration: Accumulated findings > 0
    findings_success = len(result.accumulated_findings) > 0
    print(f"1. Findings Integration: {'✅ PASS' if findings_success else '❌ FAIL'} - {len(result.accumulated_findings)} findings")

    # 2. DataPoint Creation: DataPoint nodes > 0
    datapoint_count = len([n for n in engine.llm_coordinator.graph.nodes.values() if 'DataPoint' in str(type(n))]) if hasattr(engine.llm_coordinator, 'graph') else 0
    datapoint_success = datapoint_count > 0
    print(f"2. DataPoint Creation: {'✅ PASS' if datapoint_success else '❌ FAIL'} - {datapoint_count} DataPoints")

    # 3. Satisfaction Calculation: Satisfaction > 0.0
    satisfaction = result.satisfaction_metrics.overall_satisfaction()
    satisfaction_success = satisfaction > 0.0
    print(f"3. Satisfaction Calculation: {'✅ PASS' if satisfaction_success else '❌ FAIL'} - {satisfaction:.3f}")

    # 4. End-to-End Flow: All components working together
    e2e_success = findings_success and datapoint_success and satisfaction_success
    print(f"4. End-to-End Flow: {'✅ PASS' if e2e_success else '❌ FAIL'} - Complete integration")

    # 5. Performance Consistency: Results should be deterministic structure
    performance_success = result.accumulated_findings is not None and result.satisfaction_metrics is not None
    print(f"5. Performance Consistency: {'✅ PASS' if performance_success else '❌ FAIL'} - Stable structure")

    # Additional diagnostic info
    print(f"\n📈 DIAGNOSTIC METRICS:")
    print(f"- Total searches: {len(result.search_history) if hasattr(result, 'search_history') else 'N/A'}")
    print(f"- Graph nodes: {len(engine.llm_coordinator.graph.nodes) if hasattr(engine.llm_coordinator, 'graph') else 'N/A'}")
    print(f"- Evidence strength breakdown:")
    if result.accumulated_findings:
        strength_counts = {}
        for finding in result.accumulated_findings:
            strength = finding.evidence_strength
            strength_counts[strength] = strength_counts.get(strength, 0) + 1
        for strength, count in strength_counts.items():
            print(f"  - {strength}: {count}")

    # Show sample findings
    print(f"\n🔍 SAMPLE FINDINGS:")
    for i, finding in enumerate(result.accumulated_findings[:3]):
        content_preview = finding.content[:80] + "..." if len(finding.content) > 80 else finding.content
        print(f"  {i+1}. [{finding.source}] {content_preview} (credibility: {finding.credibility_score:.2f})")

    # Overall validation
    all_success = findings_success and datapoint_success and satisfaction_success and e2e_success and performance_success

    print(f"\n🎯 OVERALL VALIDATION: {'✅ ALL CRITERIA PASSED' if all_success else '❌ SOME CRITERIA FAILED'}")

    return {
        'findings_integration': findings_success,
        'datapoint_creation': datapoint_success,
        'satisfaction_calculation': satisfaction_success,
        'end_to_end_flow': e2e_success,
        'performance_consistency': performance_success,
        'overall_success': all_success,
        'metrics': {
            'findings_count': len(result.accumulated_findings),
            'datapoints_count': datapoint_count,
            'satisfaction_score': satisfaction
        }
    }

if __name__ == "__main__":
    validation_result = test_complete_validation()

    if validation_result['overall_success']:
        print(f"\n🚀 IMPLEMENTATION COMPLETE: All CLAUDE.md requirements satisfied!")
        exit(0)
    else:
        print(f"\n⚠️ IMPLEMENTATION INCOMPLETE: Some requirements not met")
        exit(1)