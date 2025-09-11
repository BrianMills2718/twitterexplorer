# investigation_engine.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import time
import math

# Lazy import of streamlit for complete CLI isolation
# Streamlit will only be imported when actually needed by UI functions
st = None
STREAMLIT_AVAILABLE = None  # Will be determined on first access

# Streamlit helper functions with lazy import for complete CLI isolation
def safe_streamlit(func_name, *args, **kwargs):
    """Safely call streamlit functions only when available - lazy import on first use"""
    global st, STREAMLIT_AVAILABLE
    
    # Check if CLI mode is explicitly disabled
    import os
    if os.environ.get('DISABLE_STREAMLIT', '').lower() in ('1', 'true', 'yes'):
        return None
    
    # Lazy import - only import when actually needed
    if STREAMLIT_AVAILABLE is None:
        try:
            import streamlit as st_module
            st = st_module
            STREAMLIT_AVAILABLE = True
        except ImportError:
            st = None
            STREAMLIT_AVAILABLE = False
    
    if STREAMLIT_AVAILABLE and st is not None:
        func = getattr(st, func_name, None)
        if func:
            return func(*args, **kwargs)
    return None

# Create streamlit-compatible no-op objects for CLI mode
class MockContainer:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

def get_streamlit_container():
    """Get streamlit container or no-op equivalent - lazy import"""
    global st, STREAMLIT_AVAILABLE
    
    # Check if CLI mode is explicitly disabled
    import os
    if os.environ.get('DISABLE_STREAMLIT', '').lower() in ('1', 'true', 'yes'):
        return MockContainer()
    
    # Lazy import - only import when actually needed
    if STREAMLIT_AVAILABLE is None:
        try:
            import streamlit as st_module
            st = st_module
            STREAMLIT_AVAILABLE = True
        except ImportError:
            st = None
            STREAMLIT_AVAILABLE = False
    
    if STREAMLIT_AVAILABLE and st is not None:
        return st.container()
    return MockContainer()

def get_streamlit_empty():
    """Get streamlit empty or no-op equivalent - lazy import"""
    global st, STREAMLIT_AVAILABLE
    
    # Check if CLI mode is explicitly disabled  
    import os
    if os.environ.get('DISABLE_STREAMLIT', '').lower() in ('1', 'true', 'yes'):
        return MockContainer()
    
    # Lazy import - only import when actually needed  
    if STREAMLIT_AVAILABLE is None:
        try:
            import streamlit as st_module
            st = st_module
            STREAMLIT_AVAILABLE = True
        except ImportError:
            st = None
            STREAMLIT_AVAILABLE = False
    
    if STREAMLIT_AVAILABLE and st is not None:
        return st.empty()
    return MockContainer()

# Import existing modules
import llm_handler
import api_client
import graph_manager
from logging_system import investigation_logger
from finding_evaluator_llm import LLMFindingEvaluator
from graph_visualizer import InvestigationGraphVisualizer
from cross_reference_analyzer import CrossReferenceAnalyzer
from temporal_timeline_analyzer import TemporalTimelineAnalyzer
from rejection_feedback import RejectionFeedback, analyze_rejections
from investigation_context import InvestigationContext
from realtime_insight_synthesizer import RealTimeInsightSynthesizer

# Import bridge for architectural integration (will only be used in graph mode)
try:
    from investigation_bridge import ConcreteInvestigationBridge
    BRIDGE_AVAILABLE = True
except ImportError:
    ConcreteInvestigationBridge = None
    BRIDGE_AVAILABLE = False

@dataclass
class InvestigationConfig:
    """Configuration for investigation behavior"""
    # Search limits
    max_searches: int = 100
    max_time_minutes: int = 60
    
    # Satisfaction controls  
    satisfaction_enabled: bool = True
    satisfaction_threshold: float = 0.8
    min_searches_before_satisfaction: int = 10
    
    # Transparency settings
    show_search_details: bool = True
    show_strategy_reasoning: bool = True
    show_effectiveness_scores: bool = True
    
    # Adaptive behavior
    enable_strategy_adaptation: bool = True
    enable_alternative_approaches: bool = True
    enable_name_variation_search: bool = True
    
    # Model configuration
    model_provider: str = 'openai'  # Options: 'openai', 'gemini'
    
    # Search behavior
    pages_per_search: int = 3
    search_timeout_seconds: int = 30
    retry_failed_searches: bool = True
    
    # Endpoint diversity enforcement
    enforce_endpoint_diversity: bool = False
    max_endpoint_repeats: int = 5
    diversity_threshold: float = 0.3

@dataclass
class SearchAttempt:
    """Record of a single search attempt"""
    search_id: int
    round_number: int
    endpoint: str
    params: Dict[str, Any]
    query_description: str
    results_count: int
    effectiveness_score: float
    execution_time: float
    error: Optional[str] = None
    key_findings: List[str] = field(default_factory=list)
    node_id: Optional[str] = None  # Graph node ID for this search

@dataclass
class Finding:
    """A piece of information discovered during investigation"""
    content: str
    source: str
    credibility_score: float
    category: str
    search_id: int
    evidence_strength: str
    
@dataclass
class SatisfactionMetrics:
    """Multi-dimensional satisfaction scoring"""
    information_coverage: float = 0.0  # 0-1: How much of topic covered
    source_diversity: float = 0.0      # 0-1: Variety of perspectives found
    evidence_quality: float = 0.0      # 0-1: Credibility of sources
    claim_specificity: float = 0.0     # 0-1: Specific vs general findings
    contradiction_resolution: float = 0.0  # 0-1: Conflicting info addressed
    
    def overall_satisfaction(self) -> float:
        weights = [0.25, 0.2, 0.25, 0.15, 0.15]
        scores = [self.information_coverage, self.source_diversity,
                 self.evidence_quality, self.claim_specificity,
                 self.contradiction_resolution]
        return sum(score * weight for score, weight in zip(scores, weights))

@dataclass
class InvestigationRound:
    """A complete round of searches with a unified strategy"""
    round_number: int
    strategy_description: str
    searches: List[SearchAttempt] = field(default_factory=list)
    total_results: int = 0
    round_effectiveness: float = 0.0
    key_insights: List[str] = field(default_factory=list)
    next_strategy_hints: List[str] = field(default_factory=list)

class InvestigationSession:
    """Manages the complete investigation state"""
    
    def __init__(self, original_query: str, config: InvestigationConfig):
        self.original_query = original_query
        self.config = config
        self.start_time = datetime.now()
        
        # Progress tracking
        self.search_count = 0
        self.round_count = 0
        self.total_results_found = 0
        
        # Investigation state
        self.rounds: List[InvestigationRound] = []
        self.accumulated_findings: List[Finding] = []
        self.search_history: List[SearchAttempt] = []
        self.knowledge_graph: Dict[str, Any] = {}
        self.root_node_id: Optional[str] = None  # Graph root node ID
        
        # Intelligence tracking
        self.dead_ends: List[str] = []  # failed approaches
        self.promising_leads: List[str] = []  # successful directions
        self.effective_search_patterns: Dict[str, float] = {}
        
        # Satisfaction tracking
        self.satisfaction_metrics = SatisfactionMetrics()
        self.satisfaction_history: List[float] = []
        
        # Cross-reference analysis (Task 1.1 - Advanced Features)
        self.cross_reference_analysis = None  # Will be populated during investigation
        
        # Rejection feedback tracking
        self.rejection_feedback_history: List[RejectionFeedback] = []  # Track rejections per round
        
        # Temporal timeline analysis (Task 1.2 - Advanced Features)
        self.temporal_timeline = None  # Will be populated during investigation
        
        # Investigation context for goal-aware processing
        self.context: Optional[InvestigationContext] = None
        
        # Real-time insight tracking
        self.insights_generated: List[Dict[str, Any]] = []
        
        # Status
        self.is_active = True
        self.completion_reason: Optional[str] = None
        
        # Final summary for user display
        self.final_summary = None  # Will be populated at investigation end
        
    def should_continue(self) -> Tuple[bool, str]:
        """Determine if investigation should continue"""
        
        # Check hard limits
        if self.search_count >= self.config.max_searches:
            return False, f"Reached maximum search limit ({self.config.max_searches})"
            
        elapsed_minutes = (datetime.now() - self.start_time).seconds / 60
        if elapsed_minutes >= self.config.max_time_minutes:
            return False, f"Reached time limit ({self.config.max_time_minutes} minutes)"
            
        # Check satisfaction if enabled
        if (self.config.satisfaction_enabled and 
            self.search_count >= self.config.min_searches_before_satisfaction):
            
            current_satisfaction = self.satisfaction_metrics.overall_satisfaction()
            if current_satisfaction >= self.config.satisfaction_threshold:
                return False, f"Investigation satisfied (score: {current_satisfaction:.2f})"
                
        return True, "Investigation continuing"
        
    def add_search_attempt(self, attempt: SearchAttempt):
        """Add a completed search attempt"""
        self.search_history.append(attempt)
        self.search_count += 1
        self.total_results_found += attempt.results_count
        
        # Add to current round
        if self.rounds:
            self.rounds[-1].searches.append(attempt)
            self.rounds[-1].total_results += attempt.results_count
            
    def start_new_round(self, strategy_description: str) -> InvestigationRound:
        """Start a new investigation round"""
        self.round_count += 1
        round_obj = InvestigationRound(
            round_number=self.round_count,
            strategy_description=strategy_description
        )
        self.rounds.append(round_obj)
        return round_obj
        
    def update_satisfaction_metrics(self, findings: List[Finding]):
        """Update satisfaction based on new findings"""
        if not findings:
            return
            
        # Update information coverage
        unique_topics = len(set(f.category for f in self.accumulated_findings))
        self.satisfaction_metrics.information_coverage = min(1.0, unique_topics / 5.0)
        
        # Update source diversity  
        unique_sources = len(set(f.source for f in self.accumulated_findings))
        self.satisfaction_metrics.source_diversity = min(1.0, unique_sources / 10.0)
        
        # Update evidence quality
        avg_credibility = sum(f.credibility_score for f in self.accumulated_findings) / len(self.accumulated_findings) if self.accumulated_findings else 0
        self.satisfaction_metrics.evidence_quality = avg_credibility
        
        # Update claim specificity
        specific_findings = [f for f in self.accumulated_findings if f.evidence_strength in ['high', 'very_high']]
        self.satisfaction_metrics.claim_specificity = min(1.0, len(specific_findings) / max(1, len(self.accumulated_findings)))
        
        # Track satisfaction history
        self.satisfaction_history.append(self.satisfaction_metrics.overall_satisfaction())

class InvestigationEngine:
    """Core engine for conducting iterative investigations"""
    
    @classmethod
    def from_config(cls, api_key: str = None, provider: str = None, 
                   config_file: str = None, model_overrides: Dict[str, str] = None):
        """Create investigation engine with specific configuration"""
        
        # Handle simple provider switching
        if provider and not config_file:
            # Generate temporary config for provider
            temp_config = cls._generate_provider_config(provider)
            engine = cls(api_key, model_config_path=temp_config)
        elif config_file:
            engine = cls(api_key, model_config_path=config_file)
        else:
            engine = cls(api_key)
        
        # Apply model overrides
        if model_overrides:
            for operation, model in model_overrides.items():
                engine.model_manager.config["models"][operation] = model
                print(f"Model override: {operation} = {model}")
        
        return engine
    
    @staticmethod
    def _generate_provider_config(provider: str) -> str:
        """Generate temporary config for provider switching"""
        if provider == "openai":
            models = {op: "gpt-5-mini" for op in [
                "strategic_coordinator", "finding_evaluator", "insight_synthesizer",
                "emergent_questions", "cross_reference", "temporal_analysis"
            ]}
        elif provider == "gemini":
            models = {op: "gemini/gemini-2.5-flash" for op in [
                "strategic_coordinator", "finding_evaluator", "insight_synthesizer", 
                "emergent_questions", "cross_reference", "temporal_analysis"
            ]}
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        models.update({
            "fallback_primary": "gpt-4o-mini",
            "fallback_secondary": "gpt-3.5-turbo"
        })
        
        config = {
            "default_provider": provider,
            "models": models
        }
        
        # Write to temporary file
        import tempfile
        import yaml
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config, temp_file, default_flow_style=False)
        temp_file.close()
        
        return temp_file.name
    
    def __init__(self, rapidapi_key: str, model_config_path: str = None):
        self.rapidapi_key = rapidapi_key
        self.progress_container = None  # For real-time UI updates
        self.logger = investigation_logger  # Fix for logger attribute error
        
        # Initialize model manager
        from llm_model_manager import LLMModelManager
        self.model_manager = LLMModelManager(config_path=model_config_path)
        
        # Try to initialize Graph-Aware LLM coordinator first (new architecture)
        try:
            from graph_aware_llm_coordinator import GraphAwareLLMCoordinator
            from llm_client import get_litellm_client
            from investigation_graph import InvestigationGraph
            
            # Create graph-based coordinator
            llm_client = get_litellm_client()
            investigation_graph = InvestigationGraph()
            self.llm_coordinator = GraphAwareLLMCoordinator(llm_client, investigation_graph, self.model_manager)
            self.graph = investigation_graph  # Store graph reference for bridge
            self.graph_mode = True
            
            # Initialize finding evaluator with the same LLM client
            self.finding_evaluator = LLMFindingEvaluator(llm_client, self.model_manager)
            
            # Initialize insight synthesizer (will be configured with context later)
            self.insight_synthesizer = None
            
            # CRITICAL: Initialize architectural integration bridge (will be configured with context later)
            self.integration_bridge = None
            
        except Exception as graph_error:
            # Fallback to new LLM coordinator with LiteLLM
            try:
                from llm_investigation_coordinator import LLMInvestigationCoordinator
                import litellm
                
                # Use centralized LLM client from secrets
                from llm_client import get_litellm_client
                llm_client = get_litellm_client()
                self.llm_coordinator = LLMInvestigationCoordinator(llm_client)
                self.graph_mode = False
                
                # Initialize finding evaluator with the same LLM client
                self.finding_evaluator = LLMFindingEvaluator(llm_client)
                
                # Initialize insight synthesizer (will be configured with context later)
                self.insight_synthesizer = None
                
            except Exception as fallback_error:
                raise RuntimeError(f"Both Graph-aware and original LLM coordinator initialization failed. Graph error: {graph_error}. Fallback error: {fallback_error}")
    
    def set_progress_container(self, container):
        """Set the Streamlit container for progress updates"""
        self.progress_container = container
    
    def send_progress_update(self, message: str, update_type: str = "info"):
        """Send a progress update to the UI"""
        if self.progress_container:
            if update_type == "info":
                self.progress_container.info(message)
            elif update_type == "success":
                self.progress_container.success(message)
            elif update_type == "warning":
                self.progress_container.warning(message)
            elif update_type == "error":
                self.progress_container.error(message)
            elif update_type == "markdown":
                self.progress_container.markdown(message)
    
    def send_satisfaction_update(self, satisfaction_level: float):
        """Send satisfaction metric update"""
        if self.progress_container:
            percentage = satisfaction_level * 100
            message = f"📊 **Current Satisfaction:** {percentage:.1f}%"
            if satisfaction_level < 0.3:
                message += " - 🔴 Low"
            elif satisfaction_level < 0.7:
                message += " - 🟡 Moderate"
            else:
                message += " - 🟢 High"
            self.progress_container.markdown(message)
        
    def conduct_investigation(self, query: str, config: InvestigationConfig = None) -> 'InvestigationSession':
        """Conduct a complete iterative investigation with context-aware processing"""
        
        if config is None:
            config = InvestigationConfig()
            
        session = InvestigationSession(query, config)
        
        # CREATE: Investigation context for goal-aware processing
        investigation_context = InvestigationContext(
            analytic_question=query,
            investigation_scope="twitter_investigation"
        )
        session.context = investigation_context
        
        # Pass context to LLM coordinator
        if hasattr(self.llm_coordinator, 'set_context'):
            self.llm_coordinator.set_context(investigation_context)
        
        # Create real-time insight synthesizer
        if self.graph_mode and hasattr(self.llm_coordinator, 'graph'):
            self.insight_synthesizer = RealTimeInsightSynthesizer(
                llm_client=self.llm_coordinator.llm,
                graph=self.llm_coordinator.graph,
                context=investigation_context,
                model_manager=self.model_manager
            )
            
            # CRITICAL: Create and wire architectural integration bridge
            if BRIDGE_AVAILABLE and ConcreteInvestigationBridge is not None:
                self.integration_bridge = ConcreteInvestigationBridge(
                    llm_coordinator=self.llm_coordinator,
                    graph=self.llm_coordinator.graph,
                    context=investigation_context,
                    model_manager=self.model_manager
                )
                
                # Wire bridge into insight synthesizer
                self.insight_synthesizer.bridge = self.integration_bridge
            else:
                self.integration_bridge = None
                self.logger.warning("Bridge not available - architectural integration disabled")
        
        # Create AnalyticQuestion root node if in graph mode
        if self.graph_mode and hasattr(self.llm_coordinator, 'graph'):
            root_node = self.llm_coordinator.graph.create_analytic_question_node(
                text=query,
                is_root=True,
                investigation_goal=query
            )
            session.root_node_id = root_node.id  # Track for connecting questions
        
        # Start logging session
        session_id = investigation_logger.start_session(query, config)
        session.session_id = session_id  # Store session ID on session object
        
        # Create containers for real-time updates only if in Streamlit context
        # Detect CLI mode by checking command line arguments or environment
        import sys
        is_cli_mode = ('cli_test.py' in sys.argv[0] or 
                      len(sys.argv) > 1 and not sys.argv[0].endswith('streamlit'))
        
        if self.progress_container and not is_cli_mode:
            # Already have a container (Streamlit mode)
            progress_container = self.progress_container
            details_container = get_streamlit_container()
        elif not is_cli_mode:
            # Only create containers if NOT in CLI mode
            progress_container = get_streamlit_container()
            details_container = get_streamlit_container()
        else:
            # CLI mode - no containers needed
            progress_container = None
            details_container = None
        
        # Send initial progress update
        self.send_progress_update(f"🚀 Starting investigation: {query}", "info")
        
        try:
            while session.should_continue()[0]:
                # Send strategy generation update
                self.send_progress_update("🧠 Generating next strategy...", "info")
                
                # Generate next strategy
                strategy = self._generate_strategy(session)
                current_round = session.start_new_round(strategy['description'])
                
                # Send strategy update
                self.send_progress_update(f"**Round {current_round.round_number}:** {strategy['description']}", "markdown")
                
                # Log strategy decision
                context = self._build_strategy_context(session)
                investigation_logger.log_strategy_decision(
                    round_number=current_round.round_number,
                    previous_context=context,
                    strategy_type=strategy.get('description', 'Unknown'),
                    reasoning=strategy.get('reasoning', ''),
                    searches_planned=strategy.get('searches', [])
                )
                
                # Display round header
                if progress_container:
                    with progress_container:
                        self._display_round_header(session, current_round, strategy)
                else:
                    self._display_round_header(session, current_round, strategy)
                
                # Execute searches for this round
                round_results = []
                for i, search_plan in enumerate(strategy['searches']):
                    search_id = session.search_count + 1
                    
                    # Send search execution update
                    self.send_progress_update(f"🔍 Executing search {i+1}/{len(strategy['searches'])}: {search_plan.get('query', 'Unknown query')}", "info")
                    
                    # Display search attempt
                    if details_container:
                        with details_container:
                            search_placeholder = get_streamlit_empty()
                            self._display_search_attempt(search_placeholder, search_plan, search_id)
                    else:
                        search_placeholder = get_streamlit_empty()
                        self._display_search_attempt(search_placeholder, search_plan, search_id)
                    
                    # Execute the search
                    attempt = self._execute_search(search_plan, search_id, current_round.round_number)
                    session.add_search_attempt(attempt)
                    round_results.append(attempt)
                    
                    # Send result update
                    if attempt.results_count > 0:
                        self.send_progress_update(f"✅ Found {attempt.results_count} results (effectiveness: {attempt.effectiveness_score}/10)", "success")
                    else:
                        self.send_progress_update(f"⚠️ No results found", "warning")
                    
                    # Log search attempt
                    investigation_logger.log_search_attempt(
                        attempt=attempt, 
                        strategy_type=strategy.get('description', 'Unknown'),
                        sample_results=None  # TODO: Add sample results extraction
                    )
                    
                    # Update display with results
                    if details_container:
                        with details_container:
                            self._display_search_results(search_placeholder, attempt)
                    else:
                        self._display_search_results(search_placeholder, attempt)
                    
                    # Break if we hit limits mid-round
                    if not session.should_continue()[0]:
                        break
                
                # Analyze round results with LLM evaluation
                try:
                    self._analyze_round_results_with_llm(session, current_round, round_results)
                except Exception as e:
                    # self.logger.warning(f"Error in round analysis: {e}")
                    print(f"Warning: Error in round analysis: {e}")
                    # Continue investigation despite error
                
                # Send batch evaluation update
                avg_effectiveness = sum(r.effectiveness_score for r in round_results) / len(round_results) if round_results else 0
                self.send_progress_update(f"📊 Round {current_round.round_number} average effectiveness: {avg_effectiveness:.1f}/10", "info")
                
                # Update and send satisfaction metrics
                session.update_satisfaction_metrics(session.accumulated_findings)
                satisfaction = session.satisfaction_metrics.overall_satisfaction()
                self.send_satisfaction_update(satisfaction)
                
                # Log round completion
                investigation_logger.log_round_completion(
                    round_number=current_round.round_number,
                    strategy_used=current_round.strategy_description,
                    searches_executed=len(round_results),
                    total_results=current_round.total_results,
                    round_effectiveness=current_round.round_effectiveness,
                    key_insights=current_round.key_insights,
                    next_strategy_hints=current_round.next_strategy_hints
                )
                
                # Display batch evaluation results and learning
                if details_container:
                    with details_container:
                        self._display_batch_evaluation(current_round, round_results)
                else:
                    self._display_batch_evaluation(current_round, round_results)
                
                # Update progress display
                if progress_container:
                    with progress_container:
                        self._display_investigation_progress(session)
                else:
                    self._display_investigation_progress(session)
                    
            # Investigation complete
            session.is_active = False
            session.completion_reason = session.should_continue()[1]
            
            # === NEW: Generate final summary from all insights ===
            self._generate_final_summary(session)
            
            # Send completion update
            final_satisfaction = session.satisfaction_metrics.overall_satisfaction()
            self.send_progress_update(f"✅ Investigation complete! Final satisfaction: {final_satisfaction:.1%}", "success")
            self.send_progress_update(f"📈 Total searches: {session.search_count}, Total results: {session.total_results_found}", "info")
            
            # Task 1.1: Perform cross-reference analysis on accumulated findings
            if session.accumulated_findings and len(session.accumulated_findings) >= 2:
                self.send_progress_update("🔍 Analyzing cross-references and patterns...", "info")
                try:
                    # Use the same LLM client for consistency
                    llm_client = None
                    if hasattr(self.llm_coordinator, 'llm'):
                        llm_client = self.llm_coordinator.llm
                    elif hasattr(self.llm_coordinator, 'llm_client'):
                        llm_client = self.llm_coordinator.llm_client
                        
                    analyzer = CrossReferenceAnalyzer(llm_client)
                    session.cross_reference_analysis = analyzer.analyze_findings(
                        session.accumulated_findings,
                        session.original_query
                    )
                    
                    # Report cross-reference results
                    analysis = session.cross_reference_analysis
                    if analysis:
                        self.send_progress_update(f"🔗 Found {len(analysis.patterns)} patterns, {len(analysis.contradictions)} contradictions", "info")
                        self.send_progress_update(f"📊 Cross-reference confidence: {analysis.confidence_score:.1%}", "info")
                    
                except Exception as e:
                    self.send_progress_update(f"⚠️ Cross-reference analysis failed: {e}", "warning")
                    # Continue without failing the entire investigation
            
            # Task 1.2: Perform temporal timeline analysis on accumulated findings
            if session.accumulated_findings and len(session.accumulated_findings) >= 1:
                self.send_progress_update("🕒 Analyzing temporal timeline...", "info")
                try:
                    # Use the same LLM client for consistency
                    llm_client = None
                    if hasattr(self.llm_coordinator, 'llm'):
                        llm_client = self.llm_coordinator.llm
                    elif hasattr(self.llm_coordinator, 'llm_client'):
                        llm_client = self.llm_coordinator.llm_client
                        
                    timeline_analyzer = TemporalTimelineAnalyzer(llm_client)
                    session.temporal_timeline = timeline_analyzer.analyze_timeline(
                        session.accumulated_findings,
                        session.original_query
                    )
                    
                    # Report temporal timeline results
                    timeline = session.temporal_timeline
                    if timeline and timeline.events:
                        self.send_progress_update(f"📅 Timeline: {len(timeline.events)} events spanning {timeline.start_date} to {timeline.end_date}", "info")
                        self.send_progress_update(f"⏱️ Timeline confidence: {timeline.confidence_score:.1%}, consistency: {timeline.consistency_score:.1%}", "info")
                    
                except Exception as e:
                    self.send_progress_update(f"⚠️ Temporal timeline analysis failed: {e}", "warning")
                    # Continue without failing the entire investigation
            
            # End logging session
            investigation_logger.end_session(session)
            
            # Automatically export graph after every investigation
            self._export_investigation_graph(session)
            
            return session
            
        except Exception as e:
            session.is_active = False
            session.completion_reason = f"Investigation failed: {str(e)}"
            
            # Still generate summary even on error
            self._generate_final_summary(session)
            
            # Task 1.1: Try to perform cross-reference analysis even on error if we have findings
            if session.accumulated_findings and len(session.accumulated_findings) >= 2:
                try:
                    llm_client = None
                    if hasattr(self.llm_coordinator, 'llm'):
                        llm_client = self.llm_coordinator.llm
                    elif hasattr(self.llm_coordinator, 'llm_client'):
                        llm_client = self.llm_coordinator.llm_client
                        
                    analyzer = CrossReferenceAnalyzer(llm_client)
                    session.cross_reference_analysis = analyzer.analyze_findings(
                        session.accumulated_findings,
                        session.original_query
                    )
                except Exception as analysis_error:
                    # Continue without cross-reference analysis
                    pass
            
            # Task 1.2: Try to perform temporal timeline analysis even on error if we have findings
            if session.accumulated_findings and len(session.accumulated_findings) >= 1:
                try:
                    llm_client = None
                    if hasattr(self.llm_coordinator, 'llm'):
                        llm_client = self.llm_coordinator.llm
                    elif hasattr(self.llm_coordinator, 'llm_client'):
                        llm_client = self.llm_coordinator.llm_client
                        
                    timeline_analyzer = TemporalTimelineAnalyzer(llm_client)
                    session.temporal_timeline = timeline_analyzer.analyze_timeline(
                        session.accumulated_findings,
                        session.original_query
                    )
                except Exception as timeline_error:
                    # Continue without temporal timeline analysis
                    pass
            
            # Log the error and end session
            investigation_logger.end_session(session)
            
            # Automatically export graph even on error (if graph was built)
            self._export_investigation_graph(session)
            
            safe_streamlit("error", f"Investigation error: {e}")
            return session
    
    def _export_investigation_graph(self, session: InvestigationSession):
        """Automatically export investigation graph as JSON and HTML after every investigation"""
        if not self.graph_mode or not hasattr(self.llm_coordinator, 'graph'):
            return  # Skip if not in graph mode
        
        try:
            graph = self.llm_coordinator.graph
            session_id = session.session_id if hasattr(session, 'session_id') else 'unknown'
            
            # 1. Export JSON
            json_filename = f"investigation_graph_{session_id}.json"
            graph_json = graph.to_json()
            with open(json_filename, 'w', encoding='utf-8') as f:
                f.write(graph_json)
            
            # 2. Export HTML Visualization
            visualizer = InvestigationGraphVisualizer()
            
            # Convert InvestigationGraph to GraphVisualizer format
            # Add nodes
            for node_id, node in graph.nodes.items():
                if node.node_type == "AnalyticQuestion":
                    visualizer.add_query_node(node.properties.get("text", "Investigation"), node.created_at.isoformat() if node.created_at else None)
                elif node.node_type == "InvestigationQuestion": 
                    # Use add_search_node for investigation questions (closest match)
                    search_params = {"query": node.properties.get("text", "Question"), "type": "investigation_question"}
                    visualizer.add_search_node(search_params, 0, node.created_at.isoformat() if node.created_at else None)
                elif node.node_type == "SearchQuery":
                    endpoint = node.properties.get("endpoint", "unknown")
                    params = node.properties.get("parameters", {})
                    search_params = {"endpoint": endpoint, **params}
                    visualizer.add_search_node(search_params, 0, node.created_at.isoformat() if node.created_at else None)
                elif node.node_type == "DataPoint":
                    content = node.properties.get("content", "Finding")
                    source = node.properties.get("source", "Twitter")
                    relevance = node.properties.get("relevance_score", 0.5)
                    visualizer.add_datapoint_node(content, source, relevance, node.created_at.isoformat() if node.created_at else None)
            
            # Add edges - create a node ID mapping first
            node_id_map = {}  # Map from InvestigationGraph node IDs to GraphVisualizer node IDs
            
            # Build the mapping
            visualizer_nodes = list(visualizer.nodes.keys())
            graph_nodes = list(graph.nodes.keys())
            
            # Create mapping based on order (since we added them in the same order)
            for i, graph_node_id in enumerate(graph_nodes):
                if i < len(visualizer_nodes):
                    node_id_map[graph_node_id] = visualizer_nodes[i]
            
            # Add edges using the mapping
            for edge in graph.edges:
                source_viz_id = node_id_map.get(edge.source_id)
                target_viz_id = node_id_map.get(edge.target_id) 
                
                if source_viz_id and target_viz_id:
                    visualizer.add_edge(source_viz_id, target_viz_id, edge.edge_type)
            
            # Save HTML
            html_filename = f"investigation_graph_{session_id}.html"  
            visualizer.save_visualization(html_filename)
            
            # Also save as current_investigation_graph.json for easy access
            with open("current_investigation_graph.json", 'w', encoding='utf-8') as f:
                f.write(graph_json)
            
            print(f"Graph exported: {json_filename} and {html_filename}")
            
        except Exception as e:
            print(f"Warning: Failed to export investigation graph: {e}")
            # Don't fail the entire investigation if graph export fails
    
    def _generate_final_summary(self, session: InvestigationSession):
        """Generate user-facing summary from all round insights"""
        
        # Collect all insights from all rounds
        all_insights = []
        for round_obj in session.rounds:
            if hasattr(round_obj, 'key_insights') and round_obj.key_insights:
                all_insights.extend(round_obj.key_insights)
        
        # Build summary
        summary_parts = [
            f"## Investigation Summary: {session.original_query}",
            f"",
            f"**Searches Conducted:** {session.search_count}",
            f"**Total Results Analyzed:** {session.total_results_found}",
            f"**Investigation Duration:** {session.rounds[-1].round_number if session.rounds else 0} rounds",
            f""
        ]
        
        if all_insights:
            summary_parts.append("### Key Findings:")
            for i, insight in enumerate(all_insights, 1):
                summary_parts.append(f"{i}. {insight}")
        else:
            summary_parts.append("### No specific insights extracted")
            summary_parts.append("The investigation found results but no significant patterns or announcements.")
        
        # Add effectiveness summary
        if session.rounds:
            avg_effectiveness = sum(r.round_effectiveness for r in session.rounds) / len(session.rounds)
            summary_parts.append(f"")
            summary_parts.append(f"**Average Search Effectiveness:** {avg_effectiveness:.1f}/10")
        
        # Add satisfaction level
        if hasattr(session, 'satisfaction_metrics'):
            satisfaction = session.satisfaction_metrics.overall_satisfaction()
            summary_parts.append(f"**Information Satisfaction:** {satisfaction:.0%}")
        
        session.final_summary = "\n".join(summary_parts)
        
        # Also send to progress container if available
        if self.progress_container:
            self.send_progress_update("=" * 60, "markdown")
            self.send_progress_update(session.final_summary, "markdown")
            self.send_progress_update("=" * 60, "markdown")
        
        return session.final_summary
            
    def _generate_strategy(self, session: InvestigationSession) -> Dict[str, Any]:
        """Generate next investigation strategy using LLM coordinator - FAIL FAST"""
        
        # Build rejection context from previous rounds
        rejection_context = ""
        if session.rejection_feedback_history:
            # Get the most recent rejection feedback
            recent_feedback = session.rejection_feedback_history[-1]
            rejection_context = recent_feedback.to_strategy_context()
            # self.logger.info(f"Passing rejection feedback to strategy: {recent_feedback.rejection_rate:.1%} rejection rate")
            pass  # Log disabled temporarily
        
        if self.graph_mode:
            # EMERGENT QUESTIONS FEEDBACK LOOP: Get emergent questions to drive new searches
            emergent_questions = []
            if hasattr(self.llm_coordinator, 'graph'):
                # Get all EmergentQuestion nodes from the graph
                emergent_nodes = self.llm_coordinator.graph.get_nodes_by_type('EmergentQuestion')
                emergent_questions = [node.properties.get('text', '') for node in emergent_nodes if node.properties.get('text')]
                
                if emergent_questions:
                    self.send_progress_update(f"🔍 **Feedback Loop Active**: Using {len(emergent_questions)} emergent questions from previous insights", "info")
                    # Show sample questions for transparency
                    sample_questions = emergent_questions[:2]  # Show first 2 questions
                    for i, q in enumerate(sample_questions, 1):
                        short_q = q[:60] + "..." if len(q) > 60 else q
                        self.send_progress_update(f"   {i}. {short_q}", "markdown")
                elif session.round_count == 1:
                    self.send_progress_update("ℹ️ **Round 1**: No previous emergent questions yet - using initial strategy", "info")
                else:
                    self.send_progress_update("ℹ️ No emergent questions generated from previous rounds", "info")
            
            # Use Graph-Aware LLM Coordinator
            # Pass rejection context if available
            if hasattr(self.llm_coordinator, 'set_rejection_context') and rejection_context:
                self.llm_coordinator.set_rejection_context(rejection_context)
            
            # Pass emergent questions context to the coordinator
            if hasattr(self.llm_coordinator, 'set_emergent_questions_context'):
                self.llm_coordinator.set_emergent_questions_context(emergent_questions)
            
            decision = self.llm_coordinator.make_strategic_decision(session.original_query)
            
            # Display user update
            safe_streamlit("info", f"🤖 **Strategic Decision:** {decision.reasoning}")
            
            # Convert decision to strategy format
            searches = []
            
            # Defensive check for None or empty searches
            if not decision.searches:
                # self.logger.warning("Strategic decision contained no searches")
                print("Warning: Strategic decision contained no searches")
                return {
                    'description': f"Graph Strategy: {decision.reasoning}",
                    'searches': [],
                    'reasoning': decision.reasoning
                }
            
            for search_spec in decision.searches:
                # Skip None entries
                if search_spec is None:
                    # self.logger.warning("Skipping None search_spec in decision.searches")
                    print("Warning: Skipping None search_spec in decision.searches")
                    continue
                # Convert SearchStrategy object to dict format
                try:
                    if hasattr(search_spec, 'parameters'):
                        # It's a SearchStrategy object
                        # Validate that parameters is actually a SearchParameters object
                        if search_spec.parameters is None:
                            params_dict = {}
                        elif hasattr(search_spec.parameters, 'model_dump'):
                            try:
                                params_dict = {k: v for k, v in search_spec.parameters.model_dump().items() if v is not None}
                            except Exception as param_error:
                                # self.logger.error(f"Error dumping parameters: {param_error}")
                                print(f"Error dumping parameters: {param_error}")
                                params_dict = {}
                        else:
                            # parameters exists but isn't a proper object
                            # self.logger.warning(f"Invalid parameters type: {type(search_spec.parameters)}")
                            print(f"Warning: Invalid parameters type: {type(search_spec.parameters)}")
                            params_dict = {}
                        search_plan = {
                            'endpoint': search_spec.endpoint,
                            'params': params_dict,
                            'reason': search_spec.reasoning,
                            'max_pages': 3  # SearchStrategy doesn't have max_pages, use default
                        }
                    else:
                        # Fallback for dict format (backward compatibility)
                        search_plan = {
                            'endpoint': search_spec.get('endpoint', 'search.php'),
                            'params': search_spec.get('parameters', {}),
                            'reason': search_spec.get('reasoning', ''),
                            'max_pages': search_spec.get('max_pages', 3)
                        }
                    searches.append(search_plan)
                except Exception as e:
                    # self.logger.error(f"Error processing search_spec: {e}")
                    print(f"Error processing search_spec: {e}")
                    continue
            
            return {
                'description': f"Graph Strategy: {decision.reasoning}",
                'searches': searches,
                'reasoning': decision.reasoning
            }
        
        else:
            # Use original LLM coordinator (fallback)
            # Initialize coordinator context if needed
            if not hasattr(self.llm_coordinator, 'context') or self.llm_coordinator.context is None:
                self.llm_coordinator.start_investigation(session.original_query)
            
            # Prepare context for LLM coordinator
            current_understanding = self._build_current_understanding(session)
            # Add rejection context to understanding if available
            if rejection_context:
                current_understanding += f" | {rejection_context}"
            information_gaps = self._identify_information_gaps(session)
            search_history = self._format_search_history_for_coordinator(session)
            
            # Get decision from LLM coordinator - NO FALLBACK
            decision = self.llm_coordinator.decide_next_action(
                goal=session.original_query,
                current_understanding=current_understanding,
                gaps=information_gaps,
                search_history=search_history
            )
            
            # Validate decision structure - FAIL FAST if invalid
            required_keys = ['endpoint', 'parameters', 'reasoning']
            missing_keys = [key for key in required_keys if key not in decision]
            if missing_keys:
                raise RuntimeError(f"LLM coordinator returned invalid decision, missing keys: {missing_keys}")
            
            # Display user update if available
            if decision.get('user_update'):
                safe_streamlit("info", f"🤖 **Investigation Update:** {decision['user_update']}")
            
            # Convert decision to strategy format - support multiple searches per round
            searches = []
            
            # Check if decision contains multiple searches (batch planning)
            if 'searches' in decision and isinstance(decision['searches'], list):
                # LLM planned multiple searches for this round
                for search_spec in decision.get('searches', []):
                    # Skip None entries
                    if search_spec is None:
                        # self.logger.warning("Skipping None search_spec in decision['searches']")
                        print("Warning: Skipping None search_spec in decision['searches']")
                        continue
                    # Handle both SearchStrategy objects and dict format
                    try:
                        if hasattr(search_spec, 'parameters'):
                            # It's a SearchStrategy object
                            # Validate that parameters is actually a SearchParameters object
                            if search_spec.parameters is None:
                                params_dict = {}
                            elif hasattr(search_spec.parameters, 'model_dump'):
                                try:
                                    params_dict = {k: v for k, v in search_spec.parameters.model_dump().items() if v is not None}
                                except Exception as param_error:
                                    # self.logger.error(f"Error dumping parameters: {param_error}")
                                    print(f"Error dumping parameters: {param_error}")
                                    params_dict = {}
                            else:
                                # parameters exists but isn't a proper object
                                # self.logger.warning(f"Invalid parameters type: {type(search_spec.parameters)}")
                                print(f"Warning: Invalid parameters type: {type(search_spec.parameters)}")
                                params_dict = {}
                            search_plan = {
                                'endpoint': search_spec.endpoint,
                                'params': params_dict,
                                'reason': search_spec.reasoning,
                                'max_pages': 3  # SearchStrategy doesn't have max_pages, use default
                            }
                        else:
                            # It's a dict (backward compatibility)
                            search_plan = {
                            'endpoint': search_spec.get('endpoint', decision.get('endpoint', 'search.php')),
                            'params': search_spec.get('parameters', search_spec.get('params', {})),
                            'reason': search_spec.get('reasoning', search_spec.get('reason', '')),
                            'max_pages': search_spec.get('max_pages', 3)
                            }
                        searches.append(search_plan)
                    except Exception as e:
                        # self.logger.error(f"Error processing search_spec in fallback: {e}")
                        print(f"Error processing search_spec in fallback: {e}")
                        continue
            else:
                # Single search (backward compatibility)
                search_plan = {
                    'endpoint': decision['endpoint'],
                    'params': decision['parameters'],
                    'reason': decision['reasoning'],
                    'max_pages': 3
                }
                searches.append(search_plan)
            
            return {
                'description': f"LLM Strategy: {decision['reasoning']}",
                'searches': searches,
                'reasoning': decision['reasoning']
            }
    
    def _build_current_understanding(self, session: InvestigationSession) -> str:
        """Build current understanding for LLM coordinator"""
        
        if not session.rounds:
            return "Starting investigation - no searches conducted yet"
        
        understanding_parts = []
        understanding_parts.append(f"Investigation Progress: {session.search_count} searches across {session.round_count} rounds")
        understanding_parts.append(f"Total Results Found: {session.total_results_found}")
        understanding_parts.append(f"Current Satisfaction: {session.satisfaction_metrics.overall_satisfaction():.1%}")
        
        # Add successful findings
        if session.promising_leads:
            understanding_parts.append(f"Successful Approaches: {'; '.join(session.promising_leads[-3:])}")
        
        # Add key insights from recent rounds
        recent_insights = []
        for round_obj in session.rounds[-2:]:
            if round_obj.key_insights:
                recent_insights.extend(round_obj.key_insights)
        
        if recent_insights:
            understanding_parts.append(f"Key Insights: {'; '.join(recent_insights[-3:])}")
        
        return ". ".join(understanding_parts)
    
    def _identify_information_gaps(self, session: InvestigationSession) -> List[str]:
        """Identify current information gaps for LLM coordinator"""
        
        gaps = []
        
        # Check satisfaction dimensions for gaps
        if session.satisfaction_metrics.information_coverage < 0.5:
            gaps.append("Need broader topic coverage and different perspectives")
        
        if session.satisfaction_metrics.source_diversity < 0.3:
            gaps.append("Need more diverse information sources")
        
        if session.satisfaction_metrics.claim_specificity < 0.4:
            gaps.append("Need more specific and detailed information")
        
        if session.total_results_found == 0:
            gaps.append("No relevant results found yet - need alternative search approaches")
        elif session.total_results_found < 20:
            gaps.append("Limited results found - need more comprehensive search coverage")
        
        # Check for failed approaches
        if len(session.dead_ends) > 3:
            gaps.append("Many unsuccessful searches - need different search strategies")
        
        # If no specific gaps identified, add general gap
        if not gaps:
            gaps.append("Continue building comprehensive understanding of the topic")
        
        return gaps
    
    def _format_search_history_for_coordinator(self, session: InvestigationSession) -> List[Dict]:
        """Format search history for LLM coordinator"""
        
        formatted_history = []
        
        for attempt in session.search_history[-10:]:  # Last 10 searches
            formatted_attempt = {
                'search_id': attempt.search_id,
                'query': attempt.params.get('query', 'Unknown'),
                'endpoint': attempt.endpoint,
                'params': attempt.params,
                'results_count': attempt.results_count,
                'effectiveness_score': attempt.effectiveness_score,
                'execution_time': attempt.execution_time,
                'error': attempt.error,
                'round_number': attempt.round_number
            }
            formatted_history.append(formatted_attempt)
        
        return formatted_history
        
    def _build_strategy_context(self, session: InvestigationSession) -> str:
        """Build context string from previous investigation rounds"""
        
        if not session.rounds:
            return "No previous searches conducted."
            
        context_parts = []
        context_parts.append(f"INVESTIGATION PROGRESS: {session.search_count} searches across {session.round_count} rounds")
        context_parts.append(f"TOTAL RESULTS FOUND: {session.total_results_found}")
        context_parts.append(f"SATISFACTION SCORE: {session.satisfaction_metrics.overall_satisfaction():.2f}")
        
        # Add recent rounds summary
        recent_rounds = session.rounds[-3:] if len(session.rounds) > 3 else session.rounds
        for round_obj in recent_rounds:
            context_parts.append(f"\nROUND {round_obj.round_number}: {round_obj.strategy_description}")
            context_parts.append(f"  - Searches: {len(round_obj.searches)}")
            context_parts.append(f"  - Results: {round_obj.total_results}")
            context_parts.append(f"  - Effectiveness: {round_obj.round_effectiveness:.1f}/10")
            
            if round_obj.key_insights:
                context_parts.append(f"  - Key Insights: {'; '.join(round_obj.key_insights[:3])}")
                
        # Add dead ends and promising leads
        if session.dead_ends:
            context_parts.append(f"\nDEAD ENDS (avoid): {'; '.join(session.dead_ends[-5:])}")
        if session.promising_leads:
            context_parts.append(f"\nPROMISING LEADS (explore): {'; '.join(session.promising_leads[-5:])}")
            
        return "\n".join(context_parts)
        
    def _create_strategy_prompt(self, original_query: str, context: str, session: InvestigationSession) -> str:
        """Create LLM prompt for strategy generation"""
        
        return f"""
You are conducting an ITERATIVE INVESTIGATION to answer: "{original_query}"

PREVIOUS INVESTIGATION CONTEXT:
{context}

Your task is to design the NEXT ROUND of searches based on:
1. What has been tried before (avoid repeating ineffective approaches)
2. What gaps remain in the investigation
3. What promising leads should be explored further
4. What new angles or approaches might work

STRATEGY GUIDELINES:
- If previous searches found nothing, try broader terms, name variations, or related topics
- If some results were found, drill deeper into those successful directions  
- Consider alternative spellings, nicknames, or contextual searches
- Think about who would be discussing this topic and where they'd discuss it
- Consider temporal factors (recent vs historical discussions)

Design 2-4 strategic searches for this round that build on previous learnings.
"""

    def _process_llm_strategy(self, llm_response: Dict, session: InvestigationSession) -> Dict[str, Any]:
        """Process LLM response into investigation strategy"""
        
        api_plan = llm_response.get('api_plan', [])
        if not api_plan:
            raise ValueError(f"LLM strategy generation failed - no api_plan returned: {llm_response}")
            
        return {
            'description': llm_response.get('message_to_user', 'Continuing investigation'),
            'searches': api_plan[:4],  # Limit to 4 searches per round
            'reasoning': llm_response.get('message_to_user', '')
        }
        
        
    def _execute_search(self, search_plan: Dict, search_id: int, round_number: int) -> SearchAttempt:
        """Execute a single search and return attempt record"""
        
        start_time = time.time()
        attempt = SearchAttempt(
            search_id=search_id,
            round_number=round_number,
            endpoint=search_plan['endpoint'],
            params=search_plan['params'],
            query_description=search_plan.get('reason', 'Search'),
            results_count=0,
            effectiveness_score=0.0,
            execution_time=0.0
        )
        
        try:
            # Execute the API call
            result = api_client.execute_api_step(
                search_plan, 
                [],  # No dependencies for now
                self.rapidapi_key
            )
            
            attempt.execution_time = time.time() - start_time
            
            if 'error' in result:
                attempt.error = result['error']
                attempt.effectiveness_score = 0.0
            else:
                # Count results - check all possible keys where data might be
                data = result.get('data', {})
                
                # List of all possible keys where results might be stored
                possible_keys = [
                    'timeline', 'followers', 'following', 'users', 
                    'trends', 'retweets', 'affilates', 'members', 
                    'sharings', 'results', 'data'
                ]
                
                # Try to find results in any of these keys
                for key in possible_keys:
                    if isinstance(data, dict) and key in data and isinstance(data[key], list):
                        attempt.results_count = len(data[key])
                        break
                else:
                    # Check if data itself is a list
                    if isinstance(data, list):
                        attempt.results_count = len(data)
                    # Check if it's a single item (non-empty dict)
                    elif isinstance(data, dict) and data:
                        attempt.results_count = 1
                        
                # Extract results for evaluation and store for batch processing
                raw_results = self._extract_results_for_evaluation(result)
                attempt._raw_results = raw_results  # Store for batch evaluation
                
                # For now, use simple scoring - will be overridden by batch evaluation
                attempt.effectiveness_score = self._calculate_simple_effectiveness_score(attempt)
                
        except Exception as e:
            attempt.error = str(e)
            attempt.execution_time = time.time() - start_time
            attempt.effectiveness_score = 0.0
            
        return attempt
        
    def _calculate_effectiveness_score(self, attempt: SearchAttempt, raw_results: List[Dict] = None) -> float:
        """Calculate 0-10 effectiveness score for a search attempt using LLM evaluation"""
        
        if attempt.error:
            return 0.0
            
        if attempt.results_count == 0:
            return 0.0
        
        # LLM evaluation is REQUIRED - no fallback to quantity-based scoring
        if not self.llm_coordinator or not raw_results:
            raise RuntimeError("LLM coordinator and search results are required for effectiveness evaluation")
            
        if not hasattr(self.llm_coordinator, 'context') or not self.llm_coordinator.context:
            raise RuntimeError("LLM coordinator context not initialized - cannot evaluate results")
        
        search_context = {
            'query': attempt.params.get('query', 'Unknown'),
            'endpoint': attempt.endpoint,
            'evaluation_criteria': {
                'information_targets': ['relevant information', 'topic-related content']
            }
        }
        
        evaluation = self.llm_coordinator.evaluate_results(
            goal=self.llm_coordinator.context.goal,
            results=raw_results[:10],  # Limit to first 10 for evaluation
            search_context=search_context
        )
        
        if evaluation.get('relevance_score') is None:
            raise RuntimeError("LLM coordinator failed to provide relevance_score in evaluation")
        
        # Use LLM relevance score as primary effectiveness measure
        llm_score = float(evaluation['relevance_score'])
        
        # Adjust for execution time (small factor)
        time_factor = max(0.9, min(1.0, 10.0 / max(attempt.execution_time, 1.0)))
        
        return min(10.0, llm_score * time_factor)
    
    def _calculate_simple_effectiveness_score(self, attempt: SearchAttempt) -> float:
        """Calculate simple effectiveness score for initial scoring (overridden by batch evaluation)"""
        
        if attempt.error:
            return 0.0
            
        if attempt.results_count == 0:
            return 0.0
        
        # Simple quantity-based scoring for initial estimation
        # This will be overridden by semantic LLM evaluation in batch processing
        base_score = min(8.0, attempt.results_count / 10.0)  # Max 8.0 for quantity
        
        # Time factor (small influence)
        time_factor = max(0.8, min(1.0, 15.0 / max(attempt.execution_time, 1.0)))
        
        return base_score * time_factor
    
    def _extract_results_for_evaluation(self, api_result: Dict) -> List[Dict]:
        """Extract results in a format suitable for LLM evaluation"""
        
        results = []
        
        try:
            data = api_result.get('data', {})
            
            if not data:
                return results
            
            # List of all possible keys where results might be stored
            possible_keys = [
                'timeline', 'followers', 'following', 'users', 
                'trends', 'retweets', 'affilates', 'members', 
                'sharings', 'results', 'data'
            ]
            
            # Try to extract from any key that contains a list
            extracted = False
            for key in possible_keys:
                if isinstance(data, dict) and key in data and isinstance(data[key], list):
                    items = data[key]
                    for item in items[:20]:  # Limit for evaluation
                        if isinstance(item, dict):
                            # Extract text content for evaluation - try multiple fields
                            text_content = (
                                item.get('text') or 
                                item.get('content') or 
                                item.get('description') or
                                item.get('name') or
                                item.get('screen_name') or
                                item.get('title') or
                                str(item)[:500]  # Fallback to string representation
                            )
                            results.append({
                                'text': text_content,
                                'source': f'twitter_api_{key}',
                                'metadata': item
                            })
                    extracted = True
                    break  # Use first list found
            
            # If no list found, check if data itself is a list
            if not extracted and isinstance(data, list):
                for item in data[:20]:
                    if isinstance(item, dict):
                        text_content = (
                            item.get('text') or 
                            item.get('content') or 
                            str(item)[:500]
                        )
                        results.append({
                            'text': text_content,
                            'source': 'twitter_api_list',
                            'metadata': item
                        })
            # Single result case
            elif not extracted and isinstance(data, dict) and data:
                text_content = (
                    data.get('text') or 
                    data.get('content') or 
                    str(data)[:500]
                )
                results.append({
                    'text': text_content,
                    'source': 'twitter_api_single',
                    'metadata': data
                })
                
        except Exception as e:
            # If extraction fails, return empty list
            pass
        
        return results
    
    def _analyze_round_results_with_llm(self, session: InvestigationSession, current_round: InvestigationRound, results: List[SearchAttempt]):
        """Analyze round results using LLM batch evaluation - MORE EFFICIENT"""
        
        if not results:
            return
        
        # === NEW SECTION: Use instance's finding evaluator ===
        # The finding evaluator is already initialized in __init__ with the correct LLM client
        round_datapoints = []  # Track DataPoints created this round
        
        # Collect all results for batch evaluation
        all_results = []
        search_contexts = []
        
        for attempt in results:
            # === NEW: Find existing search node for this attempt ===
            search_node = None
            if self.graph_mode and hasattr(self.llm_coordinator, 'graph'):
                # Find existing SearchQuery node instead of creating duplicate
                search_node = self.llm_coordinator.graph.find_search_query_node(
                    endpoint=attempt.endpoint,
                    parameters=attempt.params
                )
                if not search_node:
                    # If not found, create new node (fallback)
                    search_node = self.llm_coordinator.graph.create_search_query_node(
                        endpoint=attempt.endpoint,
                        parameters=attempt.params
                    )
                
                # === NEW: Batch evaluate findings and create DataPoints ===
                if attempt.results_count > 0 and hasattr(attempt, '_raw_results'):
                    # Use batch evaluation for efficiency
                    results_to_eval = attempt._raw_results[:20]  # Limit to top 20
                    assessments = self.finding_evaluator.evaluate_batch(
                        results_to_eval,
                        session.original_query
                    )
                    
                    # Track rejections for feedback
                    rejection_feedback = analyze_rejections(
                        results_to_eval,
                        assessments,
                        session.original_query
                    )
                    rejection_feedback.round_number = current_round.round_number
                    session.rejection_feedback_history.append(rejection_feedback)
                    
                    # Log rejection statistics
                    # Log rejection statistics (disabled temporarily)
                    # self.logger.log(f"Round {current_round.round_number}: {rejection_feedback.total_evaluated} evaluated, "
                    #                f"{rejection_feedback.total_accepted} accepted, {rejection_feedback.total_rejected} rejected "
                    #                f"({rejection_feedback.rejection_rate:.1%} rejection rate)")
                    
                    # Send user update about rejections if high
                    if rejection_feedback.rejection_rate > 0.8:
                        self.send_progress_update(
                            f"⚠️ High rejection rate ({rejection_feedback.rejection_rate:.0%}) - adjusting strategy",
                            "warning"
                        )
                    
                    # Create DataPoints for significant findings
                    for raw_result, assessment in zip(results_to_eval, assessments):
                        if assessment.is_significant:
                            # Additional goal-relevance filter using context
                            content = raw_result.get('text', '')
                            goal_relevance = session.context.calculate_goal_relevance_score(content) if session.context else 0.5
                            
                            # Only create DataPoint if relevant to investigation goal
                            if goal_relevance > 0.3:  # Context-aware threshold
                                # Try to create DataPoint node if in graph mode
                                if self.graph_mode and hasattr(self.llm_coordinator, 'graph'):
                                    try:
                                        dp = self.llm_coordinator.graph.create_datapoint_node(
                                            content=content,
                                            source=attempt.endpoint,
                                            timestamp=datetime.now().isoformat(),
                                            entities=assessment.entities,
                                            follow_up_needed=assessment.suggested_followup,
                                            relevance_score=assessment.relevance_score,
                                            goal_relevance_score=goal_relevance
                                        )
                                        round_datapoints.append(dp)
                                        
                                        # Connect search to DataPoint if search_node exists
                                        if 'search_node' in locals():
                                            self.llm_coordinator.graph.create_edge(
                                                search_node, dp, "DISCOVERED",
                                                properties={'relevance': assessment.relevance_score}
                                            )
                                    except Exception as e:
                                        # self.logger.debug(f"Could not create graph node: {e}")
                                        pass  # Silently continue
                                
                                # ALWAYS add to accumulated findings (regardless of graph mode)
                                finding = Finding(
                                    content=content,
                                    source=attempt.endpoint,
                                    credibility_score=assessment.relevance_score if assessment else 0.5,
                                    category='tweet',
                                    search_id=attempt.search_id,
                                    evidence_strength='high' if assessment and assessment.relevance_score > 0.7 else 
                                                     'medium' if assessment and assessment.relevance_score > 0.5 else 'low'
                                )
                                session.accumulated_findings.append(finding)
                                
                                # Send progress update about finding
                                self.send_progress_update(
                                    f"Found significant: {content[:100]}...",
                                    "info"
                                )
                
                # REAL-TIME INSIGHT SYNTHESIS
                if self.insight_synthesizer and len(round_datapoints) > 0:
                    for dp in round_datapoints:
                        insights_created = self.insight_synthesizer.process_new_datapoint(dp.id)
                        
                        if insights_created:
                            # User notification
                            self.send_progress_update(
                                f"🧠 Synthesized {len(insights_created)} insights from recent findings",
                                "info"
                            )
                            
                            # Log insight creation
                            for insight_id in insights_created:
                                insight_node = self.llm_coordinator.graph.nodes.get(insight_id)
                                if insight_node:
                                    session.insights_generated.append({
                                        "id": insight_id,
                                        "content": insight_node.properties.get("content", ""),
                                        "confidence": insight_node.properties.get("confidence", 0.0),
                                        "round_number": session.current_round_number if hasattr(session, 'current_round_number') else session.round_count
                                    })
        
            # EXISTING CODE: Get the raw results that were used for individual scoring
            if hasattr(attempt, '_raw_results'):
                all_results.extend(attempt._raw_results)
                search_contexts.append({
                    'search_id': attempt.search_id,
                    'query': attempt.params.get('query', 'Unknown'),
                    'endpoint': attempt.endpoint,
                    'results_count': attempt.results_count
                })
        
        # === NEW SECTION: Generate Insights from DataPoints ===
        if self.graph_mode and len(round_datapoints) >= 3:
            try:
                # Ask LLM to find patterns across DataPoints
                datapoint_contents = [dp.properties['content'] for dp in round_datapoints]
                
                insight_prompt = f"""
                Analyze these findings from investigation "{session.original_query}":
                
                {datapoint_contents}
                
                Identify:
                1. Patterns or commonalities
                2. Contradictions
                3. Key insights
                
                Return as JSON with: synthesis, confidence (0-1), key_pattern
                """
                
                # Use LLM to synthesize insight
                if hasattr(self.llm_coordinator, 'llm_client'):
                    from realtime_insight_synthesizer import InsightSynthesis
                    model = self.model_manager.get_model_for_operation("insight_synthesizer")
                    response = self.llm_coordinator.llm_client.completion(
                        model=model,
                        messages=[{"role": "user", "content": insight_prompt}],
                        response_format=InsightSynthesis
                    )
                    
                    # Handle both new structured output and fallback parsing
                    if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                        # New structured output format
                        insight_obj = response.choices[0].message.parsed
                        insight_data = {
                            'synthesis': insight_obj.content,
                            'confidence': insight_obj.confidence_level,
                            'title': insight_obj.title,
                            'pattern_type': insight_obj.pattern_type,
                            'key_evidence': insight_obj.key_evidence
                        }
                    else:
                        # Fallback to manual JSON parsing
                        import json
                        try:
                            content = response.choices[0].message.content
                            insight_data = json.loads(content)
                        except (json.JSONDecodeError, AttributeError):
                            insight_data = None
                    
                    if insight_data and insight_data.get('confidence', 0) > 0.5:
                        # Create Insight node
                        insight = self.llm_coordinator.graph.create_insight_node_enhanced(
                            content=insight_data.get('synthesis', 'Pattern detected'),
                            confidence=insight_data.get('confidence', 0.5),
                            supporting_datapoints=[dp.id for dp in round_datapoints[:5]],
                            title=insight_data.get('title', 'Investigation Pattern')  # CRITICAL FIX: Pass title from LLM
                        )
                        
                        # Send progress update
                        self.send_progress_update(
                            f"Pattern detected: {insight_data.get('key_pattern', 'Multiple related findings')}",
                            "success"
                        )
                        
            except Exception as e:
                # Log but don't fail investigation
                print(f"Insight generation failed: {e}")
        
        # EXISTING CODE CONTINUES: Single LLM evaluation for the entire round
        if all_results and self.llm_coordinator:
            try:
                if self.graph_mode:
                    # Use Graph-Aware evaluation
                    batch_evaluation = self.llm_coordinator.evaluate_batch_results(
                        session.original_query, 
                        all_results[:50]  # Limit for evaluation
                    )
                    
                    # Apply batch evaluation insights to individual searches
                    batch_relevance = batch_evaluation.relevance_score
                    
                    # Update individual attempt scores based on batch evaluation
                    for attempt in results:
                        if attempt.results_count > 0:
                            # Use batch evaluation as base, adjust for individual contribution
                            individual_factor = min(1.0, attempt.results_count / 20.0)  # Normalize by typical result count
                            attempt.effectiveness_score = min(10.0, batch_relevance * individual_factor)
                    
                    # Store batch insights
                    if batch_evaluation.key_insights:
                        current_round.key_insights = batch_evaluation.key_insights[:3]
                
                else:
                    # Use original coordinator evaluation
                    batch_context = {
                        'round_searches': search_contexts,
                        'total_results': len(all_results),
                        'evaluation_criteria': {
                            'information_targets': ['relevant information', 'topic-related content']
                        }
                    }
                    
                    batch_evaluation = self.llm_coordinator.evaluate_results(
                        goal=self.llm_coordinator.context.goal,
                        results=all_results[:50],  # Limit for evaluation
                        search_context=batch_context
                    )
                    
                    # Apply batch evaluation insights to individual searches
                    batch_relevance = batch_evaluation.get('relevance_score', 5.0)
                    
                    # Update individual attempt scores based on batch evaluation
                    for attempt in results:
                        if attempt.results_count > 0:
                            # Use batch evaluation as base, adjust for individual contribution
                            individual_factor = min(1.0, attempt.results_count / 20.0)  # Normalize by typical result count
                            attempt.effectiveness_score = min(10.0, batch_relevance * individual_factor)
                    
                    # Store batch insights
                    if batch_evaluation.get('key_insights'):
                        current_round.key_insights = batch_evaluation['key_insights'][:3]
                
            except Exception as e:
                # If batch evaluation fails, fall back to individual evaluation
                self._analyze_round_results(session, current_round, results)
                return
        
        # Calculate round effectiveness from updated scores
        if results:
            current_round.round_effectiveness = sum(r.effectiveness_score for r in results) / len(results)
        
        # Continue with other analysis
        successful_searches = [r for r in results if r.effectiveness_score > 5.0]
        failed_searches = [r for r in results if r.effectiveness_score < 2.0]
        
        # Update dead ends and promising leads
        for search in failed_searches:
            search_terms = str(search.params.get('query', ''))
            if search_terms not in session.dead_ends:
                session.dead_ends.append(search_terms)
                
        for search in successful_searches:
            search_terms = str(search.params.get('query', ''))
            if search_terms not in session.promising_leads:
                session.promising_leads.append(search_terms)
        
        # Update satisfaction metrics with batch findings
        if successful_searches:
            batch_findings = []
            for search in successful_searches:
                for i in range(min(search.results_count, 5)):
                    finding = Finding(
                        content=f"Result from {search.query_description}",
                        source="twitter_search",
                        credibility_score=0.7,
                        category="general",
                        search_id=search.search_id,
                        evidence_strength="medium"
                    )
                    batch_findings.append(finding)
                    
            session.accumulated_findings.extend(batch_findings)
            session.update_satisfaction_metrics(batch_findings)
        
    def _analyze_round_results(self, session: InvestigationSession, current_round: InvestigationRound, results: List[SearchAttempt]):
        """Analyze results from completed round"""
        
        # Calculate round effectiveness
        if results:
            current_round.round_effectiveness = sum(r.effectiveness_score for r in results) / len(results)
        
        # Identify insights and patterns
        successful_searches = [r for r in results if r.effectiveness_score > 5.0]
        failed_searches = [r for r in results if r.effectiveness_score < 2.0]
        
        # Update dead ends and promising leads
        for search in failed_searches:
            search_terms = str(search.params.get('query', ''))
            if search_terms not in session.dead_ends:
                session.dead_ends.append(search_terms)
                
        for search in successful_searches:
            search_terms = str(search.params.get('query', ''))
            if search_terms not in session.promising_leads:
                session.promising_leads.append(search_terms)
                
        # Generate insights
        insights = []
        if successful_searches:
            insights.append(f"Found {sum(s.results_count for s in successful_searches)} relevant results")
        if failed_searches:
            insights.append(f"{len(failed_searches)} searches yielded no results")
            
        current_round.key_insights = insights
        
        # Update satisfaction metrics
        if successful_searches:
            # Create mock findings for satisfaction calculation
            mock_findings = []
            for search in successful_searches:
                for i in range(min(search.results_count, 5)):  # Sample findings
                    finding = Finding(
                        content=f"Result from {search.query_description}",
                        source="twitter_search",
                        credibility_score=0.7,
                        category="general",
                        search_id=search.search_id,
                        evidence_strength="medium"
                    )
                    mock_findings.append(finding)
                    
            session.accumulated_findings.extend(mock_findings)
            session.update_satisfaction_metrics(mock_findings)
    
    def _display_round_header(self, session: InvestigationSession, round_obj: InvestigationRound, strategy: Dict):
        """Display investigation round header"""
        
        safe_streamlit("markdown", f"""
        ### 🔍 INVESTIGATION ROUND {round_obj.round_number}/{session.config.max_searches//4}
        **Strategy:** {strategy['description']}
        
        **Progress:** {session.search_count}/{session.config.max_searches} searches | 
        **Satisfaction:** {'█' * int(session.satisfaction_metrics.overall_satisfaction() * 10)}{'░' * (10 - int(session.satisfaction_metrics.overall_satisfaction() * 10))} 
        {session.satisfaction_metrics.overall_satisfaction():.1%}
        """)
        
    def _display_search_attempt(self, placeholder, search_plan: Dict, search_id: int):
        """Display search attempt in progress"""
        
        query_str = search_plan['params'].get('query', 'Unknown query')
        endpoint = search_plan['endpoint']
        
        placeholder.markdown(f"""
        **Search {search_id}:** {query_str}
        - Endpoint: `{endpoint}` | Pages: {search_plan.get('max_pages', 3)}
        - Strategy: {search_plan.get('reason', 'No description')}
        - Status: 🔄 Executing...
        """)
        
    def _display_search_results(self, placeholder, attempt: SearchAttempt):
        """Display completed search results"""
        
        # Create effectiveness stars
        stars = '⭐' * int(attempt.effectiveness_score / 2) + '☆' * (5 - int(attempt.effectiveness_score / 2))
        
        query_str = attempt.params.get('query', 'Unknown query')
        
        status_emoji = "✅" if not attempt.error else "❌"
        error_text = f"\n- Error: {attempt.error}" if attempt.error else ""
        
        placeholder.markdown(f"""
        **Search {attempt.search_id}:** {query_str}
        - Endpoint: `{attempt.endpoint}` | Time: {attempt.execution_time:.1f}s
        - Strategy: {attempt.query_description}
        - Results: {attempt.results_count} tweets | Effectiveness: {stars} ({attempt.effectiveness_score:.1f}/10)
        - Status: {status_emoji} {'Completed' if not attempt.error else 'Failed'}{error_text}
        """)
        
    def _display_investigation_progress(self, session: InvestigationSession):
        """Display overall investigation progress"""
        
        should_continue, reason = session.should_continue()
        
        safe_streamlit("markdown", f"""
        ---
        **📊 Investigation Status:** {reason}
        
        **Key Metrics:**
        - Total Results Found: {session.total_results_found}
        - Unique Sources: {len(set(f.source for f in session.accumulated_findings))}  
        - Investigation Satisfaction: {session.satisfaction_metrics.overall_satisfaction():.1%}
        
        **Next Action:** {'🔍 Planning next round...' if should_continue else '✅ Investigation complete'}
        """)
        
    def _display_batch_evaluation(self, current_round: InvestigationRound, results: List[SearchAttempt]):
        """Display what the LLM learned from this batch and how it affects next strategy"""
        
        if not results:
            return
            
        # Calculate batch metrics
        total_results = sum(r.results_count for r in results)
        avg_effectiveness = current_round.round_effectiveness
        successful_searches = [r for r in results if r.effectiveness_score > 5.0]
        
        # Create effectiveness indicator
        effectiveness_color = (
            "🟢" if avg_effectiveness >= 7 else
            "🟡" if avg_effectiveness >= 4 else
            "🔴"
        )
        
        safe_streamlit("markdown", "---")
        safe_streamlit("markdown", f"### {effectiveness_color} **BATCH {current_round.round_number} EVALUATION**")
        
        # Display batch results summary
        safe_streamlit("markdown", f"""
        **📊 Batch Results:**
        - **Searches Executed:** {len(results)}
        - **Total Results Found:** {total_results} tweets
        - **Average Effectiveness:** {avg_effectiveness:.1f}/10
        - **Successful Searches:** {len(successful_searches)}/{len(results)}
        """)
        
        # Display LLM key insights
        if current_round.key_insights:
            safe_streamlit("markdown", "**🧠 LLM Analysis - What We Learned:**")
            for i, insight in enumerate(current_round.key_insights, 1):
                safe_streamlit("markdown", f"  {i}. {insight}")
        else:
            safe_streamlit("markdown", "**🧠 LLM Analysis:** No significant insights extracted from this batch")
        
        # Display most/least effective searches for learning
        if len(results) > 1:
            best_search = max(results, key=lambda r: r.effectiveness_score)
            worst_search = min(results, key=lambda r: r.effectiveness_score)
            
            safe_streamlit("markdown", "**📈 Search Performance Analysis:**")
            safe_streamlit("markdown", f"- **Most Effective:** `{best_search.params.get('query', 'Unknown')}` → {best_search.results_count} results ({best_search.effectiveness_score:.1f}/10)")
            safe_streamlit("markdown", f"- **Least Effective:** `{worst_search.params.get('query', 'Unknown')}` → {worst_search.results_count} results ({worst_search.effectiveness_score:.1f}/10)")
        
        # Display strategy hints for next round
        if current_round.next_strategy_hints:
            safe_streamlit("markdown", "**🎯 Strategy Recommendations for Next Round:**")
            for hint in current_round.next_strategy_hints:
                safe_streamlit("markdown", f"  • {hint}")
        
        # Show graph context influence (if graph mode)
        if hasattr(self, 'graph_mode') and self.graph_mode:
            try:
                if hasattr(self.llm_coordinator, 'graph'):
                    graph = self.llm_coordinator.graph
                    knowledge_nodes = len(graph.nodes) if hasattr(graph, 'nodes') else 0
                    if knowledge_nodes > 0:
                        safe_streamlit("markdown", f"**🕸️ Investigation Graph:** {knowledge_nodes} knowledge nodes accumulated")
            except:
                pass  # Don't break display if graph info fails
        
        safe_streamlit("markdown", "---")