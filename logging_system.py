# logging_system.py
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import logging
from pathlib import Path

@dataclass
class LogEntry:
    """Base class for all log entries"""
    timestamp: str
    entry_type: str
    session_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SessionStartLog(LogEntry):
    """Log entry for investigation session start"""
    user_query: str
    config: Dict[str, Any]
    user_ip: Optional[str] = None
    
@dataclass
class SessionEndLog(LogEntry):
    """Log entry for investigation session completion"""
    completion_reason: str
    total_searches: int
    total_results: int
    satisfaction_score: float
    duration_seconds: float
    
@dataclass
class SearchAttemptLog(LogEntry):
    """Log entry for individual search attempts"""
    search_id: int
    round_number: int
    strategy_type: str
    query: str
    endpoint: str
    params: Dict[str, Any]
    results_count: int
    effectiveness_score: float
    execution_time: float
    error: Optional[str] = None
    sample_results: Optional[List[Dict]] = None

@dataclass
class StrategyDecisionLog(LogEntry):
    """Log entry for strategy generation decisions"""
    round_number: int
    previous_context: str
    strategy_type: str
    reasoning: str
    searches_planned: List[Dict[str, Any]]
    
@dataclass
class LLMInteractionLog(LogEntry):
    """Log entry for LLM interactions"""
    interaction_type: str  # "strategy_generation", "summarization", "analysis"
    prompt_sent: str
    llm_response: Dict[str, Any]
    processing_time: float
    success: bool
    error: Optional[str] = None

@dataclass
class RoundCompletionLog(LogEntry):
    """Log entry for completed investigation rounds"""
    round_number: int
    strategy_used: str
    searches_executed: int
    total_results: int
    round_effectiveness: float
    key_insights: List[str]
    next_strategy_hints: List[str]

class InvestigationLogger:
    """Comprehensive logging system for Twitter investigations"""
    
    def __init__(self, base_log_dir: str = "logs"):
        self.base_log_dir = Path(base_log_dir)
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        
        # Create directory structure
        self._setup_log_directories()
        
        # Setup Python logging for system events
        self._setup_system_logging()
    
    def _setup_log_directories(self):
        """Create the logging directory structure"""
        directories = [
            self.base_log_dir,
            self.base_log_dir / "sessions",
            self.base_log_dir / "searches", 
            self.base_log_dir / "llm_interactions",
            self.base_log_dir / "strategies",
            self.base_log_dir / "analytics",
            self.base_log_dir / "system"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _setup_system_logging(self):
        """Setup Python logging for system events"""
        log_file = self.base_log_dir / "system" / f"system_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        self.system_logger = logging.getLogger('investigation_system')
    
    def start_session(self, user_query: str, config, user_ip: Optional[str] = None) -> str:
        """Start a new investigation session and return session ID"""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.session_start_time = datetime.now(timezone.utc)
        
        # Log session start
        start_log = SessionStartLog(
            timestamp=self.session_start_time.isoformat(),
            entry_type="session_start",
            session_id=session_id,
            user_query=user_query,
            config=asdict(config),
            user_ip=user_ip
        )
        
        self._write_session_log(start_log)
        self.system_logger.info(f"Started investigation session {session_id} for query: {user_query[:50]}...")
        
        return session_id
    
    def end_session(self, session):
        """Log investigation session completion"""
        if not self.current_session_id or not self.session_start_time:
            self.system_logger.warning("end_session called without active session")
            return
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.session_start_time).total_seconds()
        
        end_log = SessionEndLog(
            timestamp=end_time.isoformat(),
            entry_type="session_end", 
            session_id=self.current_session_id,
            completion_reason=session.completion_reason or "Unknown",
            total_searches=session.search_count,
            total_results=session.total_results_found,
            satisfaction_score=session.satisfaction_metrics.overall_satisfaction(),
            duration_seconds=duration
        )
        
        self._write_session_log(end_log)
        
        # Write complete session summary
        self._write_complete_session_summary(session, duration)
        
        self.system_logger.info(f"Completed investigation session {self.current_session_id} - {session.search_count} searches, {session.total_results_found} results")
        
        self.current_session_id = None
        self.session_start_time = None
    
    def log_search_attempt(self, attempt, strategy_type: str, sample_results: Optional[List[Dict]] = None):
        """Log individual search attempt with results"""
        if not self.current_session_id:
            self.system_logger.warning("log_search_attempt called without active session")
            return
        
        search_log = SearchAttemptLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="search_attempt",
            session_id=self.current_session_id,
            search_id=attempt.search_id,
            round_number=attempt.round_number,
            strategy_type=strategy_type,
            query=attempt.params.get('query', ''),
            endpoint=attempt.endpoint,
            params=attempt.params,
            results_count=attempt.results_count,
            effectiveness_score=attempt.effectiveness_score,
            execution_time=attempt.execution_time,
            error=attempt.error,
            sample_results=sample_results
        )
        
        self._write_search_log(search_log)
        self.system_logger.debug(f"Logged search {attempt.search_id}: '{attempt.params.get('query', '')}' -> {attempt.results_count} results")
    
    def log_strategy_decision(self, round_number: int, previous_context: str, strategy_type: str, 
                            reasoning: str, searches_planned: List[Dict[str, Any]]):
        """Log strategy generation decision"""
        if not self.current_session_id:
            return
        
        strategy_log = StrategyDecisionLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="strategy_decision",
            session_id=self.current_session_id,
            round_number=round_number,
            previous_context=previous_context,
            strategy_type=strategy_type,
            reasoning=reasoning,
            searches_planned=searches_planned
        )
        
        self._write_strategy_log(strategy_log)
        self.system_logger.debug(f"Logged strategy decision for round {round_number}: {strategy_type}")
    
    def log_llm_interaction(self, interaction_type: str, prompt_sent: str, llm_response: Dict[str, Any],
                           processing_time: float, success: bool = True, error: Optional[str] = None):
        """Log LLM interactions for analysis"""
        if not self.current_session_id:
            return
        
        # Truncate very long prompts for logging
        truncated_prompt = prompt_sent[:2000] + "..." if len(prompt_sent) > 2000 else prompt_sent
        
        llm_log = LLMInteractionLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="llm_interaction",
            session_id=self.current_session_id,
            interaction_type=interaction_type,
            prompt_sent=truncated_prompt,
            llm_response=llm_response,
            processing_time=processing_time,
            success=success,
            error=error
        )
        
        self._write_llm_log(llm_log)
        self.system_logger.debug(f"Logged LLM interaction: {interaction_type} ({'success' if success else 'failed'})")
    
    def log_round_completion(self, round_number: int, strategy_used: str, searches_executed: int,
                           total_results: int, round_effectiveness: float, key_insights: List[str],
                           next_strategy_hints: List[str]):
        """Log completion of investigation round"""
        if not self.current_session_id:
            return
        
        round_log = RoundCompletionLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry_type="round_completion",
            session_id=self.current_session_id,
            round_number=round_number,
            strategy_used=strategy_used,
            searches_executed=searches_executed,
            total_results=total_results,
            round_effectiveness=round_effectiveness,
            key_insights=key_insights,
            next_strategy_hints=next_strategy_hints
        )
        
        self._write_session_log(round_log)
        self.system_logger.debug(f"Logged round {round_number} completion: {searches_executed} searches, effectiveness {round_effectiveness:.1f}")
    
    def _write_session_log(self, log_entry: LogEntry):
        """Write session-level log entry"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        session_dir = self.base_log_dir / "sessions" / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = session_dir / f"{self.current_session_id}.jsonl"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.to_dict(), ensure_ascii=False) + '\n')
    
    def _write_search_log(self, log_entry: SearchAttemptLog):
        """Write search-level log entry"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        search_file = self.base_log_dir / "searches" / f"searches_{date_str}.jsonl"
        
        with open(search_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.to_dict(), ensure_ascii=False) + '\n')
    
    def _write_llm_log(self, log_entry: LLMInteractionLog):
        """Write LLM interaction log entry"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        llm_file = self.base_log_dir / "llm_interactions" / f"llm_{date_str}.jsonl"
        
        with open(llm_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.to_dict(), ensure_ascii=False) + '\n')
    
    def _write_strategy_log(self, log_entry: StrategyDecisionLog):
        """Write strategy decision log entry"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        strategy_file = self.base_log_dir / "strategies" / f"strategies_{date_str}.jsonl"
        
        with open(strategy_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry.to_dict(), ensure_ascii=False) + '\n')
    
    def _write_complete_session_summary(self, session, duration_seconds: float):
        """Write comprehensive session summary for analysis"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        summary_dir = self.base_log_dir / "sessions" / date_str
        summary_file = summary_dir / f"{self.current_session_id}_summary.json"
        
        # Build comprehensive summary
        summary = {
            "session_metadata": {
                "session_id": self.current_session_id,
                "start_time": self.session_start_time.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration_seconds,
                "user_query": session.original_query
            },
            "configuration": asdict(session.config),
            "performance_metrics": {
                "total_searches": session.search_count,
                "total_rounds": session.round_count,
                "total_results_found": session.total_results_found,
                "satisfaction_score": session.satisfaction_metrics.overall_satisfaction(),
                "satisfaction_breakdown": asdict(session.satisfaction_metrics),
                "completion_reason": session.completion_reason
            },
            "search_summary": {
                "searches_by_effectiveness": self._analyze_search_effectiveness(session),
                "most_effective_strategies": self._identify_effective_strategies(session),
                "dead_ends": session.dead_ends,
                "promising_leads": session.promising_leads
            },
            "rounds_summary": [
                {
                    "round_number": round_obj.round_number,
                    "strategy": round_obj.strategy_description,
                    "searches_count": len(round_obj.searches),
                    "total_results": round_obj.total_results,
                    "effectiveness": round_obj.round_effectiveness,
                    "insights": round_obj.key_insights
                }
                for round_obj in session.rounds
            ]
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def _analyze_search_effectiveness(self, session) -> Dict[str, List[Dict]]:
        """Analyze search effectiveness patterns"""
        effectiveness_bins = {
            "highly_effective": [],  # 8-10
            "moderately_effective": [],  # 5-7
            "low_effectiveness": [],  # 2-4
            "ineffective": []  # 0-1
        }
        
        for search in session.search_history:
            search_info = {
                "search_id": search.search_id,
                "query": search.params.get('query', ''),
                "results": search.results_count,
                "effectiveness": search.effectiveness_score
            }
            
            if search.effectiveness_score >= 8:
                effectiveness_bins["highly_effective"].append(search_info)
            elif search.effectiveness_score >= 5:
                effectiveness_bins["moderately_effective"].append(search_info)
            elif search.effectiveness_score >= 2:
                effectiveness_bins["low_effectiveness"].append(search_info)
            else:
                effectiveness_bins["ineffective"].append(search_info)
        
        return effectiveness_bins
    
    def _identify_effective_strategies(self, session) -> List[Dict]:
        """Identify most effective search strategies"""
        strategy_effectiveness = {}
        
        for round_obj in session.rounds:
            if round_obj.searches:
                avg_effectiveness = sum(s.effectiveness_score for s in round_obj.searches) / len(round_obj.searches)
                strategy_effectiveness[round_obj.strategy_description] = avg_effectiveness
        
        # Sort by effectiveness
        sorted_strategies = sorted(strategy_effectiveness.items(), key=lambda x: x[1], reverse=True)
        
        return [{"strategy": strategy, "avg_effectiveness": effectiveness} 
                for strategy, effectiveness in sorted_strategies]

# Global logger instance
investigation_logger = InvestigationLogger()