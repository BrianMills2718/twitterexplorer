# graph_aware_llm_coordinator.py
"""
Graph-Aware LLM Coordinator - Enhanced Intelligence with Full Context

This replaces the linear LLM coordinator with graph-based strategic intelligence
that uses complete investigation context for coherent decision making.
"""

import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from investigation_graph import InvestigationGraph, InvestigationContext
from llm_client import (
    LiteLLMClient, InvestigationEvaluation, 
    ContextSynthesis, EmergentQuestions,
    StrategicDecision,
    SearchStrategy, SearchParameters
)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from adaptive_strategy_system import AdaptiveStrategySystem

# Use base StrategicDecision directly to avoid schema conflicts

class UnderstandingSynthesis(BaseModel):
    """Current understanding synthesis from graph analysis"""
    current_understanding: str
    confidence_level: float
    key_findings: List[str]
    critical_gaps: List[str]
    investigation_completeness: float = Field(description="Completeness score of the investigation from 0.0 to 1.0")
    next_priorities: Optional[List[str]] = Field(description="Priority areas for future investigation")

class EmergentQuestion(BaseModel):
    """Question that emerged during investigation"""
    text: str
    emergence_reason: str
    priority: float = Field(description="Priority score for this emergent question from 0.0 to 1.0")

class EndpointDiversityTracker:
    """Tracks and enforces endpoint diversity in investigations"""
    
    def __init__(self):
        self.endpoint_usage = {}
        self.available_endpoints = [
            "search.php", "timeline.php", "screenname.php", "mentions.php",
            "replies.php", "trends.php", "followers.php", "follows.php",
            "community.php", "list.php", "bookmark.php", "notifications.php",
            "saved_searches.php", "quotes.php", "dm.php", "analytics.php"
        ]
        
    def record_usage(self, endpoint: str):
        """Record usage of an endpoint"""
        self.endpoint_usage[endpoint] = self.endpoint_usage.get(endpoint, 0) + 1
        
    def get_usage_count(self, endpoint: str) -> int:
        """Get usage count for specific endpoint"""
        return self.endpoint_usage.get(endpoint, 0)
        
    def get_overused_endpoints(self, threshold: int = 3) -> List[str]:
        """Get endpoints that have been overused"""
        return [ep for ep, count in self.endpoint_usage.items() if count >= threshold]
        
    def get_unused_endpoints(self) -> List[str]:
        """Get endpoints that haven't been used yet"""
        return [ep for ep in self.available_endpoints if ep not in self.endpoint_usage]
        
    def get_least_used_endpoints(self, n: int = 3) -> List[str]:
        """Get n least used endpoints"""
        unused = self.get_unused_endpoints()
        if len(unused) >= n:
            return unused[:n]
        
        # Include used endpoints sorted by usage
        used_sorted = sorted(
            [(ep, count) for ep, count in self.endpoint_usage.items()],
            key=lambda x: x[1]
        )
        
        result = unused[:]
        for ep, _ in used_sorted:
            if len(result) >= n:
                break
            if ep not in result:
                result.append(ep)
        
        return result[:n]
        
    def calculate_diversity_score(self) -> float:
        """Calculate diversity score (0-1, higher is better)"""
        if not self.endpoint_usage:
            return 0.0
        
        unique_endpoints = len(self.endpoint_usage)
        total_uses = sum(self.endpoint_usage.values())
        
        if total_uses == 0:
            return 0.0
            
        # Diversity is ratio of unique endpoints to total uses
        # Adjusted by distribution evenness
        base_diversity = unique_endpoints / min(total_uses, len(self.available_endpoints))
        
        # Calculate evenness (how evenly distributed usage is)
        if unique_endpoints > 1:
            avg_usage = total_uses / unique_endpoints
            variance = sum((count - avg_usage) ** 2 for count in self.endpoint_usage.values())
            evenness = 1.0 / (1.0 + variance / total_uses)
        else:
            evenness = 0.0
            
        return (base_diversity * 0.7 + evenness * 0.3)
        
    def suggest_next_endpoint(self, investigation_context: str) -> str:
        """Suggest the best endpoint to use next based on diversity and context"""
        # Get overused and unused endpoints
        overused = self.get_overused_endpoints(threshold=3)
        unused = self.get_unused_endpoints()
        least_used = self.get_least_used_endpoints(5)
        
        # Prefer unused endpoints, then least used, avoid overused
        candidates = unused if unused else least_used
        
        # Filter out overused endpoints unless no choice
        filtered = [ep for ep in candidates if ep not in overused]
        candidates = filtered if filtered else candidates
        
        # For now, return first candidate (could be enhanced with context analysis)
        return candidates[0] if candidates else "search.php"

class ContextManager:
    """Manages context optimization for LLM processing"""
    
    def __init__(self, max_tokens: int = 50000):
        self.max_tokens = max_tokens
        
    def optimize_context(self, full_context: str) -> str:
        """Optimize context to fit within token limits while preserving critical information"""
        
        # Simple word-based approximation (roughly 1.3 words per token)
        estimated_tokens = len(full_context.split()) * 1.3
        
        if estimated_tokens <= self.max_tokens:
            return full_context
        
        # If context is too large, prioritize sections
        lines = full_context.split('\n')
        priority_sections = {
            "ORIGINAL GOAL:": 1.0,
            "CURRENT INFORMATION GAPS:": 0.9, 
            "FAILED APPROACHES": 0.8,
            "STRATEGIC COHERENCE DECISION POINT:": 1.0,
            "INVESTIGATION PROGRESS:": 0.7,
            "DISCONNECTED THREADS:": 0.6
        }
        
        # Keep high priority sections, truncate others
        optimized_lines = []
        current_section = None
        section_priority = 0.5
        
        for line in lines:
            # Check if this is a new section
            for section, priority in priority_sections.items():
                if section in line:
                    current_section = section
                    section_priority = priority
                    break
            
            # Keep line if high priority or if we're not over the limit yet
            estimated_length = len(' '.join(optimized_lines + [line]).split()) * 1.3
            
            if section_priority >= 0.8 or estimated_length < self.max_tokens:
                optimized_lines.append(line)
            elif section_priority >= 0.6:
                # Truncate lower priority sections
                optimized_lines.append(f"[... {current_section} content truncated for brevity ...]")
        
        return '\n'.join(optimized_lines)

class GraphAwareLLMCoordinator:
    """
    Enhanced LLM coordinator with full graph context awareness
    
    Uses complete investigation graph to make strategic decisions with coherence,
    emergent question detection, and progressive understanding synthesis.
    """
    
    def __init__(self, llm_client: LiteLLMClient, graph: InvestigationGraph, model_manager=None):
        self.llm = llm_client
        self.graph = graph
        self.context = None  # Investigation context
        self.context_manager = ContextManager()
        self.diversity_tracker = EndpointDiversityTracker()
        self.adaptive_strategy = AdaptiveStrategySystem()
        self.search_history = []  # Track searches for adaptation
        self.emergent_questions = []  # Emergent questions to drive follow-up searches
        self.logger = logging.getLogger(__name__)  # Initialize logger
        
        # Initialize model manager
        if model_manager is None:
            from llm_model_manager import LLMModelManager
            self.model_manager = LLMModelManager()
        else:
            self.model_manager = model_manager
        
    def set_context(self, context):
        """Set investigation context for goal-aware processing"""
        self.context = context
        self.total_results_found = 0
        self.logger = logging.getLogger(__name__)
        self.rejection_context = ""  # Track what was rejected from previous rounds
        
        # Complete endpoint specifications from merged_endpoints.json (16 total endpoints)
        self.available_endpoints = {
            'search.php': {
                'required_params': ['query'],
                'optional_params': ['cursor', 'search_type'],
                'search_type_values': ['Top', 'Latest', 'Media', 'People', 'Lists'],
                'description': 'Targeted searches for specific content, user posts about topics, mentions',
                'best_for': 'Finding User X posts about Topic Y, targeted content discovery, specific claims research',
                'query_examples': ['climate change policy', 'from:username topic', '@username', 'technology trends 2024'],
                'advanced_operators': ['from:username', 'to:username', '@username', 'Boolean operators (AND OR)', 'exclusion with -term']
            },
            'timeline.php': {
                'required_params': ['screenname'],
                'optional_params': ['rest_id', 'cursor'],
                'description': 'User\'s recent posts ONLY - no topic filtering',
                'best_for': 'Recent activity overview, general user posting patterns',
                'limitation': 'Cannot filter by topic - returns chronological timeline only'
            },
            'screenname.php': {
                'required_params': ['screenname'],
                'optional_params': ['rest_id'],
                'description': 'User profile information and validation',
                'best_for': 'User verification, profile information, follower counts, bio'
            },
            'following.php': {
                'required_params': ['screenname'],
                'optional_params': ['cursor', 'rest_id'],
                'description': 'Who a user follows - reveals associations and connections',
                'best_for': 'Network analysis, finding connections and associations'
            },
            'followers.php': {
                'required_params': ['screenname'],
                'optional_params': ['cursor'],
                'description': 'Who follows a user - reveals audience and influence patterns',
                'best_for': 'Influence analysis, credibility assessment, audience patterns'
            },
            'tweet.php': {
                'required_params': ['id'],
                'optional_params': [],
                'description': 'Individual tweet details with full metadata',
                'best_for': 'Deep analysis of specific claims, viral content examination'
            },
            'latest_replies.php': {
                'required_params': ['id'],
                'optional_params': ['cursor'],
                'description': 'Replies to specific tweets - shows reactions and discussions',
                'best_for': 'Reaction analysis, counter-arguments, discussion patterns'
            },
            'tweet_thread.php': {
                'required_params': ['id'],
                'optional_params': ['cursor'],
                'description': 'Complete conversation threads from a tweet',
                'best_for': 'Full context analysis, comprehensive discussion tracking'
            },
            'trends.php': {
                'required_params': ['country'],
                'optional_params': [],
                'country_format': 'Must be one word - e.g. UnitedStates, not United States',
                'description': 'Current trending topics by location',
                'best_for': 'Current events context, topic relevance validation'
            },
            'usermedia.php': {
                'required_params': ['screenname'],
                'optional_params': ['rest_id', 'cursor'],
                'description': 'User media posts (photos, videos) with context',
                'best_for': 'Visual evidence analysis, media-based claims investigation'
            },
            'retweets.php': {
                'required_params': ['id'],
                'optional_params': ['cursor'],
                'description': 'Who retweeted a specific tweet - amplification analysis',
                'best_for': 'Amplification patterns, network influence, viral spread analysis'
            },
            'affilates.php': {
                'required_params': ['screenname'],
                'optional_params': ['cursor'],
                'description': 'User affiliations and connections',
                'best_for': 'Network mapping, association analysis'
            },
            'checkretweet.php': {
                'required_params': ['screenname', 'tweet_id'],
                'optional_params': [],
                'description': 'Check if user retweeted specific tweet',
                'best_for': 'Engagement verification, amplification tracking'
            },
            'checkfollow.php': {
                'required_params': ['user', 'follows'],
                'optional_params': [],
                'description': 'Check if user follows another user',
                'best_for': 'Network relationship verification'
            },
            'listtimeline.php': {
                'required_params': ['list_id'],
                'optional_params': ['cursor'],
                'description': 'Timeline from a specific Twitter list',
                'best_for': 'Curated content analysis, topic-specific feeds'
            },
            'screennames.php': {
                'required_params': ['rest_ids'],
                'optional_params': [],
                'description': 'Bulk user profile lookup by rest_ids',
                'best_for': 'Batch user information retrieval'
            }
        }
    
    def start_investigation(self, goal: str) -> InvestigationContext:
        """Initialize investigation with graph-based context"""
        # Create analytic question if not exists
        if not self.graph.analytic_question:
            self.graph.create_analytic_question_node(goal)
        
        context = InvestigationContext(goal=goal, graph=self.graph)
        self.logger.info(f"Started graph-aware investigation: {goal}")
        return context
    
    def set_rejection_context(self, context: str):
        """Set rejection feedback context for next strategy generation"""
        self.rejection_context = context
        self.logger.info(f"Rejection context set: {len(context)} chars")
    
    def set_emergent_questions_context(self, emergent_questions: List[str]):
        """Set emergent questions to drive follow-up searches"""
        self.emergent_questions = emergent_questions
        if emergent_questions:
            self.logger.info(f"Emergent questions set: {len(emergent_questions)} questions")
        else:
            self.emergent_questions = []
    
    def check_and_adapt_strategy(self, goal: str) -> Optional[StrategicDecision]:
        """
        Check if strategy adaptation is needed and generate pivot if necessary
        
        Returns pivot strategy if needed, None otherwise
        """
        # Analyze current situation
        analysis = self.adaptive_strategy.analyze_situation(
            recent_searches=self.search_history[-10:],
            total_results=self.total_results_found,
            investigation_goal=goal
        )
        
        if analysis["needs_pivot"]:
            self.logger.info(f"ADAPTIVE: Pivoting strategy due to {analysis['pivot_reason']}")
            self.logger.info(f"ADAPTIVE: Recommended strategy: {analysis['recommended_strategy']}")
            
            # Generate pivot strategy
            current_context = {
                "searches_conducted": len(self.search_history),
                "results_found": self.total_results_found,
                "endpoints_used": list(self.diversity_tracker.endpoint_usage.keys()),
                "recent_queries": [s.get('query', '') for s in self.search_history[-5:]]
            }
            
            pivot_strategy = self.adaptive_strategy.generate_pivot_strategy(
                current_context=current_context,
                pivot_type=analysis['recommended_strategy'],
                investigation_goal=goal
            )
            
            # Convert to StrategicDecision
            searches = []
            for search in pivot_strategy.get('searches', []):
                searches.append(SearchStrategy(
                    endpoint=search['endpoint'],
                    parameters=SearchParameters(**search['parameters']),
                    reasoning=search['reasoning']
                ))
            
            decision = StrategicDecision(
                decision_type="pivot",
                reasoning=f"ADAPTIVE PIVOT: {pivot_strategy.get('reasoning', 'Adapting strategy')}",
                searches=searches,
                expected_outcomes=["Find alternative information sources", "Break out of ineffective pattern"],
                context_utilization=0.9,
                strategic_coherence_score=0.8
            )
            
            return decision
        
        return None
    
    def make_strategic_decision(self, goal: str) -> StrategicDecision:
        """
        Make strategic decision using complete graph context
        
        EVIDENCE REQUIREMENT: Must use full context for coherent decisions
        """
        # First check if we need to adapt/pivot strategy
        pivot_decision = self.check_and_adapt_strategy(goal)
        if pivot_decision:
            self.logger.info("ADAPTIVE: Using pivot strategy instead of normal decision")
            
            # CRITICAL: Validate pivot decision parameters too
            validated_pivot_decision = self._enforce_parameter_validation(pivot_decision)
            
            # Track the validated pivot searches
            for search in validated_pivot_decision.searches:
                self.search_history.append({
                    'endpoint': search.endpoint,
                    'query': search.parameters.query if hasattr(search.parameters, 'query') else None,
                    'parameters': search.parameters
                })
            return validated_pivot_decision
        
        try:
            # Get complete strategic context from graph
            strategic_context = self.graph.get_strategic_context_for_llm()
            optimized_context = self.context_manager.optimize_context(strategic_context)
            
            # Calculate context utilization
            context_utilization = min(1.0, len(optimized_context.split()) / len(strategic_context.split()))
            
            # Create strategic decision prompt
            prompt = self._create_strategic_decision_prompt(goal, optimized_context)
            
            # DIAGNOSTIC: Log prompt size for analysis
            self.logger.info(f"DIAGNOSTIC: Prompt size: {len(prompt)} chars, {len(prompt.split())} words")
            self.logger.info(f"DIAGNOSTIC: Prompt lines: {len(prompt.split(chr(10)))} lines")
            
            # Get LLM decision with structured output
            model = self.model_manager.get_model_for_operation("strategic_coordinator")
            response = self.llm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=StrategicDecision
            )
            
            # CRITICAL: Store raw response for diagnostics
            self._last_raw_response = response.model_dump() if hasattr(response, 'model_dump') else str(response)
            self.logger.info(f"DIAGNOSTIC: Raw LLM response captured")
            
            # Parse structured response - use .parsed if available, fallback to manual parsing
            if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                # New structured output format
                base_decision = response.choices[0].message.parsed
                decision = StrategicDecision(
                    decision_type=base_decision.decision_type,
                    reasoning=base_decision.reasoning,
                    searches=base_decision.searches,
                    expected_outcomes=base_decision.expected_outcomes,
                    confidence=base_decision.confidence,
                    context_utilization=context_utilization,
                    strategic_coherence_score=0.8
                )
            else:
                # Fallback to JSON parsing
                response_content = response.choices[0].message.content
                if response_content:
                    import json
                    base_decision_data = json.loads(response_content)
                    decision = StrategicDecision(
                        decision_type=base_decision_data.get("decision_type", "gap_filling"),
                        reasoning=base_decision_data.get("reasoning", ""),
                        searches=base_decision_data.get("searches", []),
                        expected_outcomes=base_decision_data.get("expected_outcomes", []),
                        confidence=base_decision_data.get("confidence"),
                        context_utilization=context_utilization,
                        strategic_coherence_score=0.8
                    )
                else:
                    # FAIL FAST - No fallback!
                    self.logger.error(f"DIAGNOSTIC: LLM response had no parsed output or content")
                    raise RuntimeError("LLM returned no structured output or content. Check LiteLLM configuration and API key.")
            
            # DIAGNOSTIC: Log decision details (for both successful parsing paths)
            self.logger.info(f"DIAGNOSTIC: Decision type: {decision.decision_type}")
            self.logger.info(f"DIAGNOSTIC: Searches count: {len(decision.searches)}")
            self.logger.info(f"DIAGNOSTIC: Reasoning length: {len(decision.reasoning)} chars")
            
            # Log each search decision AND track endpoint usage
            for i, search in enumerate(decision.searches):
                endpoint = search.endpoint
                self.logger.info(f"DIAGNOSTIC: Search {i+1} - Endpoint: {endpoint}")
                
                # CRITICAL: Track endpoint usage for diversity
                self.diversity_tracker.record_usage(endpoint)
                
                if hasattr(search, 'parameters'):
                    params_str = str(search.parameters.model_dump() if hasattr(search.parameters, 'model_dump') else search.parameters)
                    self.logger.info(f"DIAGNOSTIC: Search {i+1} - Parameters: {params_str}")
                self.logger.info(f"DIAGNOSTIC: Search {i+1} - Reasoning: {search.reasoning[:100]}...")
            
            # Log diversity metrics
            diversity_score = self.diversity_tracker.calculate_diversity_score()
            self.logger.info(f"DIAGNOSTIC: Endpoint diversity score: {diversity_score:.2f}")
            self.logger.info(f"DIAGNOSTIC: Endpoints used: {list(self.diversity_tracker.endpoint_usage.keys())}")
            
            # CRITICAL: Validate parameters and prevent placeholders from reaching API
            validated_decision = self._enforce_parameter_validation(decision)
            
            # Update graph with validated decision  
            self._update_graph_with_decision(validated_decision)
            
            return validated_decision
                
        except Exception as e:
            self.logger.error(f"Error in make_strategic_decision: {e}")
            self.logger.error(f"DIAGNOSTIC: Prompt was: {prompt[:500]}..." if 'prompt' in locals() else "DIAGNOSTIC: Prompt not created")
            # FAIL FAST - No fallback!
            raise RuntimeError(f"LLM strategic decision failed: {e}") from e
    
    def track_search_results(self, endpoint: str, query: str, results_count: int):
        """Track search results for adaptation"""
        search_record = {
            'endpoint': endpoint,
            'query': query,
            'results_count': results_count,
            'timestamp': datetime.now()
        }
        self.search_history.append(search_record)
        self.total_results_found += results_count
        
        # Update adaptive strategy tracking
        strategy_type = "search" if endpoint == "search.php" else endpoint.replace(".php", "")
        self.adaptive_strategy.update_effectiveness(strategy_type, results_count)
        
        # Log if no results
        if results_count == 0:
            self.logger.warning(f"ADAPTIVE: No results from {endpoint} with query: {query[:50]}")
    
    def evaluate_batch_results(self, goal: str, results: List[Dict]) -> InvestigationEvaluation:
        """
        Evaluate batch of results using semantic analysis
        
        EVIDENCE REQUIREMENT: Must distinguish relevant from irrelevant semantically
        """
        try:
            # Create evaluation prompt
            prompt = self._create_evaluation_prompt(goal, results)
            
            # Get LLM evaluation with structured output
            model = self.model_manager.get_model_for_operation("strategic_coordinator")
            response = self.llm.completion(
                model=model, 
                messages=[{"role": "user", "content": prompt}],
                response_format=InvestigationEvaluation
            )
            
            # Parse structured response - use .parsed if available, fallback to manual parsing
            if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                # New structured output format
                evaluation = response.choices[0].message.parsed
            else:
                # Fallback to JSON parsing
                content = response.choices[0].message.content
                if content:
                    import json
                    try:
                        eval_data = json.loads(content)
                        # Convert to InvestigationEvaluation object
                        evaluation = InvestigationEvaluation(
                            relevance_score=eval_data.get('relevance_score', 5.0),
                            information_value=eval_data.get('information_value', 5.0),
                            key_insights=eval_data.get('key_insights', []),
                            remaining_gaps=eval_data.get('remaining_gaps', []),
                            should_continue=eval_data.get('should_continue', True)
                        )
                    except json.JSONDecodeError as e:
                        raise RuntimeError(f"Failed to parse JSON evaluation: {e}")
                else:
                    # FAIL FAST - No fallback!
                    raise RuntimeError("LLM returned no evaluation content. Check LiteLLM configuration and API key.")
            
            # Update graph with evaluation results (for both successful parsing paths)
            self._update_graph_with_evaluation(results, evaluation)
            
            return evaluation
                
        except Exception as e:
            self.logger.error(f"Error in evaluate_batch_results: {e}")
            # FAIL FAST - No fallback!
            raise RuntimeError(f"LLM batch evaluation failed: {e}") from e
    
    def detect_emergent_questions(self, insights: List[Any]) -> List[EmergentQuestion]:
        """
        Detect emergent questions from insights and contradictions
        
        EVIDENCE REQUIREMENT: Must spawn new questions from discoveries
        """
        try:
            # Create emergent question detection prompt
            prompt = self._create_emergent_question_prompt(insights)
            
            # Get LLM analysis with structured output
            model = self.model_manager.get_model_for_operation("emergent_questions")
            response = self.llm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=EmergentQuestions
            )
            
            # Parse structured response - use .parsed if available, fallback to manual parsing
            emergent_questions = []
            if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                # New structured output format
                parsed_response = response.choices[0].message.parsed
                questions_list = parsed_response.questions if hasattr(parsed_response, 'questions') else []
                priority_scores = parsed_response.priority_scores if hasattr(parsed_response, 'priority_scores') else []
                
                for i, question_obj in enumerate(questions_list):
                    priority = priority_scores[i] if i < len(priority_scores) else 0.5
                    
                    # question_obj is now an EmergentQuestion object, not a dict
                    emergent_q = EmergentQuestion(
                        text=question_obj.text if hasattr(question_obj, 'text') else str(question_obj),
                        emergence_reason=question_obj.reason if hasattr(question_obj, 'reason') else "Emergent from insights",
                        priority=priority
                    )
                    emergent_questions.append(emergent_q)
                    
                    # Add to graph
                    self.graph.create_emergent_question_node(emergent_q.text, emergent_q.emergence_reason)
            else:
                # Fallback to JSON parsing
                content = response.choices[0].message.content
                if content:
                    import json
                    try:
                        questions_data = json.loads(content)
                        questions_list = questions_data.get("questions", [])
                        priority_scores = questions_data.get("priority_scores", [])
                        
                        for i, question_dict in enumerate(questions_list):
                            priority = priority_scores[i] if i < len(priority_scores) else 0.5
                            
                            emergent_q = EmergentQuestion(
                                text=question_dict.get("text", ""),
                                emergence_reason=question_dict.get("reason", ""),
                                priority=priority
                            )
                            emergent_questions.append(emergent_q)
                            
                            # Add to graph
                            self.graph.create_emergent_question_node(emergent_q.text, emergent_q.emergence_reason)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse emergent questions JSON: {e}")
                        # Return empty list instead of failing
                else:
                    self.logger.warning("No content in emergent questions response")
            
            return emergent_questions
            
        except Exception as e:
            self.logger.error(f"Error in detect_emergent_questions: {e}")
            return []
    
    def synthesize_current_understanding(self) -> UnderstandingSynthesis:
        """
        Build progressive understanding from graph state
        
        EVIDENCE REQUIREMENT: Must build coherent understanding narrative  
        """
        try:
            # Collect evidence from graph
            insights = self.graph.get_nodes_by_type("Insight")
            data_points = self.graph.get_nodes_by_type("DataPoint")
            answered_questions = self.graph.get_answered_questions()
            
            # Create synthesis prompt
            prompt = self._create_synthesis_prompt(insights, data_points, answered_questions)
            
            # Get LLM synthesis with structured output
            model = self.model_manager.get_model_for_operation("insight_synthesizer")
            response = self.llm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format=ContextSynthesis
            )
            
            # Parse structured response - use .parsed if available, fallback to manual parsing
            if hasattr(response.choices[0].message, 'parsed') and response.choices[0].message.parsed:
                # New structured output format - but ContextSynthesis might not match UnderstandingSynthesis exactly
                parsed_response = response.choices[0].message.parsed
                
                # Map ContextSynthesis to UnderstandingSynthesis
                return UnderstandingSynthesis(
                    current_understanding=getattr(parsed_response, 'current_understanding', ''),
                    confidence_level=getattr(parsed_response, 'confidence_level', 0.5),
                    key_findings=getattr(parsed_response, 'key_findings', []),
                    critical_gaps=getattr(parsed_response, 'critical_gaps', []),
                    investigation_completeness=getattr(parsed_response, 'investigation_completeness', 0.5),
                    next_priorities=getattr(parsed_response, 'next_priorities', [])
                )
            else:
                # Fallback to JSON parsing
                content = response.choices[0].message.content
                if content:
                    import json
                    try:
                        synthesis_data = json.loads(content)
                        
                        return UnderstandingSynthesis(
                            current_understanding=synthesis_data.get("current_understanding", ""),
                            confidence_level=synthesis_data.get("confidence_level", 0.5),
                            key_findings=synthesis_data.get("key_findings", []),
                            critical_gaps=synthesis_data.get("critical_gaps", []),
                            investigation_completeness=synthesis_data.get("investigation_completeness", 0.5),
                            next_priorities=synthesis_data.get("next_priorities", [])
                        )
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse synthesis JSON: {e}")
                        # Return empty synthesis instead of failing
                        return UnderstandingSynthesis(
                            current_understanding="",
                            confidence_level=0.0,
                            key_findings=[],
                            critical_gaps=[],
                            investigation_completeness=0.0,
                            next_priorities=[]
                        )
                else:
                    # FAIL FAST - No fallback!
                    raise RuntimeError("LLM returned no understanding synthesis content. Check LiteLLM configuration and API key.")
                
        except Exception as e:
            self.logger.error(f"Error in synthesize_current_understanding: {e}")
            # FAIL FAST - No fallback!
            raise RuntimeError(f"LLM understanding synthesis failed: {e}") from e
    
    def _get_endpoint_usage_report(self) -> str:
        """Generate endpoint usage report for diversity awareness"""
        if not self.diversity_tracker.endpoint_usage:
            return "No endpoints used yet - all endpoints available!"
        
        report_lines = []
        report_lines.append("Current endpoint usage:")
        for endpoint, count in sorted(self.diversity_tracker.endpoint_usage.items(), key=lambda x: x[1], reverse=True):
            status = " [OVERUSED - AVOID!]" if count >= 3 else ""
            report_lines.append(f"- {endpoint}: {count} times{status}")
        
        unused = self.diversity_tracker.get_unused_endpoints()
        if unused:
            report_lines.append(f"\nUnused endpoints (PREFER THESE): {', '.join(unused[:5])}")
        
        diversity_score = self.diversity_tracker.calculate_diversity_score()
        report_lines.append(f"\nDiversity score: {diversity_score:.2f} (target: >0.5)")
        
        return "\n".join(report_lines)
    
    def _extract_available_tweet_ids(self) -> str:
        """Extract tweet IDs from graph data points to provide context for dependent searches"""
        tweet_ids = []
        
        try:
            # Get data points from graph that contain tweet data
            data_points = self.graph.get_nodes_by_type("DataPoint")
            
            for dp in data_points:
                source_info = dp.properties.get('source_info', {})
                content = dp.properties.get('content', '')
                
                # Extract tweet ID from source info - check multiple fields
                if isinstance(source_info, dict):
                    # Check various possible ID fields
                    tweet_id = (source_info.get('id') or 
                               source_info.get('tweet_id') or
                               source_info.get('rest_id') or
                               source_info.get('id_str'))
                    
                    if tweet_id and tweet_id != 'unknown' and str(tweet_id).strip():
                        tweet_ids.append(f"- {tweet_id} (from {source_info.get('source', 'unknown')})")
                
                # Also check if content contains structured data
                if content and isinstance(content, str):
                    import re
                    # More comprehensive ID patterns
                    id_patterns = [
                        r'"id":\s*"(\d{15,})"',  # JSON format with long IDs
                        r'"rest_id":\s*"(\d{15,})"',  # REST ID format
                        r'"id_str":\s*"(\d{15,})"',  # ID string format
                        r'id["\']?\s*:\s*["\']?(\d{15,})',  # Various ID patterns
                        r'tweet_id["\']?\s*:\s*["\']?(\d{15,})',  # Tweet ID patterns
                    ]
                    
                    for pattern in id_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if len(match) >= 15:  # Twitter IDs are typically 15+ chars
                                tweet_ids.append(f"- {match} (extracted from content)")
                                break  # Only take first match per pattern per datapoint
                        if matches:  # If we found matches with this pattern, move to next datapoint
                            break
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tweet_ids = []
            for tid in tweet_ids:
                id_part = tid.split(' ')[1]  # Extract just the ID number
                if id_part not in seen:
                    seen.add(id_part)
                    unique_tweet_ids.append(tid)
                            
            if unique_tweet_ids:
                return "\n".join(unique_tweet_ids[:10])  # Limit to 10 most recent
            else:
                return "No tweet IDs available from previous searches - suggest using search queries instead of specific ID-dependent operations"
                
        except Exception as e:
            self.logger.error(f"Error extracting tweet IDs: {e}")
            return "Error extracting tweet IDs from context - suggest using search queries instead"
    
    def _extract_available_user_data(self) -> str:
        """Extract user data from graph data points to provide context for user-related searches"""
        user_data = []
        
        try:
            # Get data points from graph that contain user data
            data_points = self.graph.get_nodes_by_type("DataPoint")
            
            for dp in data_points:
                source_info = dp.properties.get('source_info', {})
                content = dp.properties.get('content', '')
                
                # Extract usernames from source info
                if isinstance(source_info, dict):
                    username = source_info.get('username') or source_info.get('screenname')
                    if username:
                        user_data.append(f"- @{username}")
                
                # Try to extract usernames from content
                import re
                username_patterns = [
                    r'"screenname":\s*"([^"]+)"',  # JSON screenname
                    r'"username":\s*"([^"]+)"',    # JSON username
                    r'@([a-zA-Z0-9_]+)',           # @mentions
                ]
                
                for pattern in username_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        if len(match) > 2:  # Valid username length
                            user_data.append(f"- @{match}")
                            
            # Remove duplicates and limit
            unique_users = list(set(user_data))[:10]
            
            if unique_users:
                return "\n".join(unique_users)
            else:
                return "No user data available from previous searches"
                
        except Exception as e:
            self.logger.error(f"Error extracting user data: {e}")
            return "Error extracting user data from context"
    
    def _create_strategic_decision_prompt(self, goal: str, context: str) -> str:
        """Create prompt for strategic decision making"""
        json_structure = """{
  "decision_type": "gap_filling"|"thread_connecting"|"deep_dive"|"pivot",
  "reasoning": "Detailed explanation of strategic rationale",
  "searches": [
    {
      "endpoint": "search.php",
      "parameters": {
        "query": "specific search terms"
      },
      "reasoning": "Why this search addresses the strategy"
    },
    {
      "endpoint": "timeline.php",
      "parameters": {
        "screenname": "exact_twitter_username"
      },
      "reasoning": "Why this timeline is relevant"
    }
  ],
  "expected_outcomes": ["What this strategy should achieve", "Expected results"],
  "confidence": 0.8
}"""
        
        # Add rejection feedback if available
        rejection_info = ""
        if self.rejection_context:
            rejection_info = f"\nIMPORTANT FEEDBACK FROM PREVIOUS ROUND:\n{self.rejection_context}\n"
        
        # Add emergent questions for follow-up searches
        emergent_questions_info = ""
        if self.emergent_questions:
            questions_text = "\n".join(f"- {q}" for q in self.emergent_questions)
            emergent_questions_info = f"""
EMERGENT QUESTIONS TO EXPLORE:
{questions_text}

PRIORITY: These emergent questions should drive your search strategy. Design searches to explore and answer these specific questions.
"""
        
        # Include context information if available
        context_prompt = ""
        if self.context:
            context_prompt = f"""
INVESTIGATION CONTEXT:
- Goal: {self.context.analytic_question}
- Key Focus Areas: {', '.join(self.context.goal_keywords)}
- Scope: {self.context.investigation_scope}

IMPORTANT: All search strategies must stay relevant to the investigation goal.
Avoid searches that would find content unrelated to: {self.context.analytic_question}
"""

        # Extract available data for parameter resolution
        available_tweet_ids = self._extract_available_tweet_ids()
        available_user_data = self._extract_available_user_data()

        return f"""
You are an expert investigation strategist. Your goal: {goal}

{context_prompt}
COMPLETE INVESTIGATION CONTEXT:
{context}
{rejection_info}
{emergent_questions_info}
Based on this COMPLETE context, make the most strategically coherent decision for the next investigation round.

CRITICAL REQUIREMENTS:
1. Address the most important information gaps first
2. Build on successful patterns, avoid failed approaches  
3. **MANDATORY**: Use DIVERSE endpoints - DO NOT use only search.php
4. **DIVERSITY RULE**: Each batch MUST include at least 2-3 different endpoints
5. Create searches that complement each other
6. Ensure strategic coherence with overall investigation

ENDPOINT USAGE TRACKER:
{self._get_endpoint_usage_report()}

**DIVERSITY ENFORCEMENT**: If search.php has been used >3 times, you MUST use other endpoints!

Available endpoints - ALL 16 ENDPOINTS WITH COMPLETE PARAMETERS:

**Content Discovery & Search:**
- search.php: REQUIRED[query] OPTIONAL[cursor, search_type] | search_type: Top/Latest/Media/People/Lists
- trends.php: REQUIRED[country] | country format: UnitedStates (one word)

**User Profile & Timeline:**
- timeline.php: REQUIRED[screenname] OPTIONAL[rest_id, cursor] | Recent posts chronologically
- screenname.php: REQUIRED[screenname] OPTIONAL[rest_id] | Profile info, follower counts
- usermedia.php: REQUIRED[screenname] OPTIONAL[rest_id, cursor] | User's photos/videos

**Network Analysis:**
- following.php: REQUIRED[screenname] OPTIONAL[cursor, rest_id] | Who user follows
- followers.php: REQUIRED[screenname] OPTIONAL[cursor] | Who follows user
- affilates.php: REQUIRED[screenname] OPTIONAL[cursor] | User affiliations
- checkfollow.php: REQUIRED[user, follows] | Verify follow relationship
- screennames.php: REQUIRED[rest_ids] | Bulk user profile lookup

**Tweet & Conversation Analysis:**
- tweet.php: REQUIRED[id] | Individual tweet with full metadata
- latest_replies.php: REQUIRED[id] OPTIONAL[cursor] | Replies to specific tweet
- tweet_thread.php: REQUIRED[id] OPTIONAL[cursor] | Complete conversation thread
- retweets.php: REQUIRED[id] OPTIONAL[cursor] | Who retweeted specific tweet
- checkretweet.php: REQUIRED[screenname, tweet_id] | Check if user retweeted

**List Analysis:**
- listtimeline.php: REQUIRED[list_id] OPTIONAL[cursor] | Timeline from Twitter list

**STRATEGIC IMPERATIVE: Use diverse endpoints for comprehensive investigation. Network endpoints reveal associations. Conversation endpoints show reactions and discussions. Tweet analysis provides deep context. Profile endpoints verify credibility.**

**CRITICAL PARAMETER REQUIREMENTS - ABSOLUTELY MANDATORY:**

✅ PARAMETER REQUIREMENTS - USE CONCRETE VALUES ONLY:
- Use actual usernames: "elonmusk", "reuters", "nasa"
- Use real search terms: "climate change policy", "AI safety"  
- Use specific tweet IDs from available context data when needed
- If specific IDs are not available in context, design searches that don't require them

**AVAILABLE TWEET IDs FROM PREVIOUS SEARCHES:**
{available_tweet_ids}

**AVAILABLE USER DATA FROM PREVIOUS SEARCHES:**
{available_user_data}

**VALIDATION**: Every parameter value must be ready to send to the API immediately without replacement.

Return a strategic decision with EXACT JSON structure:
{json_structure}

CRITICAL: Each search MUST have "endpoint" and "parameters" with appropriate parameter names for that endpoint.
All parameter VALUES must be concrete and usable - NO PLACEHOLDERS!

**COMPREHENSIVE ENDPOINT PARAMETER GUIDE:**

**CONTENT DISCOVERY:**
**search.php** - TARGETED SEARCHES:
- REQUIRED: query | OPTIONAL: cursor, search_type
- search_type VALUES: "Top", "Latest", "Media", "People", "Lists"
- ADVANCED QUERY OPERATORS:
  - User posts about topic: "from:elonmusk tesla"
  - User mentions: "@nasa space exploration"
  - Boolean logic: "climate change (solution OR policy OR action)"
  - Exclusions: "apple -fruit -food"
  - Exact phrases: "artificial intelligence"
- EXAMPLES: query="from:reuters breaking news", search_type="Latest"

**trends.php** - TRENDING TOPICS:
- REQUIRED: country | FORMAT: Must be single word like "UnitedStates"
- EXAMPLES: country="UnitedStates", country="Canada"

**USER ANALYSIS:**
**timeline.php** - USER'S RECENT POSTS:
- REQUIRED: screenname | OPTIONAL: rest_id, cursor
- LIMITATION: No topic filtering - chronological posts only
- EXAMPLES: screenname="reuters"

**screenname.php** - USER PROFILE:
- REQUIRED: screenname | OPTIONAL: rest_id
- EXAMPLES: screenname="nasa"

**usermedia.php** - USER'S MEDIA:
- REQUIRED: screenname | OPTIONAL: rest_id, cursor
- EXAMPLES: screenname="natgeo", cursor="next_page_token"

**NETWORK ANALYSIS:**
**following.php** - WHO USER FOLLOWS:
- REQUIRED: screenname | OPTIONAL: cursor, rest_id
- EXAMPLES: screenname="techcrunch", cursor="pagination_token"

**followers.php** - WHO FOLLOWS USER:
- REQUIRED: screenname | OPTIONAL: cursor
- EXAMPLES: screenname="bloomberg"

**affilates.php** - USER AFFILIATIONS:
- REQUIRED: screenname | OPTIONAL: cursor
- EXAMPLES: screenname="stanford"

**checkfollow.php** - VERIFY RELATIONSHIP:
- REQUIRED: user, follows (both usernames)
- EXAMPLES: user="elonmusk", follows="nasa"

**screennames.php** - BULK USER LOOKUP:
- REQUIRED: rest_ids (comma-separated Twitter user IDs)
- EXAMPLES: rest_ids="123456789,987654321"

**CONVERSATION ANALYSIS:**
**tweet.php** - SINGLE TWEET DETAILS:
- REQUIRED: id (tweet ID)
- EXAMPLES: id="1234567890123456789"

**latest_replies.php** - REPLIES TO TWEET:
- REQUIRED: id (tweet ID) | OPTIONAL: cursor
- EXAMPLES: id="1234567890123456789", cursor="reply_cursor"

**tweet_thread.php** - FULL CONVERSATION:
- REQUIRED: id (tweet ID) | OPTIONAL: cursor
- EXAMPLES: id="1234567890123456789"

**retweets.php** - WHO RETWEETED:
- REQUIRED: id (tweet ID) | OPTIONAL: cursor
- EXAMPLES: id="1234567890123456789"

**checkretweet.php** - VERIFY RETWEET:
- REQUIRED: screenname, tweet_id
- EXAMPLES: screenname="cnn", tweet_id="1234567890123456789"

**LIST ANALYSIS:**
**listtimeline.php** - LIST CONTENT:
- REQUIRED: list_id | OPTIONAL: cursor
- EXAMPLES: list_id="987654321"

**STRATEGIC PARAMETER USAGE:**
- Targeted user content: search.php with "from:username topic"
- User's recent activity: timeline.php with screenname
- Network mapping: following.php + followers.php for connections
- Conversation analysis: tweet.php → latest_replies.php for full context
- Verification: checkfollow.php, checkretweet.php for relationship validation
"""

    def _create_evaluation_prompt(self, goal: str, results: List[Dict]) -> str:
        """Create prompt for batch result evaluation"""
        
        # Format results for evaluation
        results_text = []
        for i, result in enumerate(results[:20]):  # Limit for prompt size
            text_content = result.get('text', result.get('content', str(result)))[:200]
            results_text.append(f"{i+1}. {text_content}...")
        
        return f"""
Evaluate these search results for investigation: {goal}

RESULTS TO EVALUATE:
{chr(10).join(results_text)}

Rate HONESTLY based on semantic relevance to the investigation goal:

1. Relevance Score (0-10): How directly related to "{goal}"?
   - 0-1: Completely unrelated (like "save money" for "Trump Epstein")
   - 2-4: Tangentially related but not useful
   - 5-7: Somewhat relevant, some useful information
   - 8-10: Highly relevant, directly addresses investigation

2. Information Value (0-10): How much does this advance understanding?

Extract key insights that actually advance the investigation.
Identify remaining information gaps after reviewing these results.

Be brutally honest about relevance - don't inflate scores.
"""

    def _create_emergent_question_prompt(self, insights: List[Any]) -> str:
        """Create prompt for emergent question detection"""
        
        insights_text = []
        for insight in insights[:10]:  # Limit for prompt size
            if hasattr(insight, 'content'):
                insights_text.append(f"- {insight.content}")
            else:
                insights_text.append(f"- {str(insight)}")
        
        return f"""
Analyze these insights for contradictions, gaps, or new investigation directions:

INSIGHTS:
{chr(10).join(insights_text)}

Identify emergent questions that arise from:
1. Contradictions between insights
2. Unexpected findings that require explanation
3. Gaps revealed by current understanding
4. New investigation directions suggested by evidence

For each emergent question, explain why it emerged and rate its priority (0-1).

Return as structured data with questions array and priority scores.
"""

    def _create_synthesis_prompt(self, insights: List[Any], data_points: List[Any], answered_questions: List[Any]) -> str:
        """Create prompt for understanding synthesis"""
        
        return f"""
Synthesize current understanding of the investigation based on accumulated evidence:

INSIGHTS: {len(insights)} insights generated
DATA POINTS: {len(data_points)} data points collected  
ANSWERED QUESTIONS: {len(answered_questions)} questions addressed

Based on this evidence, provide:
1. current_understanding: Comprehensive summary of what we know
2. confidence_level: 0.0-1.0 confidence in findings
3. key_findings: Most important discoveries
4. critical_gaps: Highest priority missing information
5. investigation_completeness: 0.0-1.0 how complete the investigation is
6. next_priorities: What to focus on next

Focus on building a coherent narrative from the evidence while acknowledging uncertainties.
"""

    def _calculate_coherence_score(self, decision: StrategicDecision) -> float:
        """Calculate strategic coherence score for a decision"""
        
        score = 0.5  # Base score
        
        # Higher score for addressing gaps
        gaps = self.graph.get_information_gaps()
        if gaps and any(gap_keyword in decision.reasoning.lower() 
                       for gap in gaps[:3] 
                       for gap_keyword in gap.lower().split()[:3]):
            score += 0.2
        
        # Higher score for avoiding failed patterns  
        failed_patterns = self.graph.get_failed_patterns()
        avoids_failures = True
        for pattern in failed_patterns:
            pattern_query = pattern.split("'")[1] if "'" in pattern else pattern.lower()
            for search in decision.searches:
                if search is None or not hasattr(search, 'parameters') or not search.parameters:
                    continue
                search_query = search.parameters.query if search.parameters.query else ""
                if pattern_query in search_query.lower():
                    avoids_failures = False
                    break
        
        if avoids_failures and failed_patterns:
            score += 0.2
        
        # Higher score for using appropriate endpoints
        if decision.searches:
            endpoint_appropriateness = 0
            valid_searches = 0
            for search in decision.searches:
                if search is None:
                    continue
                valid_searches += 1
                endpoint = search.endpoint if hasattr(search, 'endpoint') else None
                if endpoint and endpoint in self.available_endpoints:
                    endpoint_appropriateness += 1
            if valid_searches > 0:
                score += (endpoint_appropriateness / valid_searches) * 0.1
        
        return min(1.0, score)
    
    def _update_graph_with_decision(self, decision: StrategicDecision):
        """Update graph with strategic decision nodes - maintains connectivity"""
        
        # Defensive check for None or empty searches
        if not decision or not decision.searches:
            self.logger.warning("No searches in strategic decision to update graph with")
            return
        
        # Create investigation questions if not exist
        for search in decision.searches:
            # Skip None entries
            if search is None:
                self.logger.warning("Skipping None search in decision.searches")
                continue
            
            try:
                    reasoning = search.reasoning if search.reasoning else "Strategic search"
                    
                    # Create investigation question based on search reasoning
                    question_text = f"Strategic question: {reasoning}"
                    inv_question = self.graph.create_investigation_question_node(question_text)
                    
                    # CRITICAL: Connect investigation question to analytic question to maintain connectivity
                    if self.graph.analytic_question:
                        try:
                            self.graph.create_edge(
                                self.graph.analytic_question, 
                                inv_question, 
                                "MOTIVATES", 
                                {"decision_type": decision.decision_type}
                            )
                        except ValueError as edge_error:
                            self.logger.error(f"Failed to create edge: {edge_error}")
                    
                    # Create search query node (convert SearchParameters to dict)
                    params_dict = {}
                    if hasattr(search, 'parameters') and search.parameters:
                        # Extra validation for parameters object
                        if hasattr(search.parameters, 'model_dump'):
                            try:
                                params_dict = {k: v for k, v in search.parameters.model_dump().items() if v is not None}
                                
                                # CRITICAL: Validate parameters for placeholders
                                placeholder_errors = self._validate_no_placeholders(params_dict)
                                if placeholder_errors:
                                    self.logger.error(f"PLACEHOLDER VALIDATION FAILED: {placeholder_errors}")
                                    # Skip this search to prevent API failures
                                    continue
                                    
                            except Exception as param_error:
                                self.logger.error(f"Error dumping search parameters: {param_error}")
                                params_dict = {}
                        else:
                            self.logger.warning(f"Invalid parameters object type: {type(search.parameters)}")
                            params_dict = {}
                    
                    search_node = self.graph.create_search_query_node(
                        search.endpoint if search.endpoint else 'search.php',
                        params_dict
                    )
                    
                    # Link question to search
                    try:
                        edge_properties = {"decision_type": decision.decision_type}
                        # Add coherence score if available (enhanced decision only)
                        if hasattr(decision, 'strategic_coherence_score'):
                            edge_properties["coherence_score"] = decision.strategic_coherence_score
                        
                        self.graph.create_edge(inv_question, search_node, "OPERATIONALIZES", edge_properties)
                    except ValueError as edge_error:
                        self.logger.error(f"Failed to create search edge: {edge_error}")
                    
            except Exception as e:
                self.logger.error(f"Error updating graph with search: {e}")
                import traceback
                self.logger.error(f"Traceback: {traceback.format_exc()}")
                continue
    
    def _update_graph_with_evaluation(self, results: List[Dict], evaluation: InvestigationEvaluation):
        """Update graph with evaluation results - maintains connectivity"""
        
        # Find the most recent search query node to connect data points to
        search_nodes = self.graph.get_nodes_by_type("SearchQuery")
        recent_search = search_nodes[-1] if search_nodes else None
        
        # Add high-value results as data points
        created_data_points = []
        if evaluation.relevance_score >= 6.0:
            for result in results[:5]:  # Limit to top results
                content = result.get('text', result.get('content', str(result)))
                source_info = {
                    'source': result.get('source', 'unknown'),
                    'relevance_score': evaluation.relevance_score,
                    'timestamp': datetime.now().isoformat()
                }
                data_point = self.graph.create_data_point_node(content[:500], source_info)
                created_data_points.append(data_point)
                
                # Connect data point to search query that generated it
                if recent_search:
                    self.graph.create_edge(recent_search, data_point, "GENERATES", {
                        "relevance_score": evaluation.relevance_score
                    })
        
        # Add insights to graph and connect to data points
        for insight_text in evaluation.key_insights:
            insight = self.graph.create_insight_node(insight_text, "evaluation_derived")
            
            # CRITICAL: Add missing properties to evaluation-derived insights to prevent "Untitled" display
            # Generate a title from the content (first 6 words + ellipsis if longer)
            words = insight_text.split()[:6]
            title = ' '.join(words)
            if len(insight_text.split()) > 6:
                title += "..."
            
            # Add properties consistent with real-time synthesis insights
            insight.properties['title'] = title
            insight.properties['confidence'] = 0.7  # Reasonable default for evaluation-derived insights
            insight.properties['investigation_relevance'] = evaluation.relevance_score / 10.0  # Convert 0-10 to 0-1
            insight.properties['key_evidence'] = [insight_text[:200]]  # First 200 chars as evidence
            
            # Connect insights to data points that support them
            for data_point in created_data_points:
                self.graph.create_edge(data_point, insight, "SUPPORTS", {
                    "confidence": 0.8
                })
    
    def _select_endpoint_with_diversity(self, goal: str, endpoint_usage: Dict[str, int]) -> Tuple[str, str]:
        """
        Select endpoint with diversity enforcement
        
        Returns: (endpoint, reasoning)
        """
        # Check if any endpoint is overused
        overused = self.diversity_tracker.get_overused_endpoints(threshold=3)
        unused = self.diversity_tracker.get_unused_endpoints()
        
        # If we have unused endpoints, prefer them
        if unused and overused:
            # Force diversity by suggesting unused endpoints
            suggested = self.diversity_tracker.suggest_next_endpoint(goal)
            if suggested != "search.php" or "search.php" not in overused:
                return suggested, f"Diversifying endpoints - using {suggested} for better coverage"
        
        # Otherwise use normal selection but with diversity awareness
        selected = self._select_endpoint(goal, str(endpoint_usage))
        endpoint = selected.get("endpoint", "search.php")
        
        # Override if endpoint is overused
        if endpoint in overused and unused:
            alternative = unused[0]
            return alternative, f"Overriding {endpoint} (used {self.diversity_tracker.get_usage_count(endpoint)} times) with {alternative} for diversity"
        
        return endpoint, selected.get("reasoning", "Selected based on goal match")
    
    def _suggest_endpoint_for_need(self, query: str) -> str:
        """Map investigation needs to appropriate endpoints"""
        query_lower = query.lower()
        
        # Map query patterns to endpoints
        if any(word in query_lower for word in ["@", "user said", "what did", "timeline"]):
            return "timeline.php"
        elif any(word in query_lower for word in ["profile", "who is", "screenname"]):
            return "screenname.php"
        elif any(word in query_lower for word in ["follows", "following", "connections"]):
            return "follows.php"
        elif any(word in query_lower for word in ["followers", "audience", "who follows"]):
            return "followers.php"
        elif any(word in query_lower for word in ["trending", "trends", "popular now"]):
            return "trends.php"
        elif any(word in query_lower for word in ["conversation", "discussion", "mentions"]):
            return "mentions.php"
        elif any(word in query_lower for word in ["replies", "responses", "comments"]):
            return "replies.php"
        else:
            return "search.php"
    
    def _select_endpoint(self, goal: str, context: str) -> dict:
        """
        Select the best endpoint for a specific goal - focused decision
        
        EVIDENCE REQUIREMENT: Simplified prompt for better endpoint selection
        """
        # Create focused endpoint selection prompt
        prompt = f"""You are an expert Twitter investigation strategist. 
Your task: Select the BEST endpoint for this specific goal.

GOAL: {goal}
CONTEXT: {context}

AVAILABLE ENDPOINTS (choose ONE):
1. search.php - General search across all Twitter
2. timeline.php - Get specific user's tweets (requires: screenname)
3. screenname.php - Get user profile info (requires: screenname)
4. followers.php - Get who follows a user (requires: screenname)
5. following.php - Get who a user follows (requires: screenname)
6. tweet.php - Get specific tweet details (requires: id)
7. latest_replies.php - Get replies to a tweet (requires: id)
8. retweets.php - Get who retweeted (requires: id)
9. trends.php - Get trending topics (requires: country)

Return ONLY valid JSON (no other text):
{{
  "endpoint": "selected_endpoint.php",
  "reasoning": "Why this endpoint best serves the goal",
  "required_params": ["list", "of", "required", "parameters"]
}}"""

        try:
            model = self.model_manager.get_model_for_operation("strategic_coordinator")
            response = self.llm.simple_completion(
                model=model,
                prompt=prompt
            )
            
            # Parse JSON response (try to extract JSON even if there's extra text)
            import json
            import re
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in _select_endpoint: {e}")
            # Fallback to search.php
            return {
                "endpoint": "search.php",
                "reasoning": "Fallback to general search",
                "required_params": ["query"]
            }
    
    def _formulate_query(self, endpoint: str, goal: str, endpoint_params: dict) -> dict:
        """
        Formulate query parameters for a specific endpoint - focused decision
        
        EVIDENCE REQUIREMENT: Endpoint-specific query formulation
        """
        required = endpoint_params.get('required', [])
        optional = endpoint_params.get('optional', [])
        
        # Create focused query formulation prompt
        prompt = f"""You are formulating parameters for the {endpoint} endpoint.

GOAL: {goal}
ENDPOINT: {endpoint}
REQUIRED PARAMETERS: {required}
OPTIONAL PARAMETERS: {optional}

PARAMETER GUIDELINES:
- screenname: Twitter username without @ (e.g., "elonmusk", "NASA")
- query: Search terms with operators (e.g., "from:elonmusk tesla", "climate change")
- id/tweet_id: Numeric tweet ID
- country: Single word (e.g., "UnitedStates", "Canada")
- cursor: Leave empty for first page
- search_type: One of "Top", "Latest", "Media", "People", "Lists"

Return ONLY valid JSON with the exact parameters needed (no other text):
{{
  "parameter_name": "parameter_value"
}}"""

        try:
            model = self.model_manager.get_model_for_operation("strategic_coordinator")
            response = self.llm.simple_completion(
                model=model,
                prompt=prompt
            )
            
            # Parse JSON response (try to extract JSON even if there's extra text)
            import json
            import re
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in _formulate_query: {e}")
            # Return empty parameters
            return {}
    
    def _validate_no_placeholders(self, params_dict: Dict[str, Any]) -> List[str]:
        """
        Validate that parameters contain no placeholder values
        
        Returns: List of error messages for any placeholders found
        """
        errors = []
        
        # Define placeholder patterns to detect
        placeholder_patterns = [
            r'REPLACE_WITH_[A-Z_]+',       # REPLACE_WITH_TWEET_ID_FROM_TIMELINE
            r'<[A-Za-z_]+>',               # <username>, <tweet_id>
            r'\{[A-Za-z_]+\}',             # {placeholder}
            r'\[[A-Za-z_\s]+\]',           # [placeholder text]
            r'TODO[:\s]',                  # TODO: something
            r'INSERT_[A-Z_]+',             # INSERT_VALUE_HERE
            r'example_[a-z_]+',            # example_value
            r'sample_[a-z_]+',             # sample_id
            r'placeholder_[a-z_]+',        # placeholder_text
        ]
        
        import re
        
        # Check each parameter value
        for param_name, param_value in params_dict.items():
            if not isinstance(param_value, str):
                continue
                
            # Check against all placeholder patterns
            for pattern in placeholder_patterns:
                if re.search(pattern, param_value, re.IGNORECASE):
                    errors.append(f"Parameter '{param_name}' contains placeholder: '{param_value}'")
                    break
            
            # Check for specific placeholder patterns (more precise detection)
            specific_placeholder_indicators = [
                'replace_with',
                'insert_here', 
                'todo:',
                'example_',
                'sample_',
                'your_',
                'user_id_here',
                'tweet_id_here'
            ]
            param_lower = param_value.lower()
            for indicator in specific_placeholder_indicators:
                if indicator in param_lower:
                    errors.append(f"Parameter '{param_name}' contains placeholder pattern: '{param_value}'")
                    break
        
        return errors

    def _enforce_parameter_validation(self, decision: StrategicDecision) -> StrategicDecision:
        """
        Enforce parameter validation and prevent any placeholders from reaching API calls
        
        Returns: Validated decision with placeholder searches removed
        """
        validated_searches = []
        
        for search in decision.searches:
            try:
                # Convert search parameters to dict for validation
                if hasattr(search.parameters, '__dict__'):
                    params_dict = search.parameters.__dict__
                elif hasattr(search.parameters, 'model_dump'):
                    params_dict = search.parameters.model_dump()
                else:
                    params_dict = {}
                
                # Run validation
                validation_errors = self._validate_no_placeholders(params_dict)
                
                if validation_errors:
                    self.logger.error(f"CRITICAL: Blocked placeholder parameters in {search.endpoint}: {validation_errors}")
                    self.logger.error(f"CRITICAL: Parameters were: {params_dict}")
                    # Skip this search entirely - do not allow placeholders to reach API
                    continue
                else:
                    validated_searches.append(search)
                    
            except Exception as e:
                self.logger.error(f"Error validating search parameters: {e}")
                # If validation fails, be safe and skip the search
                continue
        
        # Return decision with only validated searches
        if len(validated_searches) < len(decision.searches):
            self.logger.warning(f"Removed {len(decision.searches) - len(validated_searches)} searches due to placeholder parameters")
        
        # Create new decision with validated searches - preserve ALL required fields
        validated_decision = StrategicDecision(
            decision_type=decision.decision_type,
            reasoning=decision.reasoning,
            searches=validated_searches,
            expected_outcomes=getattr(decision, 'expected_outcomes', []),
            confidence=getattr(decision, 'confidence', 0.8),
            context_utilization=getattr(decision, 'context_utilization', 0.8),
            strategic_coherence_score=getattr(decision, 'strategic_coherence_score', 0.8)
        )
        
        return validated_decision
    
