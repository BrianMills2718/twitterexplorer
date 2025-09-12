# call_summary_logger.py - Periodic LLM call summaries during investigations
from .llm_call_tracer import get_tracer
import time
from datetime import datetime
from collections import defaultdict

class CallSummaryLogger:
    """Provides periodic summaries of LLM calls during long-running investigations"""
    
    def __init__(self, interval_seconds=60):
        self.interval_seconds = interval_seconds
        self.last_summary_time = time.time()
        self.last_call_count = 0
        
    def maybe_print_summary(self, force=False):
        """Print summary if interval elapsed or forced"""
        current_time = time.time()
        
        if force or (current_time - self.last_summary_time) >= self.interval_seconds:
            self._print_current_summary()
            self.last_summary_time = current_time
    
    def _print_current_summary(self):
        """Print current LLM call summary"""
        tracer = get_tracer()
        if not tracer:
            return
            
        summary = tracer.get_call_summary()
        current_calls = summary.get('total_calls', 0)
        
        if current_calls == 0:
            return
            
        new_calls = current_calls - self.last_call_count
        
        print("="*70)
        print(f"LLM CALL SUMMARY - {datetime.now().strftime('%H:%M:%S')}")
        print(f"   Total calls this session: {current_calls}")
        print(f"   New calls since last summary: {new_calls}")
        print(f"   Session duration: {summary.get('session_duration_s', 0):.1f}s")
        print(f"   Calls per minute: {summary.get('calls_per_minute', 0):.1f}")
        
        # Component breakdown
        components = summary.get('components', {})
        if components:
            print("   Calls by component:")
            for component, count in sorted(components.items(), key=lambda x: x[1], reverse=True):
                print(f"      • {component}: {count}")
        
        # Purpose breakdown  
        purposes = summary.get('purposes', {})
        if purposes:
            print("   Calls by purpose:")
            for purpose, count in sorted(purposes.items(), key=lambda x: x[1], reverse=True):
                print(f"      • {purpose}: {count}")
                
        print("="*70)
        
        self.last_call_count = current_calls
    
    def print_final_summary(self):
        """Print final summary at investigation end"""
        print("\n" + "="*70)
        print("FINAL LLM CALL SUMMARY")
        self._print_current_summary()
        
        # Analysis
        tracer = get_tracer()
        if tracer and tracer.calls:
            analysis = tracer.analyze_patterns()
            optimization = analysis.get('optimization_potential', {})
            
            print("OPTIMIZATION ANALYSIS:")
            print(f"   Potential savings: {optimization.get('potential_savings', 0):.1f} calls")
            
            targets = optimization.get('optimization_targets', [])
            if targets:
                print("   Top optimization targets:")
                for target in targets[:3]:
                    print(f"      • {target.get('component', 'Unknown')}: {target.get('recommendation', 'N/A')}")
        
        print("="*70 + "\n")


# Global instance for easy access
_global_summary_logger = None

def get_summary_logger():
    """Get global summary logger instance"""
    global _global_summary_logger
    if _global_summary_logger is None:
        _global_summary_logger = CallSummaryLogger()
    return _global_summary_logger