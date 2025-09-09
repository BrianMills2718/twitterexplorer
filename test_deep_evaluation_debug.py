"""Deep debug of the LLM evaluation process to find why findings aren't created"""
import sys
import os

from investigation_engine import InvestigationEngine, InvestigationConfig
from finding_evaluator_llm import LLMFindingEvaluator

def test_deep_evaluation_debug():
    """EVIDENCE: Trace the complete evaluation process step by step"""
    
    print("=== DEEP EVALUATION DEBUG ===")
    
    api_key = "d72bcd77e2msh76c7e6cf37f0b89p1c51bcjsnaad0f6b01e4f"
    engine = InvestigationEngine(api_key)
    
    # Patch the analysis method for deep debugging
    original_analyze = engine._analyze_round_results_with_llm
    
    def deep_debug_analyze(session, round_obj, results):
        print(f"\n=== DEEP ANALYSIS OF {len(results)} RESULTS ===")
        
        # Manual step-by-step execution of the analysis logic
        for attempt in results:
            print(f"\nAnalyzing attempt: {attempt.endpoint}")
            print(f"  Results count: {attempt.results_count}")
            print(f"  Has _raw_results: {hasattr(attempt, '_raw_results')}")
            
            if attempt.results_count > 0 and hasattr(attempt, '_raw_results'):
                print(f"  Condition MET: results_count > 0 and has _raw_results")
                
                # Check LLM client setup
                llm_client = None
                if hasattr(engine.llm_coordinator, 'llm'):
                    llm_client = engine.llm_coordinator.llm
                    print(f"  Using llm_coordinator.llm: {type(llm_client)}")
                elif hasattr(engine.llm_coordinator, 'llm_client'):
                    llm_client = engine.llm_coordinator.llm_client
                    print(f"  Using llm_coordinator.llm_client: {type(llm_client)}")
                else:
                    print(f"  ERROR: No LLM client found!")
                
                # Initialize evaluator
                try:
                    finding_evaluator = LLMFindingEvaluator(llm_client)
                    print(f"  LLM evaluator created successfully")
                    
                    # Get sample results
                    results_to_eval = attempt._raw_results[:3]  # Just first 3 for debug
                    print(f"  Evaluating {len(results_to_eval)} results")
                    
                    # Show sample data
                    for i, raw_result in enumerate(results_to_eval):
                        sample_text = str(raw_result.get('text', ''))[:100]
                        print(f"    Sample {i+1}: {sample_text}...")
                    
                    # Try batch evaluation
                    print(f"  Calling evaluate_batch...")
                    assessments = finding_evaluator.evaluate_batch(
                        results_to_eval,
                        session.original_query
                    )
                    print(f"  Batch evaluation returned {len(assessments)} assessments")
                    
                    # Check assessment results
                    significant_count = 0
                    for i, assessment in enumerate(assessments):
                        print(f"    Assessment {i+1}: is_significant={assessment.is_significant}, relevance={assessment.relevance_score}")
                        if assessment.is_significant:
                            significant_count += 1
                    
                    print(f"  SIGNIFICANT ASSESSMENTS: {significant_count}/{len(assessments)}")
                    
                    # Check graph mode
                    print(f"  Graph mode: {engine.graph_mode}")
                    print(f"  Has coordinator.graph: {hasattr(engine.llm_coordinator, 'graph')}")
                    
                    if engine.graph_mode and hasattr(engine.llm_coordinator, 'graph'):
                        print(f"  Graph node count before: {len(engine.llm_coordinator.graph.nodes)}")
                        
                        # Try creating DataPoints manually
                        for raw_result, assessment in zip(results_to_eval, assessments):
                            if assessment.is_significant:
                                print(f"  Creating DataPoint for significant finding...")
                                try:
                                    dp = engine.llm_coordinator.graph.create_datapoint_node(
                                        content=raw_result.get('text', ''),
                                        source=attempt.endpoint,
                                        timestamp="2025-08-27T16:25:00",
                                        entities=assessment.entities,
                                        follow_up_needed=assessment.suggested_followup
                                    )
                                    print(f"    DataPoint created: {dp.id}")
                                except Exception as e:
                                    print(f"    ERROR creating DataPoint: {e}")
                        
                        print(f"  Graph node count after: {len(engine.llm_coordinator.graph.nodes)}")
                
                except Exception as e:
                    print(f"  ERROR in evaluation process: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"  Condition NOT MET: results_count={attempt.results_count}, has_raw_results={hasattr(attempt, '_raw_results')}")
        
        # Also call original method to see what it does  
        return original_analyze(session, round_obj, results)
    
    engine._analyze_round_results_with_llm = deep_debug_analyze
    
    # Run investigation
    config = InvestigationConfig(max_searches=1, pages_per_search=1)
    result = engine.conduct_investigation("Test deep evaluation", config)
    
    print(f"\n=== FINAL RESULTS ===")
    print(f"Findings: {len(result.accumulated_findings)}")
    print(f"Satisfaction: {result.satisfaction_metrics.overall_satisfaction()}")
    print(f"Graph nodes: {len(engine.llm_coordinator.graph.nodes) if hasattr(engine.llm_coordinator, 'graph') else 'NO GRAPH'}")

if __name__ == "__main__":
    test_deep_evaluation_debug()