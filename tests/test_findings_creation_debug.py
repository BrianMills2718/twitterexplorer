"""Debug findings creation step by step"""
import sys
import os

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_findings_creation_debug():
    """EVIDENCE: Debug the exact point where findings creation fails"""

    print("=== FINDINGS CREATION DEBUG ===")

    api_key = "REDACTED_RAPIDAPI_KEY"
    engine = InvestigationEngine(api_key)

    # Patch the analysis method to add detailed debug output
    original_analyze = engine._analyze_round_results_with_llm

    def debug_findings_creation(session, round_obj, results):
        print(f"\n=== FINDINGS CREATION DEBUG ===")
        print(f"Session accumulated_findings before: {len(session.accumulated_findings)}")

        for attempt in results:
            print(f"\nProcessing attempt: {attempt.endpoint}")

            if attempt.results_count > 0 and hasattr(attempt, '_raw_results'):
                print(f"  Has {len(attempt._raw_results)} raw results")

                # Get LLM client
                llm_client = getattr(engine.llm_coordinator, 'llm', None) or getattr(engine.llm_coordinator, 'llm_client', None)

                from finding_evaluator_llm import LLMFindingEvaluator
                finding_evaluator = LLMFindingEvaluator(llm_client)

                # Test with just first result
                results_to_eval = attempt._raw_results[:1]
                print(f"  Evaluating {len(results_to_eval)} results")

                try:
                    assessments = finding_evaluator.evaluate_batch(results_to_eval, session.original_query)
                    print(f"  Got {len(assessments)} assessments")

                    for i, (raw_result, assessment) in enumerate(zip(results_to_eval, assessments)):
                        print(f"    Result {i}: is_significant={assessment.is_significant}")

                        if assessment.is_significant:
                            print(f"      Creating Finding object...")

                            # Create Finding
                            from investigation_engine import Finding

                            finding = Finding(
                                content=raw_result.get('text', ''),
                                source=attempt.endpoint,
                                credibility_score=assessment.relevance_score,
                                category='tweet',
                                search_id=attempt.search_id,
                                evidence_strength='medium' if assessment.relevance_score > 0.5 else 'low'
                            )
                            print(f"      Finding created: {finding}")

                            # Add to session
                            print(f"      Adding to session.accumulated_findings...")
                            session.accumulated_findings.append(finding)
                            print(f"      Session findings count now: {len(session.accumulated_findings)}")
                        else:
                            print(f"      Skipping - not significant")

                except Exception as e:
                    print(f"  ERROR: {e}")
                    import traceback
                    traceback.print_exc()

        print(f"\nSession accumulated_findings after manual test: {len(session.accumulated_findings)}")

        # Also call original method
        result = original_analyze(session, round_obj, results)

        print(f"Session accumulated_findings after original method: {len(session.accumulated_findings)}")

        return result

    engine._analyze_round_results_with_llm = debug_findings_creation

    # Run investigation
    config = InvestigationConfig(max_searches=1, pages_per_search=1)
    result = engine.conduct_investigation("Debug findings creation", config)

    print(f"\n=== FINAL RESULT ===")
    print(f"Final findings: {len(result.accumulated_findings)}")

if __name__ == "__main__":
    test_findings_creation_debug()