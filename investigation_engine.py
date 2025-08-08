# investigation_engine.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import streamlit as st
import time
import math

# Import existing modules
import llm_handler
import api_client
import graph_manager

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
    
    # Search behavior
    pages_per_search: int = 3
    search_timeout_seconds: int = 30
    retry_failed_searches: bool = True

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
        
        # Intelligence tracking
        self.dead_ends: List[str] = []  # failed approaches
        self.promising_leads: List[str] = []  # successful directions
        self.effective_search_patterns: Dict[str, float] = {}
        
        # Satisfaction tracking
        self.satisfaction_metrics = SatisfactionMetrics()
        self.satisfaction_history: List[float] = []
        
        # Status
        self.is_active = True
        self.completion_reason: Optional[str] = None
        
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
    
    def __init__(self, rapidapi_key: str):
        self.rapidapi_key = rapidapi_key
        
    def conduct_investigation(self, query: str, config: InvestigationConfig = None) -> 'InvestigationSession':
        """Conduct a complete iterative investigation"""
        
        if config is None:
            config = InvestigationConfig()
            
        session = InvestigationSession(query, config)
        
        # Create containers for real-time updates
        progress_container = st.container()
        details_container = st.container()
        
        try:
            while session.should_continue()[0]:
                # Generate next strategy
                strategy = self._generate_strategy(session)
                current_round = session.start_new_round(strategy['description'])
                
                # Display round header
                with progress_container:
                    self._display_round_header(session, current_round, strategy)
                
                # Execute searches for this round
                round_results = []
                for i, search_plan in enumerate(strategy['searches']):
                    search_id = session.search_count + 1
                    
                    # Display search attempt
                    with details_container:
                        search_placeholder = st.empty()
                        self._display_search_attempt(search_placeholder, search_plan, search_id)
                    
                    # Execute the search
                    attempt = self._execute_search(search_plan, search_id, current_round.round_number)
                    session.add_search_attempt(attempt)
                    round_results.append(attempt)
                    
                    # Update display with results
                    with details_container:
                        self._display_search_results(search_placeholder, attempt)
                    
                    # Break if we hit limits mid-round
                    if not session.should_continue()[0]:
                        break
                
                # Analyze round results
                self._analyze_round_results(session, current_round, round_results)
                
                # Update progress display
                with progress_container:
                    self._display_investigation_progress(session)
                    
            # Investigation complete
            session.is_active = False
            session.completion_reason = session.should_continue()[1]
            
            return session
            
        except Exception as e:
            session.is_active = False
            session.completion_reason = f"Investigation failed: {str(e)}"
            st.error(f"Investigation error: {e}")
            return session
            
    def _generate_strategy(self, session: InvestigationSession) -> Dict[str, Any]:
        """Generate next investigation strategy using adaptive planner"""
        
        try:
            # Import here to avoid circular dependencies
            from adaptive_planner import AdaptivePlanner
            
            # Use adaptive planner for intelligent strategy generation
            planner = AdaptivePlanner()
            strategy = planner.generate_adaptive_strategy(session)
            
            return strategy
            
        except Exception as e:
            print(f"Adaptive planner failed: {e}")
            # Fallback to simple strategy generation
            return self._create_fallback_strategy(session)
        
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
            return self._create_fallback_strategy(session)
            
        return {
            'description': llm_response.get('message_to_user', 'Continuing investigation'),
            'searches': api_plan[:4],  # Limit to 4 searches per round
            'reasoning': llm_response.get('message_to_user', '')
        }
        
    def _create_fallback_strategy(self, session: InvestigationSession) -> Dict[str, Any]:
        """Create fallback strategy when LLM fails"""
        
        base_query = session.original_query.lower()
        
        # Extract potential name from query
        words = base_query.split()
        potential_names = [word for word in words if word.isalpha() and len(word) > 3]
        
        searches = []
        if potential_names and len(potential_names) >= 2:
            name = f"{potential_names[0]} {potential_names[1]}"
            searches = [
                {
                    'step': 1,
                    'endpoint': 'search.php',
                    'params': {'query': f'"{name}" debunked', 'result_type': 'latest'},
                    'reason': f'Direct search for debunking information about {name}',
                    'max_pages': 3
                },
                {
                    'step': 2,
                    'endpoint': 'search.php', 
                    'params': {'query': f'"{name}" hoax', 'result_type': 'latest'},
                    'reason': f'Search for hoax claims about {name}',
                    'max_pages': 3
                }
            ]
            
        if not searches:
            searches = [
                {
                    'step': 1,
                    'endpoint': 'search.php',
                    'params': {'query': base_query, 'result_type': 'latest'},
                    'reason': 'Basic search for the query topic',
                    'max_pages': 3
                }
            ]
            
        return {
            'description': 'Fallback search strategy',
            'searches': searches,
            'reasoning': 'Using fallback strategy due to planning failure'
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
                # Count results
                data = result.get('data', {})
                if isinstance(data, dict):
                    timeline = data.get('timeline', [])
                    if isinstance(timeline, list):
                        attempt.results_count = len(timeline)
                        
                # Calculate effectiveness score
                attempt.effectiveness_score = self._calculate_effectiveness_score(attempt)
                
        except Exception as e:
            attempt.error = str(e)
            attempt.execution_time = time.time() - start_time
            attempt.effectiveness_score = 0.0
            
        return attempt
        
    def _calculate_effectiveness_score(self, attempt: SearchAttempt) -> float:
        """Calculate 0-10 effectiveness score for a search attempt"""
        
        if attempt.error:
            return 0.0
            
        # Base score from result count
        if attempt.results_count == 0:
            return 0.0
        elif attempt.results_count < 5:
            base_score = 3.0
        elif attempt.results_count < 20:
            base_score = 6.0
        elif attempt.results_count < 50:
            base_score = 8.0
        else:
            base_score = 9.0
            
        # Adjust for execution time (faster is better)
        time_factor = max(0.5, min(1.0, 5.0 / max(attempt.execution_time, 0.1)))
        
        return min(10.0, base_score * time_factor)
        
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
        
        st.markdown(f"""
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
        
        st.markdown(f"""
        ---
        **📊 Investigation Status:** {reason}
        
        **Key Metrics:**
        - Total Results Found: {session.total_results_found}
        - Unique Sources: {len(set(f.source for f in session.accumulated_findings))}  
        - Investigation Satisfaction: {session.satisfaction_metrics.overall_satisfaction():.1%}
        
        **Next Action:** {'🔍 Planning next round...' if should_continue else '✅ Investigation complete'}
        """)