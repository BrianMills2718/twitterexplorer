"""Trace exact method calls to identify where flow breaks"""
import sys
import os
import json

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_method_call_tracing():
    """EVIDENCE: Trace all method calls related to findings processing"""
    
    print("=== METHOD CALL TRACING ===")
    
    api_key = "d72bcd77e2msh76c7e6cf37f0b89p1c51bcjsnaad0f6b01e4f"
    engine = InvestigationEngine(api_key)
    
    # Track all method calls related to findings/DataPoints
    call_trace = []
    
    def trace_call(method_name, *args, **kwargs):
        call_trace.append({
            'method': method_name,
            'args_count': len(args),
            'kwargs': list(kwargs.keys())
        })
        print(f"TRACE: {method_name} called")
    
    # Patch key methods to trace calls
    if hasattr(engine, 'llm_coordinator') and hasattr(engine.llm_coordinator, 'graph'):
        # Patch DataPoint creation methods
        original_create_datapoint = getattr(engine.llm_coordinator.graph, 'create_datapoint_node', None)
        if original_create_datapoint:
            def traced_create_datapoint(*args, **kwargs):
                trace_call('create_datapoint_node', *args, **kwargs)
                return original_create_datapoint(*args, **kwargs)
            engine.llm_coordinator.graph.create_datapoint_node = traced_create_datapoint
        
        # Patch add_node method
        original_add_node = getattr(engine.llm_coordinator.graph, 'add_node', None) 
        if original_add_node:
            def traced_add_node(*args, **kwargs):
                trace_call('add_node', *args, **kwargs)  
                return original_add_node(*args, **kwargs)
            engine.llm_coordinator.graph.add_node = traced_add_node
    
    # Patch finding evaluator methods  
    original_analyze = engine._analyze_round_results_with_llm
    def traced_analyze(*args, **kwargs):
        trace_call('_analyze_round_results_with_llm', *args, **kwargs)
        return original_analyze(*args, **kwargs)
    engine._analyze_round_results_with_llm = traced_analyze
    
    # Patch LLMFindingEvaluator methods
    if hasattr(engine, 'finding_evaluator'):
        original_evaluate = getattr(engine.finding_evaluator, 'evaluate_batch', None)
        if original_evaluate:
            def traced_evaluate(*args, **kwargs):
                trace_call('evaluate_batch', *args, **kwargs)
                return original_evaluate(*args, **kwargs)
            engine.finding_evaluator.evaluate_batch = traced_evaluate
    
    # Run investigation
    config = InvestigationConfig(max_searches=1, pages_per_search=1)
    result = engine.conduct_investigation("Test investigation", config)
    
    print("\n=== CALL TRACE RESULTS ===")
    for i, call in enumerate(call_trace):
        print(f"{i+1}. {call['method']} (args: {call['args_count']}, kwargs: {call['kwargs']})")
    
    # Analysis
    datapoint_calls = [c for c in call_trace if 'datapoint' in c['method'].lower()]
    analyze_calls = [c for c in call_trace if 'analyze' in c['method'].lower()]
    evaluate_calls = [c for c in call_trace if 'evaluate' in c['method'].lower()]
    add_node_calls = [c for c in call_trace if 'add_node' in c['method']]
    
    print(f"\nANALYSIS:")
    print(f"- DataPoint creation calls: {len(datapoint_calls)}")
    print(f"- Analysis method calls: {len(analyze_calls)}")
    print(f"- Evaluate calls: {len(evaluate_calls)}")
    print(f"- Add node calls: {len(add_node_calls)}")
    print(f"- Total findings: {len(result.accumulated_findings)}")
    print(f"- Total graph nodes: {len(engine.llm_coordinator.graph.nodes) if hasattr(engine, 'llm_coordinator') and hasattr(engine.llm_coordinator, 'graph') else 0}")
    
    with open("method_trace.json", "w") as f:
        json.dump(call_trace, f, indent=2)
    
    missing_datapoint_calls = len(datapoint_calls) == 0 and len(analyze_calls) > 0
    missing_evaluate_calls = len(evaluate_calls) == 0 and len(analyze_calls) > 0
    
    return {
        'missing_datapoint_calls': missing_datapoint_calls,
        'missing_evaluate_calls': missing_evaluate_calls,
        'total_calls': len(call_trace)
    }

if __name__ == "__main__":
    result = test_method_call_tracing()
    print(f"\nDIAGNOSTIC RESULT:")
    if result['missing_datapoint_calls']:
        print("EVIDENCE: DataPoint creation methods are NOT being called")
    else:
        print("EVIDENCE: DataPoint creation methods ARE being called")
    
    if result['missing_evaluate_calls']:
        print("EVIDENCE: LLM evaluate methods are NOT being called")
    else:
        print("EVIDENCE: LLM evaluate methods ARE being called")
    
    print(f"Total method calls traced: {result['total_calls']}")