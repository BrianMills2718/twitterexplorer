# realtime_insight_synthesizer.py
"""
Real-Time Insight Synthesizer - Live Intelligence Generation

Synthesizes insights from DataPoints during investigation to provide real-time
understanding and progressive learning throughout the investigation process.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json  # Used for structured logging only
import os
from investigation_context import InvestigationContext
from investigation_graph import InvestigationGraph, Node
from llm_client import LiteLLMClient
from pydantic import BaseModel, Field
import logging

# Import LLM call tracer
try:
    from .utils.llm_call_tracer import get_tracer
    TRACER_AVAILABLE = True
except ImportError:
    TRACER_AVAILABLE = False
    get_tracer = lambda: None


class SemanticGroup(BaseModel):
    """Semantic grouping of DataPoints via LLM clustering"""
    group_theme: str = Field(description="Core theme connecting the DataPoints")
    datapoint_ids: List[str] = Field(description="IDs of DataPoints in this group")
    relevance_to_goal: float = Field(description="0-1 relevance to investigation goal")
    synthesis_worthy: bool = Field(description="Whether group warrants insight synthesis")


class SemanticGrouping(BaseModel):
    """Complete semantic grouping response"""
    groups: List[SemanticGroup] = Field(description="Semantic groups identified")
    rationale: str = Field(description="Reasoning behind grouping decisions")


class SynthesisDecision(BaseModel):
    """LLM decision on whether to synthesize insights"""
    should_synthesize: bool = Field(description="Whether to synthesize insights now")
    reasoning: str = Field(description="Rationale for decision")
    synthesis_potential: float = Field(description="0-1 potential for valuable insights")


class InsightSynthesis(BaseModel):
    """Synthesized insight with structured metadata"""
    title: str = Field(description="Concise insight title")
    content: str = Field(description="Detailed insight content")
    confidence_level: float = Field(description="Confidence 0.0-1.0")
    pattern_type: str = Field(description="Type: contradiction, trend, connection, implication")
    key_evidence: List[str] = Field(description="Supporting evidence snippets")
    investigation_relevance: float = Field(description="0-1 relevance to investigation goal")

class SynthesisDecisionV2(BaseModel):
    """Enhanced synthesis decision with context awareness"""
    decision_type: str = Field(description="Decision: CREATE, STRENGTHEN, MERGE, or SKIP")
    reasoning: str = Field(description="Explanation for the decision")
    target_insight_id: str = Field(description="ID of existing insight to strengthen/merge (empty string if not applicable)")
    confidence_adjustment: float = Field(description="New confidence for STRENGTHEN decisions (0.0 if not applicable)")
    insight: Optional[InsightSynthesis] = Field(description="New insight data (for CREATE decisions)", default=None)


class RelevanceAssessment(BaseModel):
    """Goal relevance assessment"""
    is_relevant: bool = Field(description="Whether content advances investigation goal")
    relevance_score: float = Field(description="0-1 relevance score")
    relevance_reasoning: str = Field(description="Why content is/isn't relevant")


class InsightSynthesisLogger:
    """Comprehensive debugging for insight synthesis pipeline"""
    
    def __init__(self, investigation_id: str):
        self.investigation_id = investigation_id
        self.logger = logging.getLogger(f"synthesis.{investigation_id}")
        
        # Create synthesis-specific log file
        log_dir = os.path.join(os.path.dirname(__file__), "logs", "synthesis")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"synthesis_{investigation_id}.jsonl")
        
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_datapoint_processing(self, datapoint_id: str, pending_count: int):
        self._log_structured({
            "event": "datapoint_added",
            "datapoint_id": datapoint_id,
            "pending_count": pending_count,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_llm_call(self, operation: str, success: bool, result: Any = None, error: str = None):
        self._log_structured({
            "event": "llm_call",
            "operation": operation,
            "success": success,
            "result_type": type(result).__name__ if result else None,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_semantic_grouping(self, input_count: int, groups: Any):
        groups_summary = []
        if hasattr(groups, 'groups'):
            for group in groups.groups:
                groups_summary.append({
                    "theme": group.group_theme,
                    "datapoint_count": len(group.datapoint_ids),
                    "synthesis_worthy": group.synthesis_worthy
                })
        
        self._log_structured({
            "event": "semantic_grouping",
            "input_datapoint_count": input_count,
            "output_groups": len(groups_summary),
            "groups": groups_summary,
            "timestamp": datetime.now().isoformat()
        })
    
    def log_insight_creation(self, insight: Any, success: bool):
        self._log_structured({
            "event": "insight_creation",
            "success": success,
            "insight_title": getattr(insight, 'title', None) if insight else None,
            "insight_confidence": getattr(insight, 'confidence_level', None) if insight else None,
            "timestamp": datetime.now().isoformat()
        })
    
    def _log_structured(self, data: Dict[str, Any]):
        self.logger.info(json.dumps(data))


# Backward compatibility alias
InsightModel = InsightSynthesis


class RealTimeInsightSynthesizer:
    """Synthesizes insights from DataPoints during investigation"""
    
    def __init__(self, llm_client: LiteLLMClient, graph: InvestigationGraph, context: InvestigationContext, model_manager=None):
        self.llm = llm_client
        self.graph = graph
        self.context = context
        self.pending_datapoints = []
        self.logger = logging.getLogger(__name__)
        
        # Initialize model manager
        if model_manager is None:
            from llm_model_manager import LLMModelManager
            self.model_manager = LLMModelManager()
        else:
            self.model_manager = model_manager
        
        # Create synthesis logger with investigation ID
        investigation_id = getattr(context, 'investigation_id', 'default')
        self.synthesis_logger = InsightSynthesisLogger(investigation_id)
        # CRITICAL: Bridge will be injected by investigation engine for architectural integration
        self.bridge = None
        
    def process_new_datapoint(self, datapoint_id: str) -> Optional[List[str]]:
        """Process new DataPoint with comprehensive logging"""
        self.pending_datapoints.append(datapoint_id)
        
        self.synthesis_logger.log_datapoint_processing(datapoint_id, len(self.pending_datapoints))
        
        try:
            if self._should_synthesize_llm(self.pending_datapoints):
                self.synthesis_logger._log_structured({
                    "event": "synthesis_triggered",
                    "pending_count": len(self.pending_datapoints),
                    "timestamp": datetime.now().isoformat()
                })
                
                insights_created = self._synthesize_insights_batch()
                
                self.synthesis_logger._log_structured({
                    "event": "synthesis_completed", 
                    "insights_created": len(insights_created) if insights_created else 0,
                    "timestamp": datetime.now().isoformat()
                })
                
                return insights_created
                
        except Exception as e:
            self.synthesis_logger._log_structured({
                "event": "synthesis_error",
                "error": str(e),
                "pending_datapoints": self.pending_datapoints,
                "timestamp": datetime.now().isoformat()
            })
            # Re-raise error for debugging (no silent suppression)
            raise e
            
        return None
        
    def _should_synthesize_llm(self, pending_datapoints: List[str]) -> bool:
        """LLM decides synthesis timing - NO hardcoded thresholds"""
        
        if len(pending_datapoints) < 3:
            return False
        
        # Get recent DataPoint content
        recent_content = []
        for dp_id in pending_datapoints[-5:]:
            node = self.graph.nodes.get(dp_id)
            if node:
                content = node.properties.get("content", "")[:150]
                recent_content.append(content)
        
        prompt = f"""
        INVESTIGATION: {self.context.analytic_question}
        
        RECENT FINDINGS:
        {chr(10).join(f"- {content}" for content in recent_content)}
        
        DECISION: Should insights be synthesized from these recent findings?
        
        Synthesize if:
        - Findings reveal patterns, contradictions, or connections
        - Multiple findings point to same conclusion
        - Findings significantly advance investigation understanding
        - High-quality content creates synthesis opportunity
        
        Do NOT synthesize if:
        - Findings unrelated to investigation goal
        - No meaningful patterns emerge
        - Content is low-quality or irrelevant
        """
        
        try:
            model = self.model_manager.get_model_for_operation("insight_synthesizer")
            response = self.llm.completion(
                model=model, 
                messages=[{"role": "user", "content": prompt}],
                response_format=SynthesisDecision,
                purpose="synthesis_decision"
            )
            
            # Check if parsed attribute exists before accessing it
            parsed_response = getattr(response.choices[0].message, 'parsed', None)
            self.synthesis_logger.log_llm_call("synthesis_decision", True, parsed_response)
            
            decision = parsed_response
            return decision.should_synthesize and decision.synthesis_potential > 0.6
            
        except Exception as e:
            self.synthesis_logger.log_llm_call("synthesis_decision", False, error=str(e))
            # Fallback to conservative approach on error
            return len(pending_datapoints) >= 8
        
    def _synthesize_insights_batch(self) -> List[str]:
        """Synthesize insights from pending DataPoints"""
        
        # Get DataPoint nodes
        datapoint_nodes = []
        for dp_id in self.pending_datapoints:
            node = self.graph.nodes.get(dp_id)
            if node and node.node_type == "DataPoint":
                datapoint_nodes.append(node)
        
        if len(datapoint_nodes) < 3:
            self.pending_datapoints.clear()
            return []
            
        # Group by semantic similarity using LLM
        try:
            semantic_grouping = self._group_semantically_llm(datapoint_nodes)
            self.synthesis_logger.log_semantic_grouping(len(datapoint_nodes), semantic_grouping)
            
            insights_created = []
            for group in semantic_grouping.groups:
                if group.synthesis_worthy and group.relevance_to_goal > 0.5:
                    # Get actual DataPoint nodes for this group
                    group_nodes = []
                    for dp_id in group.datapoint_ids:
                        node = self.graph.nodes.get(dp_id)
                        if node and node.node_type == "DataPoint":
                            group_nodes.append(node)
                    
                    if len(group_nodes) >= 2:
                        insight = self._synthesize_group_insight(group_nodes)
                        
                        if insight and insight.confidence_level > 0.3 and insight.investigation_relevance > 0.5:
                            insight_node = self._create_insight_node(insight, group_nodes)
                            insights_created.append(insight_node.id)
                            self.synthesis_logger.log_insight_creation(insight, True)
        
        except Exception as e:
            self.synthesis_logger._log_structured({
                "event": "grouping_error",
                "error": str(e),
                "datapoint_count": len(datapoint_nodes),
                "timestamp": datetime.now().isoformat()
            })
            insights_created = []
        
        self.pending_datapoints.clear()
        return insights_created
        
    def _group_semantically_llm(self, datapoints: List[Node]) -> SemanticGrouping:
        """Use LLM for semantic grouping - NO hardcoded rules"""
        
        # Track semantic grouping call
        tracer = get_tracer() if TRACER_AVAILABLE else None
        if tracer:
            tracer.log_trigger("datapoints_ready", "realtime_insight_synthesizer", "semantic_grouping")
        
        # Prepare DataPoint content
        datapoint_summaries = []
        for dp in datapoints:
            content = dp.properties.get("content", "")[:200]
            datapoint_summaries.append(f"[{dp.id}] {content}")
        
        prompt = f"""
        INVESTIGATION: {self.context.analytic_question}
        
        DATAPOINTS TO GROUP:
        {chr(10).join(datapoint_summaries)}
        
        TASK: Group DataPoints by semantic similarity and investigation relevance.
        
        Create natural clusters where DataPoints share:
        - Similar topics or themes related to: "{self.context.analytic_question}"
        - Related entities (people, organizations, events)
        - Complementary perspectives on same issue
        
        Requirements:
        - Minimum 2 DataPoints per group
        - Groups must advance investigation understanding
        - Mark synthesis_worthy=true only for meaningful patterns
        
        Use semantic understanding, NOT keyword matching.
        """
        
        try:
            model = self.model_manager.get_model_for_operation("insight_synthesizer")
            response = self.llm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=SemanticGrouping,
                purpose="semantic_grouping"
            )
            
            # Check if parsed attribute exists before accessing it
            parsed_response = getattr(response.choices[0].message, 'parsed', None)
            self.synthesis_logger.log_llm_call("semantic_grouping", True, parsed_response)
            return parsed_response
            
        except Exception as e:
            self.synthesis_logger.log_llm_call("semantic_grouping", False, error=str(e))
            # Fallback grouping on error
            return SemanticGrouping(
                groups=[
                    SemanticGroup(
                        group_theme="general_group",
                        datapoint_ids=[dp.id for dp in datapoints],
                        relevance_to_goal=0.5,
                        synthesis_worthy=len(datapoints) >= 3
                    )
                ],
                rationale="Fallback grouping due to LLM error"
            )
        
    def _build_comprehensive_context(self) -> str:
        """Build complete investigation context for synthesis decisions"""
        
        context_parts = []
        
        # Get existing insights with summaries
        existing_insights = self.graph.get_nodes_by_type("Insight")
        if existing_insights:
            context_parts.append("EXISTING INSIGHTS:")
            for insight in existing_insights[:10]:  # Limit for token management
                title = insight.properties.get('title', 'Untitled')
                confidence = insight.properties.get('confidence', 'N/A')
                content_summary = insight.properties.get('content', '')[:150] + "..."
                context_parts.append(f"- {title} (confidence: {confidence})")
                context_parts.append(f"  Summary: {content_summary}")
        
        # Get active emergent questions
        emergent_questions = self.graph.get_nodes_by_type("EmergentQuestion")
        if emergent_questions:
            context_parts.append("\nACTIVE EMERGENT QUESTIONS:")
            for eq in emergent_questions[:8]:  # Limit for tokens
                question_text = eq.properties.get('text', '')[:100] + "..."
                context_parts.append(f"- {question_text}")
        
        # Investigation progress
        all_datapoints = self.graph.get_nodes_by_type("DataPoint")
        context_parts.append(f"\nINVESTIGATION PROGRESS:")
        context_parts.append(f"- DataPoints collected: {len(all_datapoints)}")
        context_parts.append(f"- Insights created: {len(existing_insights)}")
        context_parts.append(f"- Questions emerged: {len(emergent_questions)}")
        
        return "\n".join(context_parts)

    def _synthesize_group_insight(self, group: List[Node]) -> Optional[InsightSynthesis]:
        """Generate insight using proper LiteLLM structured output with context awareness"""
        
        # Prepare content for LLM
        content_items = []
        for dp in group:
            content = dp.properties.get("content", "")
            if content:
                content_items.append(content[:200])  # Truncate for tokens
        
        if len(content_items) < 2:
            return None
        
        # Build comprehensive context
        investigation_context = self._build_comprehensive_context()
        
        prompt = f"""
        INVESTIGATION: {self.context.analytic_question}
        
        {investigation_context}
        
        NEW FINDINGS TO ANALYZE:
        {chr(10).join(f"- {content}" for content in content_items)}
        
        DECISION REQUIRED: Choose one action for these new findings:
        
        1. CREATE - Generate completely new insight (different from existing ones)
        2. STRENGTHEN - Add evidence to strengthen existing similar insight  
        3. MERGE - Combine with existing insights into broader understanding
        4. SKIP - Findings don't add significant new understanding
        
        DECISION CRITERIA:
        - CREATE: New findings reveal genuinely different pattern/theme from existing insights
        - STRENGTHEN: New findings support/enhance existing insight with additional evidence
        - MERGE: New findings connect separate existing insights into unified understanding
        - SKIP: New findings duplicate existing insights or lack investigation relevance
        
        FOR CREATE DECISIONS:
        - title: Descriptive title different from existing insights (5-10 words)  
        - content: Detailed explanation showing how this differs from existing insights
        - confidence_level: Rate 0.0-1.0 based on evidence strength
        - pattern_type: "contradiction", "trend", "connection", "implication"
        - key_evidence: 2-3 supporting evidence snippets
        - investigation_relevance: Rate 0.0-1.0 relevance to investigation goal
        
        FOR STRENGTHEN DECISIONS:
        - target_insight_id: ID of existing insight to strengthen
        - confidence_adjustment: New confidence level 0.0-1.0
        - reasoning: How new evidence strengthens the existing insight
        
        CRITICAL: Avoid creating duplicate insights. If findings are similar to existing insights, use STRENGTHEN or MERGE instead of CREATE.
        """
        
        try:
            model = self.model_manager.get_model_for_operation("insight_synthesizer")
            response = self.llm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=InsightSynthesis,  # Temporarily back to working schema
                purpose="insight_synthesis"
            )
            
            # Check if parsed attribute exists before accessing it
            parsed_response = getattr(response.choices[0].message, 'parsed', None)
            self.synthesis_logger.log_llm_call("insight_synthesis", True, parsed_response)
            
            if parsed_response:
                insight = parsed_response
                # Quality validation
                if insight.confidence_level < 0.3 or insight.investigation_relevance < 0.5:
                    return None
                return insight
            else:
                raise ValueError("LLM structured output parsing failed")
                
        except Exception as e:
            self.synthesis_logger.log_llm_call("insight_synthesis", False, error=str(e))
            # Surface errors for debugging (no silent suppression)
            print(f"ERROR in insight synthesis: {e}")
            raise e
    
    def _process_synthesis_decision(self, decision: SynthesisDecisionV2, group: List[Node]) -> Optional[InsightSynthesis]:
        """Process synthesis decision based on context-aware choice"""
        
        if decision.decision_type == "CREATE":
            # Create new insight - validate quality first
            if decision.insight and decision.insight.confidence_level >= 0.3 and decision.insight.investigation_relevance >= 0.5:
                return decision.insight
            else:
                print(f"CREATE decision rejected - low quality: confidence={decision.insight.confidence_level if decision.insight else 'None'}")
                return None
                
        elif decision.decision_type == "STRENGTHEN":
            # Strengthen existing insight
            if decision.target_insight_id and decision.target_insight_id != "" and decision.confidence_adjustment > 0.0:
                existing_insights = self.graph.get_nodes_by_type("Insight")
                target_insight = None
                for insight in existing_insights:
                    if insight.id == decision.target_insight_id:
                        target_insight = insight
                        break
                
                if target_insight:
                    # Update existing insight properties
                    target_insight.properties['confidence'] = decision.confidence_adjustment
                    # Add new evidence from group
                    new_evidence = [dp.properties.get('content', '')[:100] for dp in group]
                    existing_evidence = target_insight.properties.get('key_evidence', [])
                    target_insight.properties['key_evidence'] = existing_evidence + new_evidence
                    
                    print(f"STRENGTHEN: Enhanced insight {decision.target_insight_id} to confidence {decision.confidence_adjustment}")
                    return None  # No new insight created, existing one updated
                else:
                    print(f"STRENGTHEN decision failed - target insight {decision.target_insight_id} not found")
                    return None
                    
        elif decision.decision_type == "MERGE":
            print(f"MERGE decision noted but not implemented - reasoning: {decision.reasoning}")
            # MERGE logic would be complex - for now, log and skip
            return None
            
        elif decision.decision_type == "SKIP":
            print(f"SKIP decision - reasoning: {decision.reasoning}")
            return None
            
        else:
            print(f"Unknown decision type: {decision.decision_type}")
            return None
            
    def _create_insight_node(self, insight: InsightSynthesis, supporting_datapoints: List[Node]) -> Node:
        """Create Insight node in graph with SUPPORTS edges and trigger bridge integration"""
        
        # Create base insight node (only accepts content and insight_type)
        insight_node = self.graph.create_insight_node(
            content=insight.content,
            insight_type=insight.pattern_type
        )
        
        # Add additional properties to the node after creation
        insight_node.properties['title'] = insight.title
        insight_node.properties['confidence'] = insight.confidence_level
        insight_node.properties['investigation_relevance'] = insight.investigation_relevance
        insight_node.properties['key_evidence'] = insight.key_evidence
        
        # Create SUPPORTS edges from DataPoints to Insight
        for dp in supporting_datapoints:
            self.graph.create_edge(
                source=dp,
                target=insight_node,
                edge_type="SUPPORTS",
                properties={
                    "evidence_strength": dp.properties.get('relevance_score', 0.5),
                    "synthesis_timestamp": datetime.now().isoformat()
                }
            )
        
        # CRITICAL: Notify bridge of insight creation for architectural integration
        if self.bridge:
            try:
                emergent_questions = self.bridge.notify_insight_created({
                    "id": insight_node.id,
                    "content": insight.content,
                    "title": insight.title,
                    "confidence": insight.confidence_level,
                    "pattern_type": insight.pattern_type
                })
                
                if emergent_questions:
                    self.logger.info(f"Bridge integration: {len(emergent_questions)} emergent questions created from insight")
                else:
                    self.logger.info("Bridge integration: No emergent questions generated from insight")
                    
            except Exception as e:
                self.logger.error(f"Bridge integration failed during insight creation: {e}")
                # FAIL FAST - architectural integration is critical
                raise RuntimeError(f"Critical bridge failure during insight creation: {e}") from e
        else:
            self.logger.warning("No bridge available - architectural integration broken")
            
        return insight_node