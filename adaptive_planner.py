# adaptive_planner.py
from typing import Dict, List, Any, Optional
import json
import re
from dataclasses import asdict

# Import existing modules
import llm_handler
from investigation_engine import InvestigationSession, SearchAttempt

class AdaptivePlanner:
    """Intelligent search strategy planner that learns from previous results"""
    
    def __init__(self):
        self.strategy_templates = {
            'direct_search': {
                'description': 'Direct name search with debunking terms',
                'effective_for': ['specific_person', 'explicit_claims'],
                'search_patterns': [
                    '"{name}" debunked',
                    '"{name}" hoax', 
                    '"{name}" false',
                    '"{name}" fact check'
                ]
            },
            'contextual_search': {
                'description': 'Broader topic search with critical analysis',
                'effective_for': ['general_topics', 'failed_direct_searches'],
                'search_patterns': [
                    'UFO whistleblower debunked',
                    'UFO disclosure hoax',
                    'fake UFO witness',
                    'UFO skeptic analysis'
                ]
            },
            'community_search': {
                'description': 'Search within skeptical communities',
                'effective_for': ['conspiracy_topics', 'pseudoscience'],
                'search_patterns': [
                    '#UFOSkeptic {topic}',
                    '#FactCheck {topic}',
                    'skeptical inquiry {topic}',
                    'debunk {topic}'
                ]
            },
            'alternative_spellings': {
                'description': 'Try name variations and alternative spellings',
                'effective_for': ['no_results_found', 'unusual_names'],
                'search_patterns': [
                    'variations_of_name',
                    'phonetic_spelling',
                    'abbreviated_forms'
                ]
            },
            'temporal_search': {
                'description': 'Search for recent vs historical discussions',
                'effective_for': ['time_sensitive_topics', 'recent_claims'],
                'search_patterns': [
                    '{topic} 2024',
                    '{topic} recent',
                    '{topic} latest',
                    '{topic} timeline'
                ]
            }
        }
    
    def generate_adaptive_strategy(self, session: InvestigationSession) -> Dict[str, Any]:
        """Generate intelligent search strategy based on investigation history"""
        
        # Analyze current situation
        situation = self._analyze_investigation_situation(session)
        
        # Select appropriate strategy
        strategy_type = self._select_strategy_type(situation, session)
        
        # Generate specific searches
        searches = self._generate_searches_for_strategy(strategy_type, session, situation)
        
        # Create enhanced prompt for LLM
        enhanced_prompt = self._create_enhanced_prompt(session, situation, strategy_type)
        
        # Get LLM refinement
        llm_response = self._get_llm_strategy_refinement(enhanced_prompt)
        
        # Combine our intelligence with LLM suggestions
        final_strategy = self._merge_strategies(searches, llm_response, strategy_type)
        
        return final_strategy
    
    def _analyze_investigation_situation(self, session: InvestigationSession) -> Dict[str, Any]:
        """Analyze current investigation state to inform strategy"""
        
        situation = {
            'total_searches': session.search_count,
            'total_results': session.total_results_found,
            'satisfaction_score': session.satisfaction_metrics.overall_satisfaction(),
            'has_results': session.total_results_found > 0,
            'recent_effectiveness': 0.0,
            'failed_approaches': session.dead_ends,
            'successful_approaches': session.promising_leads,
            'query_characteristics': self._analyze_query_characteristics(session.original_query)
        }
        
        # Calculate recent search effectiveness
        if session.search_history:
            recent_searches = session.search_history[-5:]  # Last 5 searches
            situation['recent_effectiveness'] = sum(s.effectiveness_score for s in recent_searches) / len(recent_searches)
        
        return situation
    
    def _analyze_query_characteristics(self, query: str) -> Dict[str, Any]:
        """Analyze the original query to understand what we're looking for"""
        
        query_lower = query.lower()
        
        characteristics = {
            'is_person_specific': bool(re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query)),
            'is_debunking_request': any(word in query_lower for word in 
                                      ['debunk', 'false', 'hoax', 'fake', 'disprove', 'refute']),
            'is_ufo_related': any(word in query_lower for word in 
                                 ['ufo', 'uap', 'alien', 'extraterrestrial', 'disclosure']),
            'is_whistleblower_related': 'whistleblower' in query_lower,
            'extracted_names': re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', query),
            'key_terms': [word for word in query_lower.split() if len(word) > 3]
        }
        
        return characteristics
    
    def _select_strategy_type(self, situation: Dict, session: InvestigationSession) -> str:
        """Select the most appropriate strategy type based on situation"""
        
        # If we haven't found anything yet, try broader approaches
        if not situation['has_results'] and situation['total_searches'] > 5:
            if situation['query_characteristics']['is_person_specific']:
                return 'alternative_spellings'
            else:
                return 'contextual_search'
        
        # If recent searches are ineffective, pivot strategy
        if situation['recent_effectiveness'] < 3.0:
            if len(situation['failed_approaches']) > 3:
                return 'community_search'
            else:
                return 'contextual_search'
        
        # If we found some results, drill deeper
        if situation['has_results'] and situation['satisfaction_score'] < 0.5:
            return 'temporal_search'
        
        # Default to direct search for new investigations
        if situation['total_searches'] < 5:
            return 'direct_search'
        
        return 'contextual_search'
    
    def _generate_searches_for_strategy(self, strategy_type: str, session: InvestigationSession, situation: Dict) -> List[Dict]:
        """Generate specific searches for the chosen strategy"""
        
        strategy_template = self.strategy_templates[strategy_type]
        searches = []
        
        query_chars = situation['query_characteristics']
        
        if strategy_type == 'direct_search':
            if query_chars['extracted_names']:
                name = query_chars['extracted_names'][0]
                patterns = [
                    f'"{name}" debunked',
                    f'"{name}" hoax',
                    f'"{name}" fact check',
                    f'"{name}" false claims'
                ]
            else:
                # Use key terms from query
                key_term = ' '.join(query_chars['key_terms'][:2])
                patterns = [
                    f'"{key_term}" debunked',
                    f'"{key_term}" hoax'
                ]
        
        elif strategy_type == 'contextual_search':
            if query_chars['is_ufo_related']:
                patterns = [
                    'UFO whistleblower debunked',
                    'UFO disclosure hoax',
                    'fake UFO witness credibility',
                    'UFO skeptic analysis'
                ]
            else:
                patterns = [
                    'whistleblower hoax',
                    'false witness testimony',
                    'conspiracy theory debunked'
                ]
        
        elif strategy_type == 'community_search':
            patterns = [
                '#UFOSkeptic whistleblower',
                '#FactCheck UFO claims',
                'skeptical inquiry UFO',
                'CSICOP UFO debunk'
            ]
        
        elif strategy_type == 'alternative_spellings':
            if query_chars['extracted_names']:
                name_parts = query_chars['extracted_names'][0].split()
                if len(name_parts) >= 2:
                    first, last = name_parts[0], name_parts[1]
                    patterns = [
                        f'"{first} {last}" debunked',  # Original
                        f'"{first[0]} {last}" hoax',   # First initial  
                        f'"{last}" UFO hoax',          # Last name only
                        f'"{first}" whistleblower false'  # First name only
                    ]
                else:
                    patterns = ['whistleblower hoax', 'UFO witness false']
            else:
                patterns = ['whistleblower hoax', 'UFO witness false']
        
        elif strategy_type == 'temporal_search':
            base_terms = query_chars['key_terms'][:2]
            patterns = [
                f'{" ".join(base_terms)} 2024',
                f'{" ".join(base_terms)} recent',
                f'{" ".join(base_terms)} latest news',
                f'{" ".join(base_terms)} current'
            ]
        
        else:
            patterns = ['UFO hoax', 'conspiracy debunked']
        
        # Convert patterns to search objects
        for i, pattern in enumerate(patterns[:4]):  # Max 4 searches per round
            searches.append({
                'step': i + 1,
                'endpoint': 'search.php',
                'params': {
                    'query': pattern,
                    'result_type': 'latest'
                },
                'reason': f'{strategy_template["description"]} - searching for: {pattern}',
                'max_pages': 3
            })
        
        return searches
    
    def _create_enhanced_prompt(self, session: InvestigationSession, situation: Dict, strategy_type: str) -> str:
        """Create enhanced prompt that includes our analysis"""
        
        context_parts = []
        context_parts.append(f"ORIGINAL QUERY: {session.original_query}")
        context_parts.append(f"SEARCHES COMPLETED: {situation['total_searches']}")
        context_parts.append(f"RESULTS FOUND: {situation['total_results']}")
        context_parts.append(f"SATISFACTION: {situation['satisfaction_score']:.1%}")
        
        if situation['failed_approaches']:
            context_parts.append(f"FAILED APPROACHES: {', '.join(situation['failed_approaches'][-3:])}")
        
        if situation['successful_approaches']:
            context_parts.append(f"SUCCESSFUL TERMS: {', '.join(situation['successful_approaches'][-3:])}")
        
        context_parts.append(f"RECOMMENDED STRATEGY: {strategy_type}")
        context_parts.append(f"QUERY ANALYSIS: {situation['query_characteristics']}")
        
        prompt = f"""
ITERATIVE INVESTIGATION - ADAPTIVE STRATEGY GENERATION

{chr(10).join(context_parts)}

Based on this analysis, generate 2-4 strategic Twitter searches that:

1. AVOID repeating failed approaches
2. BUILD ON successful patterns found
3. USE the recommended strategy type: {strategy_type}  
4. ADAPT search terms based on what we've learned
5. EXPLORE new angles if previous approaches failed

For debunking investigations, prioritize:
- Skeptical communities and fact-checkers
- Expert analysis and credibility assessments
- Alternative perspectives and critical voices
- Specific claim analysis rather than general mentions

Your searches should be strategic and build towards answering the original question.
"""
        
        return prompt
    
    def _get_llm_strategy_refinement(self, enhanced_prompt: str) -> Dict[str, Any]:
        """Get LLM strategy refinement"""
        
        try:
            # Use existing LLM handler
            llm_response = llm_handler.get_llm_plan(enhanced_prompt, "")
            return llm_response
        except Exception as e:
            print(f"LLM strategy refinement failed: {e}")
            return {'response_type': 'ERROR', 'message_to_user': 'Strategy refinement failed'}
    
    def _merge_strategies(self, our_searches: List[Dict], llm_response: Dict, strategy_type: str) -> Dict[str, Any]:
        """Merge our intelligent strategy with LLM suggestions"""
        
        # Start with our strategy
        final_strategy = {
            'description': f'{strategy_type.replace("_", " ").title()} - Adaptive Investigation Round',
            'searches': our_searches,
            'reasoning': f'Using {strategy_type} strategy based on investigation analysis'
        }
        
        # Enhance with LLM if available
        if llm_response.get('response_type') == 'PLAN':
            llm_searches = llm_response.get('api_plan', [])
            
            # Merge searches - prefer LLM refinements but keep our structure
            if llm_searches:
                # Take best of both - our intelligence + LLM creativity
                combined_searches = []
                
                # Start with our searches
                for search in our_searches[:2]:  # Take our top 2
                    combined_searches.append(search)
                
                # Add LLM searches that don't duplicate our terms
                our_queries = set(s['params']['query'].lower() for s in our_searches)
                
                for llm_search in llm_searches:
                    if len(combined_searches) >= 4:
                        break
                    
                    llm_query = llm_search.get('params', {}).get('query', '').lower()
                    if llm_query and llm_query not in our_queries:
                        # Reformat to match our structure
                        combined_searches.append({
                            'step': len(combined_searches) + 1,
                            'endpoint': llm_search.get('endpoint', 'search.php'),
                            'params': llm_search.get('params', {}),
                            'reason': llm_search.get('reason', 'LLM suggested search'),
                            'max_pages': llm_search.get('max_pages', 3)
                        })
                
                final_strategy['searches'] = combined_searches
                
            # Enhance description with LLM insights
            if llm_response.get('message_to_user'):
                final_strategy['reasoning'] = llm_response['message_to_user']
        
        return final_strategy
    
    def learn_from_results(self, session: InvestigationSession):
        """Learn from investigation results to improve future strategies"""
        
        # Analyze which search patterns were most effective
        effective_patterns = {}
        
        for search in session.search_history:
            if search.effectiveness_score > 6.0:  # Good results
                query = search.params.get('query', '')
                # Extract patterns (simple approach)
                words = query.lower().split()
                for word in words:
                    if len(word) > 3:
                        effective_patterns[word] = effective_patterns.get(word, 0) + search.effectiveness_score
        
        # Store learning (in a real implementation, this would persist)
        # For now, just log what we learned
        if effective_patterns:
            print(f"Learned effective terms: {dict(sorted(effective_patterns.items(), key=lambda x: x[1], reverse=True)[:5])}")
    
    def suggest_next_investigation_approaches(self, session: InvestigationSession) -> List[str]:
        """Suggest what to investigate next if current approaches aren't working"""
        
        suggestions = []
        
        if session.total_results_found == 0:
            suggestions.extend([
                "Try searching on different platforms (Reddit, YouTube, etc.)",
                "Search for the topic in academic or scientific databases", 
                "Look for mainstream media coverage of the claims",
                "Search for the person's background or credentials"
            ])
        
        elif session.satisfaction_metrics.overall_satisfaction() < 0.3:
            suggestions.extend([
                "Focus on specific claims rather than general debunking",
                "Search for expert opinions or analysis",
                "Look for primary sources or original documents",
                "Investigate the credibility of sources making claims"
            ])
        
        return suggestions