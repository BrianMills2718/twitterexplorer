# investigation_bridge.py
"""
Investigation Bridge - Architectural Integration Layer

Bridges the gap between insight synthesis and emergent question detection by
connecting dual intelligence systems in the TwitterExplorer investigation architecture.

CRITICAL: This bridge fixes the broken feedback loop between:
- RealTimeInsightSynthesizer (creates insights)
- GraphAwareLLMCoordinator (detects emergent questions)
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from investigation_graph import InvestigationGraph
from investigation_context import InvestigationContext

# Import LLM call tracer
try:
    from .utils.llm_call_tracer import get_tracer
    TRACER_AVAILABLE = True
except ImportError:
    TRACER_AVAILABLE = False
    get_tracer = lambda: None


class InvestigationBridge(ABC):
    """Abstract bridge between insight synthesis and emergent question detection"""
    
    @abstractmethod
    def notify_insight_created(self, insight_node: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Called when insight synthesizer creates new insight"""
        pass
    
    @abstractmethod  
    def request_emergent_questions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Request emergent question detection from coordinator"""
        pass
        
    @abstractmethod
    def share_investigation_context(self, updated_context: InvestigationContext) -> bool:
        """Share updated context between systems"""
        pass


class ConcreteInvestigationBridge(InvestigationBridge):
    """Concrete bridge implementation connecting insight synthesis to emergent question detection"""
    
    def __init__(self, llm_coordinator, graph: InvestigationGraph, context: InvestigationContext, model_manager=None):
        """
        Initialize bridge between systems
        
        Args:
            llm_coordinator: GraphAwareLLMCoordinator with detect_emergent_questions method
            graph: InvestigationGraph for creating nodes and edges
            context: InvestigationContext shared between systems
        """
        self.coordinator = llm_coordinator
        self.graph = graph
        self.context = context
        self.logger = self._setup_logger()
        
        # Validate critical methods exist
        if not hasattr(self.coordinator, 'detect_emergent_questions'):
            raise RuntimeError("LLM coordinator missing detect_emergent_questions method")
        if not hasattr(self.graph, 'create_emergent_question_node'):
            raise RuntimeError("Graph missing create_emergent_question_node method")
            
        self.logger.info("ConcreteInvestigationBridge initialized - architectural integration active")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup bridge-specific logging"""
        # Create investigation ID from analytic question or use timestamp
        if self.context and hasattr(self.context, 'analytic_question'):
            # Use first few words of question as ID
            question_words = self.context.analytic_question.split()[:3]
            investigation_id = "_".join(word.lower() for word in question_words if word.isalnum())
        else:
            investigation_id = f"bridge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        logger = logging.getLogger(f"bridge.{investigation_id}")
        logger.setLevel(logging.INFO)
        return logger
    
    def notify_insight_created(self, insight_node: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """
        Bridge: Insight created -> Trigger emergent question detection
        
        CRITICAL: This is the missing integration that connects dual intelligence systems
        """
        # Track bridge activation with enhanced visibility
        tracer = get_tracer() if TRACER_AVAILABLE else None
        if tracer:
            tracer.log_trigger("insight_created", "investigation_bridge", "notify_insight_created")
        
        try:
            insight_title = insight_node.get('title', 'Untitled')
            print(f"BRIDGE ACTIVATION: Processing insight '{insight_title}'")
            self.logger.info(f"Bridge notification: Insight created - {insight_title}")
            
            # Only process the new insight, not all insights (prevents exponential growth)
            new_insight = None
            for node in self.graph.get_nodes_by_type("Insight"):
                if node.id == insight_node["id"]:
                    new_insight = node
                    break
            
            if not new_insight:
                print(f"BRIDGE WARNING: New insight not found in graph!")
                self.logger.warning("New insight not found in graph for emergent question detection")
                return []
            
            # CRITICAL: Call detect_emergent_questions with ONLY the new insight
            print(f"BRIDGE -> COORDINATOR: Calling detect_emergent_questions with 1 new insight")
            print(f"   This will trigger LLM call for emergent question detection")
            self.logger.info(f"Bridge calling detect_emergent_questions with 1 new insight")
            emergent_questions = self.coordinator.detect_emergent_questions([new_insight])
            
            if not emergent_questions:
                self.logger.info("No emergent questions generated from insights")
                return []
            
            # Create SPAWNS edges connecting insights to emergent questions
            spawns_edges = []
            for eq in emergent_questions:
                try:
                    # Get emergent question ID (should be created by detect_emergent_questions)
                    eq_id = getattr(eq, 'id', None) or str(hash(eq.text))
                    
                    # Get node objects for edge creation
                    insight_node_obj = self.graph.nodes.get(insight_node["id"])
                    eq_node_obj = None
                    
                    # Find the emergent question node (it should have been created by detect_emergent_questions)
                    for node_id, node in self.graph.nodes.items():
                        if (hasattr(node, 'node_type') and node.node_type == "EmergentQuestion" and 
                            hasattr(node, 'properties') and node.properties.get('text') == eq.text):
                            eq_node_obj = node
                            break
                    
                    if insight_node_obj and eq_node_obj:
                        edge = self.graph.create_edge(
                            source=insight_node_obj,
                            target=eq_node_obj,
                            edge_type="SPAWNS",
                            properties={
                                "emergence_reason": eq.emergence_reason if hasattr(eq, 'emergence_reason') else "insight_analysis",
                                "priority": getattr(eq, 'priority', 0.5),
                                "created_at": datetime.now().isoformat()
                            }
                        )
                        spawns_edges.append(edge.id if hasattr(edge, 'id') else str(hash(edge)))
                    
                except Exception as edge_error:
                    self.logger.error(f"Failed to create SPAWNS edge: {edge_error}")
                    # Continue processing other emergent questions
            
            self.logger.info(f"Bridge integration: Created {len(emergent_questions)} emergent questions, {len(spawns_edges)} SPAWNS edges")
            
            # Return serializable representation
            return [
                {
                    "id": getattr(eq, 'id', str(hash(eq.text))),
                    "text": eq.text,
                    "emergence_reason": getattr(eq, 'emergence_reason', "insight_analysis"),
                    "priority": getattr(eq, 'priority', 0.5)
                }
                for eq in emergent_questions
            ]
            
        except Exception as e:
            self.logger.error(f"Critical bridge failure in notify_insight_created: {e}")
            # FAIL FAST - architectural integration failures are critical
            raise RuntimeError(f"Critical architectural bridge failure: {e}") from e
    
    def request_emergent_questions(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Direct request for emergent question detection"""
        try:
            self.logger.info(f"Bridge direct request: Detecting emergent questions from {len(insights)} insights")
            emergent_questions = self.coordinator.detect_emergent_questions(insights)
            
            return [
                {
                    "text": eq.text,
                    "emergence_reason": getattr(eq, 'emergence_reason', "direct_request"),
                    "priority": getattr(eq, 'priority', 0.5)
                }
                for eq in emergent_questions
            ]
            
        except Exception as e:
            self.logger.error(f"Bridge failure in request_emergent_questions: {e}")
            raise e
    
    def share_investigation_context(self, updated_context: InvestigationContext) -> bool:
        """Synchronize context between systems"""
        try:
            self.context = updated_context
            
            # Update coordinator context if it has context attribute
            if hasattr(self.coordinator, 'context'):
                self.coordinator.context = updated_context
                
            # Update coordinator investigation goal if it has set_context method
            if hasattr(self.coordinator, 'set_context'):
                self.coordinator.set_context(updated_context)
                
            self.logger.info("Bridge context synchronization successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Context sharing failed: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of bridge integration for debugging"""
        try:
            return {
                "coordinator_available": self.coordinator is not None,
                "coordinator_type": type(self.coordinator).__name__,
                "detect_emergent_questions_available": hasattr(self.coordinator, 'detect_emergent_questions'),
                "graph_available": self.graph is not None,
                "graph_node_count": len(self.graph.nodes) if hasattr(self.graph, 'nodes') else 0,
                "emergent_question_nodes": len(self.graph.get_nodes_by_type("EmergentQuestion")) if self.graph else 0,
                "insight_nodes": len(self.graph.get_nodes_by_type("Insight")) if self.graph else 0,
                "context_available": self.context is not None,
                "integration_healthy": True
            }
        except Exception as e:
            return {
                "integration_healthy": False,
                "error": str(e)
            }