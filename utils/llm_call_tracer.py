# llm_call_tracer.py - Comprehensive LLM call tracking and analysis
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import time
import threading
from collections import defaultdict, Counter


@dataclass
class LLMCall:
    """Represents a single LLM API call with full context"""
    timestamp: datetime
    component: str
    purpose: str
    data_size: int
    model: str
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    sequence_id: int = 0
    parent_call_id: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'purpose': self.purpose,
            'data_size': self.data_size,
            'model': self.model,
            'duration_ms': self.duration_ms,
            'success': self.success,
            'error': self.error,
            'sequence_id': self.sequence_id,
            'parent_call_id': self.parent_call_id,
            'metadata': self.metadata
        }


@dataclass
class CallPattern:
    """Analysis of LLM call patterns"""
    component: str
    total_calls: int
    avg_data_size: float
    total_duration_ms: float
    success_rate: float
    purposes: List[str]
    triggers: List[str]
    cascade_count: int = 0  # How many calls this component triggers in others
    redundancy_score: float = 0.0  # Estimated redundancy (0-1)


@dataclass 
class TriggerAnalysis:
    """Analysis of what triggers each LLM call"""
    trigger_event: str
    component: str
    purpose: str
    frequency: int
    cascade_effects: List[str]  # What other calls this triggers
    timing_pattern: str  # immediate, delayed, batched


class LLMCallTracer:
    """Comprehensive LLM call tracking and analysis system"""
    
    def __init__(self):
        self.calls: List[LLMCall] = []
        self.component_counts: Dict[str, int] = defaultdict(int)
        self.purpose_counts: Dict[str, int] = defaultdict(int)
        self.sequence_counter: int = 0
        self.call_stack: List[int] = []  # Track nested calls
        self.lock = threading.Lock()  # Thread-safe operations
        self.session_start: datetime = datetime.now()
        self.trigger_map: Dict[str, List[str]] = defaultdict(list)  # event -> components triggered
        
    def start_call(self, component: str, purpose: str, data_size: int = 0, model: str = "unknown") -> int:
        """Start tracking an LLM call - returns call_id"""
        with self.lock:
            call_id = len(self.calls)
            parent_id = self.call_stack[-1] if self.call_stack else None
            
            call = LLMCall(
                timestamp=datetime.now(),
                component=component,
                purpose=purpose,
                data_size=data_size,
                model=model,
                sequence_id=self.sequence_counter,
                parent_call_id=parent_id
            )
            
            self.calls.append(call)
            self.call_stack.append(call_id)
            self.component_counts[component] += 1
            self.purpose_counts[purpose] += 1
            self.sequence_counter += 1
            
            return call_id
    
    def end_call(self, call_id: int, success: bool = True, error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """End tracking an LLM call"""
        with self.lock:
            if call_id < len(self.calls):
                call = self.calls[call_id]
                call.duration_ms = (datetime.now() - call.timestamp).total_seconds() * 1000
                call.success = success
                call.error = error
                if metadata:
                    call.metadata.update(metadata)
                
                # Remove from call stack
                if self.call_stack and self.call_stack[-1] == call_id:
                    self.call_stack.pop()
    
    def log_call(self, component: str, purpose: str, data_size: int, model: str, 
                 duration_ms: float = 0.0, success: bool = True, error: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Log a completed LLM call with full context"""
        with self.lock:
            parent_id = self.call_stack[-1] if self.call_stack else None
            
            call = LLMCall(
                timestamp=datetime.now(),
                component=component,
                purpose=purpose,
                data_size=data_size,
                model=model,
                duration_ms=duration_ms,
                success=success,
                error=error,
                sequence_id=self.sequence_counter,
                parent_call_id=parent_id,
                metadata=metadata or {}
            )
            
            self.calls.append(call)
            self.component_counts[component] += 1
            self.purpose_counts[purpose] += 1
            self.sequence_counter += 1
    
    def log_trigger(self, trigger_event: str, component: str, purpose: str):
        """Log what triggers each LLM call"""
        trigger_key = f"{trigger_event}->{component}:{purpose}"
        self.trigger_map[trigger_event].append(component)
    
    def get_call_summary(self) -> Dict[str, Any]:
        """Get summary of all calls"""
        if not self.calls:
            return {"total_calls": 0, "components": {}, "purposes": {}}
        
        total_duration = sum(call.duration_ms for call in self.calls)
        successful_calls = sum(1 for call in self.calls if call.success)
        
        return {
            "total_calls": len(self.calls),
            "total_duration_ms": total_duration,
            "success_rate": successful_calls / len(self.calls) if self.calls else 0,
            "components": dict(self.component_counts),
            "purposes": dict(self.purpose_counts),
            "session_duration_s": (datetime.now() - self.session_start).total_seconds(),
            "calls_per_minute": len(self.calls) / max(1, (datetime.now() - self.session_start).total_seconds() / 60)
        }
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze call patterns and identify optimization opportunities"""
        # Always analyze trigger patterns, even without calls
        component_analysis = {}
        
        if self.calls:
            # Group calls by component
            component_calls = defaultdict(list)
            
            for call in self.calls:
                component_calls[call.component].append(call)
            
            # Analyze each component
            for component, calls in component_calls.items():
                total_duration = sum(call.duration_ms for call in calls)
                successful_calls = sum(1 for call in calls if call.success)
                purposes = list(set(call.purpose for call in calls))
                avg_data_size = sum(call.data_size for call in calls) / len(calls) if calls else 0
                
                # Find triggers for this component
                component_triggers = []
                for trigger_event, components in self.trigger_map.items():
                    if component in components:
                        component_triggers.append(trigger_event)
                
                component_analysis[component] = CallPattern(
                    component=component,
                    total_calls=len(calls),
                    avg_data_size=avg_data_size,
                    total_duration_ms=total_duration,
                    success_rate=successful_calls / len(calls),
                    purposes=purposes,
                    triggers=component_triggers
                )
        
        # Detect cascade patterns
        cascade_analysis = self._analyze_cascades()
        
        # Detect redundancy patterns  
        redundancy_analysis = self._analyze_redundancy()
        
        # Calculate optimization potential
        optimization_potential = self._calculate_optimization_potential()
        
        return {
            "component_patterns": {comp: pattern.__dict__ for comp, pattern in component_analysis.items()},
            "cascade_analysis": cascade_analysis,
            "redundancy_analysis": redundancy_analysis,
            "optimization_potential": optimization_potential,
            "trigger_patterns": dict(self.trigger_map),
            "call_timeline": [call.to_dict() for call in self.calls[-20:]]  # Last 20 calls for timeline
        }
    
    def _analyze_cascades(self) -> Dict[str, Any]:
        """Analyze cascade effects between components"""
        cascades = defaultdict(list)
        
        for call in self.calls:
            if call.parent_call_id is not None and call.parent_call_id < len(self.calls):
                parent = self.calls[call.parent_call_id]
                cascade_key = f"{parent.component}->{call.component}"
                cascades[cascade_key].append({
                    'parent_purpose': parent.purpose,
                    'child_purpose': call.purpose,
                    'timing_ms': (call.timestamp - parent.timestamp).total_seconds() * 1000
                })
        
        return dict(cascades)
    
    def _analyze_redundancy(self) -> Dict[str, float]:
        """Analyze redundancy in calls - same purpose/data repeated"""
        redundancy_scores = {}
        
        # Group by purpose and analyze for redundancy
        purpose_groups = defaultdict(list)
        for call in self.calls:
            purpose_groups[call.purpose].append(call)
        
        for purpose, calls in purpose_groups.items():
            if len(calls) <= 1:
                redundancy_scores[purpose] = 0.0
                continue
                
            # Simple redundancy heuristic: similar data sizes and rapid succession
            rapid_succession = 0
            for i in range(1, len(calls)):
                time_diff = (calls[i].timestamp - calls[i-1].timestamp).total_seconds()
                if time_diff < 10:  # Within 10 seconds
                    rapid_succession += 1
            
            redundancy_scores[purpose] = rapid_succession / len(calls)
        
        return redundancy_scores
    
    def _calculate_optimization_potential(self) -> Dict[str, Any]:
        """Calculate potential optimization savings"""
        total_calls = len(self.calls)
        if total_calls == 0:
            return {"potential_savings": 0, "optimization_targets": []}
        
        # Identify high-frequency, potentially batchable operations
        batchable_purposes = []
        for purpose, count in self.purpose_counts.items():
            if count > total_calls * 0.2:  # More than 20% of calls
                batchable_purposes.append({
                    'purpose': purpose,
                    'count': count,
                    'potential_reduction': count * 0.7  # Assume 70% could be batched
                })
        
        # Calculate cascade reduction potential
        cascade_calls = sum(1 for call in self.calls if call.parent_call_id is not None)
        cascade_reduction_potential = cascade_calls * 0.5  # Assume 50% could be optimized
        
        total_optimization_potential = sum(bp['potential_reduction'] for bp in batchable_purposes) + cascade_reduction_potential
        
        return {
            "potential_savings": min(total_optimization_potential, total_calls * 0.8),  # Max 80% reduction
            "batchable_operations": batchable_purposes,
            "cascade_reduction_potential": cascade_reduction_potential,
            "optimization_targets": self._get_optimization_targets()
        }
    
    def _get_optimization_targets(self) -> List[Dict[str, Any]]:
        """Get specific optimization targets"""
        targets = []
        
        # High frequency components
        for component, count in self.component_counts.items():
            if count > len(self.calls) * 0.15:  # More than 15% of calls
                targets.append({
                    'type': 'high_frequency',
                    'component': component,
                    'count': count,
                    'recommendation': 'Consider batching or caching'
                })
        
        # Components with high cascade potential
        cascade_components = set()
        for call in self.calls:
            if call.parent_call_id is not None:
                cascade_components.add(call.component)
        
        for component in cascade_components:
            if self.component_counts[component] > 5:
                targets.append({
                    'type': 'cascade_heavy',
                    'component': component,
                    'count': self.component_counts[component],
                    'recommendation': 'Optimize call chaining'
                })
        
        return targets
    
    def export_data(self, format: str = 'json') -> str:
        """Export call data for analysis"""
        data = {
            'summary': self.get_call_summary(),
            'analysis': self.analyze_patterns(),
            'raw_calls': [call.to_dict() for call in self.calls]
        }
        
        if format.lower() == 'json':
            return json.dumps(data, indent=2)
        else:
            # Could add CSV, other formats
            return str(data)
    
    def reset(self):
        """Reset the tracer for a new session"""
        with self.lock:
            self.calls.clear()
            self.component_counts.clear()
            self.purpose_counts.clear()
            self.sequence_counter = 0
            self.call_stack.clear()
            self.session_start = datetime.now()
            self.trigger_map.clear()


# Global tracer instance
_global_tracer: Optional[LLMCallTracer] = None


def get_tracer() -> LLMCallTracer:
    """Get the global LLM call tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = LLMCallTracer()
    return _global_tracer


def trace_llm_call(component: str, purpose: str, data_size: int = 0, model: str = "unknown"):
    """Decorator for tracing LLM calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            call_id = tracer.start_call(component, purpose, data_size, model)
            
            try:
                result = func(*args, **kwargs)
                tracer.end_call(call_id, success=True, metadata={'result_size': len(str(result))})
                return result
            except Exception as e:
                tracer.end_call(call_id, success=False, error=str(e))
                raise
        
        return wrapper
    return decorator