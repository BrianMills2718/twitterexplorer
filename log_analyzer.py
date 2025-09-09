# log_analyzer.py
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from collections import defaultdict, Counter
import statistics

class LogAnalyzer:
    """Analyze investigation logs to identify patterns and insights"""
    
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = Path(base_log_dir)
        
    def analyze_session_performance(self, session_id: Optional[str] = None, date: Optional[str] = None) -> Dict[str, Any]:
        """Analyze performance metrics for sessions"""
        
        sessions = self._load_sessions(session_id, date)
        if not sessions:
            return {"error": "No sessions found for analysis"}
        
        analysis = {
            "total_sessions": len(sessions),
            "average_duration": statistics.mean([s.get('duration_seconds', 0) for s in sessions]),
            "average_searches": statistics.mean([s.get('total_searches', 0) for s in sessions]),
            "average_results": statistics.mean([s.get('total_results', 0) for s in sessions]),
            "average_satisfaction": statistics.mean([s.get('satisfaction_score', 0) for s in sessions]),
            "completion_reasons": Counter([s.get('completion_reason', 'Unknown') for s in sessions]),
            "session_details": []
        }
        
        for session in sessions:
            analysis["session_details"].append({
                "session_id": session.get('session_id', 'Unknown'),
                "user_query": session.get('user_query', 'Unknown'),
                "duration_minutes": round(session.get('duration_seconds', 0) / 60, 1),
                "searches": session.get('total_searches', 0),
                "results": session.get('total_results', 0),
                "satisfaction": f"{session.get('satisfaction_score', 0):.1%}",
                "completion_reason": session.get('completion_reason', 'Unknown')
            })
        
        return analysis
    
    def analyze_search_effectiveness(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Analyze which search patterns are most effective"""
        
        searches = self._load_search_attempts(date)
        if not searches:
            return {"error": "No search data found for analysis"}
        
        # Group by query patterns
        query_effectiveness = defaultdict(list)
        endpoint_effectiveness = defaultdict(list)
        strategy_effectiveness = defaultdict(list)
        
        for search in searches:
            query = search.get('query', '').lower()
            effectiveness = search.get('effectiveness_score', 0)
            results = search.get('results_count', 0)
            
            query_effectiveness[query].append(effectiveness)
            endpoint_effectiveness[search.get('endpoint', 'unknown')].append(effectiveness)
            strategy_effectiveness[search.get('strategy_type', 'unknown')].append(effectiveness)
        
        # Calculate averages and insights
        analysis = {
            "total_searches": len(searches),
            "overall_avg_effectiveness": statistics.mean([s.get('effectiveness_score', 0) for s in searches]),
            "most_effective_queries": self._get_top_performers(query_effectiveness),
            "most_effective_endpoints": self._get_top_performers(endpoint_effectiveness),
            "most_effective_strategies": self._get_top_performers(strategy_effectiveness),
            "effectiveness_distribution": {
                "highly_effective": len([s for s in searches if s.get('effectiveness_score', 0) >= 8]),
                "moderately_effective": len([s for s in searches if 5 <= s.get('effectiveness_score', 0) < 8]),
                "low_effectiveness": len([s for s in searches if 2 <= s.get('effectiveness_score', 0) < 5]),
                "ineffective": len([s for s in searches if s.get('effectiveness_score', 0) < 2])
            }
        }
        
        return analysis
    
    def analyze_llm_performance(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Analyze LLM interaction patterns and performance"""
        
        interactions = self._load_llm_interactions(date)
        if not interactions:
            return {"error": "No LLM interaction data found"}
        
        # Group by interaction type
        by_type = defaultdict(list)
        for interaction in interactions:
            by_type[interaction.get('interaction_type', 'unknown')].append(interaction)
        
        analysis = {
            "total_interactions": len(interactions),
            "success_rate": len([i for i in interactions if i.get('success', False)]) / len(interactions),
            "average_processing_time": statistics.mean([i.get('processing_time', 0) for i in interactions]),
            "by_interaction_type": {}
        }
        
        for itype, type_interactions in by_type.items():
            analysis["by_interaction_type"][itype] = {
                "count": len(type_interactions),
                "success_rate": len([i for i in type_interactions if i.get('success', False)]) / len(type_interactions),
                "avg_processing_time": statistics.mean([i.get('processing_time', 0) for i in type_interactions]),
                "common_errors": Counter([i.get('error', 'None') for i in type_interactions if not i.get('success', True)])
            }
        
        return analysis
    
    def analyze_strategy_evolution(self, session_id: str) -> Dict[str, Any]:
        """Analyze how strategy evolved during a specific investigation"""
        
        strategies = self._load_strategy_decisions(session_id)
        if not strategies:
            return {"error": f"No strategy data found for session {session_id}"}
        
        analysis = {
            "session_id": session_id,
            "total_rounds": len(strategies),
            "strategy_progression": [],
            "learning_patterns": []
        }
        
        for strategy in strategies:
            round_info = {
                "round": strategy.get('round_number', 0),
                "strategy_type": strategy.get('strategy_type', 'Unknown'),
                "reasoning": strategy.get('reasoning', 'No reasoning provided')[:200] + "..." if len(strategy.get('reasoning', '')) > 200 else strategy.get('reasoning', ''),
                "searches_planned": len(strategy.get('searches_planned', []))
            }
            analysis["strategy_progression"].append(round_info)
        
        # Identify learning patterns
        if len(strategies) > 1:
            strategy_types = [s.get('strategy_type', '') for s in strategies]
            type_changes = []
            for i in range(1, len(strategy_types)):
                if strategy_types[i] != strategy_types[i-1]:
                    type_changes.append(f"Round {i}: Changed from {strategy_types[i-1]} to {strategy_types[i]}")
            
            analysis["learning_patterns"] = type_changes or ["No strategy type changes observed"]
        
        return analysis
    
    def generate_investigation_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive report for a specific investigation"""
        
        session_data = self._load_session_summary(session_id)
        if not session_data:
            return {"error": f"Session {session_id} not found"}
        
        # Get related data
        search_data = self._load_search_attempts_for_session(session_id)
        strategy_data = self._load_strategy_decisions(session_id)
        llm_data = self._load_llm_interactions_for_session(session_id)
        
        report = {
            "investigation_overview": {
                "session_id": session_id,
                "query": session_data.get('session_metadata', {}).get('user_query', 'Unknown'),
                "duration": f"{session_data.get('session_metadata', {}).get('duration_seconds', 0) / 60:.1f} minutes",
                "completion_reason": session_data.get('performance_metrics', {}).get('completion_reason', 'Unknown')
            },
            "performance_summary": session_data.get('performance_metrics', {}),
            "search_analysis": {
                "total_searches": len(search_data),
                "searches_by_round": self._group_searches_by_round(search_data),
                "effectiveness_trend": self._calculate_effectiveness_trend(search_data)
            },
            "strategy_analysis": {
                "total_rounds": len(strategy_data),
                "strategy_evolution": [s.get('strategy_type', 'Unknown') for s in strategy_data],
                "adaptation_points": self._identify_adaptation_points(strategy_data)
            },
            "llm_interaction_summary": {
                "total_interactions": len(llm_data),
                "success_rate": len([i for i in llm_data if i.get('success', False)]) / len(llm_data) if llm_data else 0,
                "avg_processing_time": statistics.mean([i.get('processing_time', 0) for i in llm_data]) if llm_data else 0
            },
            "recommendations": self._generate_recommendations(session_data, search_data, strategy_data)
        }
        
        return report
    
    def _load_sessions(self, session_id: Optional[str] = None, date: Optional[str] = None) -> List[Dict]:
        """Load session data from logs"""
        sessions = []
        
        if date:
            session_dir = self.base_log_dir / "sessions" / date
        else:
            session_dir = self.base_log_dir / "sessions"
        
        if not session_dir.exists():
            return sessions
        
        # Find session files
        if session_id:
            summary_file = session_dir / f"{session_id}_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    return [json.load(f)]
        else:
            # Load all sessions
            for file_path in session_dir.rglob("*_summary.json"):
                try:
                    with open(file_path, 'r') as f:
                        sessions.append(json.load(f))
                except Exception as e:
                    print(f"Error loading session file {file_path}: {e}")
        
        return sessions
    
    def _load_search_attempts(self, date: Optional[str] = None) -> List[Dict]:
        """Load search attempt data from logs"""
        searches = []
        
        if date:
            search_file = self.base_log_dir / "searches" / f"searches_{date}.jsonl"
            files_to_check = [search_file] if search_file.exists() else []
        else:
            search_dir = self.base_log_dir / "searches"
            files_to_check = list(search_dir.glob("searches_*.jsonl")) if search_dir.exists() else []
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            searches.append(json.loads(line))
            except Exception as e:
                print(f"Error loading search file {file_path}: {e}")
        
        return searches
    
    def _load_llm_interactions(self, date: Optional[str] = None) -> List[Dict]:
        """Load LLM interaction data from logs"""
        interactions = []
        
        if date:
            llm_file = self.base_log_dir / "llm_interactions" / f"llm_{date}.jsonl"
            files_to_check = [llm_file] if llm_file.exists() else []
        else:
            llm_dir = self.base_log_dir / "llm_interactions"
            files_to_check = list(llm_dir.glob("llm_*.jsonl")) if llm_dir.exists() else []
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            interactions.append(json.loads(line))
            except Exception as e:
                print(f"Error loading LLM file {file_path}: {e}")
        
        return interactions
    
    def _load_strategy_decisions(self, session_id: str) -> List[Dict]:
        """Load strategy decisions for a session"""
        strategies = []
        strategy_dir = self.base_log_dir / "strategies"
        
        if not strategy_dir.exists():
            return strategies
        
        for file_path in strategy_dir.glob("strategies_*.jsonl"):
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            strategy = json.loads(line)
                            if strategy.get('session_id') == session_id:
                                strategies.append(strategy)
            except Exception as e:
                print(f"Error loading strategy file {file_path}: {e}")
        
        return sorted(strategies, key=lambda x: x.get('round_number', 0))
    
    def _load_session_summary(self, session_id: str) -> Optional[Dict]:
        """Load session summary data"""
        sessions_dir = self.base_log_dir / "sessions"
        
        for file_path in sessions_dir.rglob(f"{session_id}_summary.json"):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading session summary {file_path}: {e}")
        
        return None
    
    def _load_search_attempts_for_session(self, session_id: str) -> List[Dict]:
        """Load search attempts for a specific session"""
        searches = self._load_search_attempts()
        return [s for s in searches if s.get('session_id') == session_id]
    
    def _load_llm_interactions_for_session(self, session_id: str) -> List[Dict]:
        """Load LLM interactions for a specific session"""
        interactions = self._load_llm_interactions()
        return [i for i in interactions if i.get('session_id') == session_id]
    
    def _get_top_performers(self, effectiveness_dict: Dict, top_n: int = 10) -> List[Tuple[str, float]]:
        """Get top performing items by average effectiveness"""
        averages = [(key, statistics.mean(scores)) for key, scores in effectiveness_dict.items() if scores]
        return sorted(averages, key=lambda x: x[1], reverse=True)[:top_n]
    
    def _group_searches_by_round(self, searches: List[Dict]) -> Dict[int, List[Dict]]:
        """Group searches by round number"""
        by_round = defaultdict(list)
        for search in searches:
            round_num = search.get('round_number', 0)
            by_round[round_num].append(search)
        return dict(by_round)
    
    def _calculate_effectiveness_trend(self, searches: List[Dict]) -> List[float]:
        """Calculate effectiveness trend over time"""
        if not searches:
            return []
        
        # Sort by search_id to get chronological order
        sorted_searches = sorted(searches, key=lambda x: x.get('search_id', 0))
        return [s.get('effectiveness_score', 0) for s in sorted_searches]
    
    def _identify_adaptation_points(self, strategies: List[Dict]) -> List[str]:
        """Identify key adaptation points in strategy"""
        adaptations = []
        
        for i in range(1, len(strategies)):
            prev_strategy = strategies[i-1].get('strategy_type', '')
            curr_strategy = strategies[i].get('strategy_type', '')
            
            if prev_strategy != curr_strategy:
                adaptations.append(f"Round {i+1}: Adapted from {prev_strategy} to {curr_strategy}")
        
        return adaptations
    
    def _generate_recommendations(self, session_data: Dict, search_data: List[Dict], strategy_data: List[Dict]) -> List[str]:
        """Generate recommendations based on investigation analysis"""
        recommendations = []
        
        performance = session_data.get('performance_metrics', {})
        satisfaction = performance.get('satisfaction_score', 0)
        total_results = performance.get('total_results_found', 0)
        
        if satisfaction < 0.3:
            recommendations.append("Low satisfaction score suggests trying different search approaches or broader terms")
        
        if total_results == 0:
            recommendations.append("No results found - consider alternative spellings, broader context, or different platforms")
        
        if search_data:
            avg_effectiveness = statistics.mean([s.get('effectiveness_score', 0) for s in search_data])
            if avg_effectiveness < 3.0:
                recommendations.append("Low average search effectiveness - review and refine search terms")
        
        if len(strategy_data) < 3:
            recommendations.append("Few strategy rounds - consider more iterative approach for complex topics")
        
        return recommendations or ["Investigation performed well within normal parameters"]

def create_analysis_report(session_id: Optional[str] = None, date: Optional[str] = None) -> str:
    """Create a formatted analysis report"""
    
    analyzer = LogAnalyzer()
    
    if session_id:
        report = analyzer.generate_investigation_report(session_id)
        title = f"Investigation Report for Session {session_id}"
    else:
        report = analyzer.analyze_session_performance(date=date)
        title = f"Performance Analysis for {date if date else 'All Sessions'}"
    
    # Format as readable text report
    output = [f"\n{'='*60}", title, f"{'='*60}"]
    
    def format_dict(d: Dict, indent: int = 0) -> List[str]:
        lines = []
        spaces = "  " * indent
        
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{spaces}{key.replace('_', ' ').title()}:")
                lines.extend(format_dict(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{spaces}{key.replace('_', ' ').title()}: {len(value)} items")
                for item in value[:5]:  # Show first 5 items
                    if isinstance(item, dict):
                        lines.append(f"{spaces}  - {str(item)[:100]}...")
                    else:
                        lines.append(f"{spaces}  - {str(item)}")
                if len(value) > 5:
                    lines.append(f"{spaces}  ... and {len(value) - 5} more")
            else:
                lines.append(f"{spaces}{key.replace('_', ' ').title()}: {value}")
        
        return lines
    
    output.extend(format_dict(report))
    output.append(f"{'='*60}\n")
    
    return "\n".join(output)

# Command-line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "session" and len(sys.argv) > 2:
            print(create_analysis_report(session_id=sys.argv[2]))
        elif sys.argv[1] == "date" and len(sys.argv) > 2:
            print(create_analysis_report(date=sys.argv[2]))
        else:
            print("Usage: python log_analyzer.py [session SESSION_ID | date YYYY-MM-DD]")
    else:
        print(create_analysis_report())