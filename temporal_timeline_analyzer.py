"""Temporal Timeline Analysis for Twitter Explorer Investigation System"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import re
from collections import defaultdict

@dataclass
class TimelineEvent:
    """Represents a single event in the temporal timeline"""
    timestamp: str
    description: str
    finding_source: str
    significance_score: float  # 0.0-1.0
    event_type: str  # 'tweet', 'announcement', 'development', 'controversy'
    entities_involved: List[str]
    original_content: str

@dataclass
class TemporalTimeline:
    """Complete temporal timeline analysis of investigation findings"""
    events: List[TimelineEvent] = field(default_factory=list)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    consistency_score: float = 0.0  # 0.0-1.0
    temporal_density: float = 0.0  # Events per day
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0

class TemporalTimelineAnalyzer:
    """Analyzes temporal patterns and creates chronological timelines from investigation findings"""
    
    def __init__(self, llm_client=None):
        if llm_client is None:
            from llm_client import get_litellm_client
            self.llm_client = get_litellm_client()
        else:
            self.llm_client = llm_client
            
        # Timestamp extraction patterns
        self.timestamp_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}/\d{1,2}/\d{2}\b',  # M/D/YY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # DD Month YYYY
        ]
        
        # Time-related keywords for event significance
        self.temporal_keywords = {
            'high_significance': ['announced', 'launched', 'released', 'breakthrough', 'milestone'],
            'medium_significance': ['updated', 'improved', 'changed', 'modified', 'upgraded'],
            'low_significance': ['mentioned', 'discussed', 'talked about', 'referenced']
        }
        
    def analyze_timeline(self, findings: List[Any], investigation_goal: str) -> TemporalTimeline:
        """
        Main method to perform temporal timeline analysis on investigation findings
        
        Args:
            findings: List of Finding objects from investigation
            investigation_goal: Original investigation query for context
            
        Returns:
            TemporalTimeline with chronologically ordered events
        """
        timeline = TemporalTimeline()
        
        if len(findings) < 1:
            timeline.confidence_score = 0.0
            return timeline
            
        # Extract temporal events from findings
        events = self._extract_temporal_events(findings, investigation_goal)
        
        if not events:
            timeline.confidence_score = 0.0
            return timeline
            
        # Sort events chronologically
        timeline.events = self._sort_events_chronologically(events)
        
        # Set timeline bounds
        if timeline.events:
            timeline.start_date = timeline.events[0].timestamp
            timeline.end_date = timeline.events[-1].timestamp
            
        # Calculate metrics
        timeline.consistency_score = self._calculate_temporal_consistency(timeline.events)
        timeline.temporal_density = self._calculate_temporal_density(timeline.events)
        timeline.trend_analysis = self._analyze_temporal_trends(timeline.events, investigation_goal)
        timeline.confidence_score = self._calculate_timeline_confidence(timeline, len(findings))
        
        return timeline
    
    def _extract_temporal_events(self, findings: List[Any], investigation_goal: str) -> List[TimelineEvent]:
        """Extract temporal events from findings with timestamp information"""
        events = []
        
        for finding in findings:
            content = getattr(finding, 'content', '')
            source = getattr(finding, 'source', 'unknown')
            
            # Extract timestamps from content
            timestamps = self._extract_timestamps(content)
            
            # If no explicit timestamps, try to infer temporal context
            if not timestamps:
                # Use current date as fallback for recent findings
                timestamps = [datetime.now().strftime('%Y-%m-%d')]
            
            for timestamp in timestamps:
                # Determine event significance
                significance = self._calculate_event_significance(content)
                
                # Determine event type
                event_type = self._determine_event_type(content)
                
                # Extract entities mentioned in the content
                entities = self._extract_entities_from_content(content)
                
                # Create description from content
                description = self._create_event_description(content, investigation_goal)
                
                event = TimelineEvent(
                    timestamp=timestamp,
                    description=description,
                    finding_source=source,
                    significance_score=significance,
                    event_type=event_type,
                    entities_involved=entities,
                    original_content=content[:200] + "..." if len(content) > 200 else content
                )
                
                events.append(event)
                
        return events
    
    def _extract_timestamps(self, content: str) -> List[str]:
        """Extract timestamps from content using regex patterns"""
        timestamps = []
        
        for pattern in self.timestamp_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                normalized = self._normalize_timestamp(match)
                if normalized:
                    timestamps.append(normalized)
                    
        return list(set(timestamps))  # Remove duplicates
    
    def _normalize_timestamp(self, timestamp_str: str) -> Optional[str]:
        """Normalize various timestamp formats to YYYY-MM-DD"""
        try:
            # Handle different formats
            if re.match(r'\d{4}-\d{2}-\d{2}', timestamp_str):
                return timestamp_str
            elif re.match(r'\d{2}/\d{2}/\d{4}', timestamp_str):
                # MM/DD/YYYY
                month, day, year = timestamp_str.split('/')
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif re.match(r'\d{1,2}/\d{1,2}/\d{2}', timestamp_str):
                # M/D/YY
                month, day, year = timestamp_str.split('/')
                year = f"20{year}" if int(year) < 50 else f"19{year}"
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            else:
                # Try to parse month names
                from datetime import datetime
                try:
                    if ',' in timestamp_str:
                        dt = datetime.strptime(timestamp_str, '%b %d, %Y')
                    else:
                        dt = datetime.strptime(timestamp_str, '%d %b %Y')
                    return dt.strftime('%Y-%m-%d')
                except:
                    pass
                    
        except Exception:
            pass
            
        return None
    
    def _calculate_event_significance(self, content: str) -> float:
        """Calculate significance score based on content keywords"""
        content_lower = content.lower()
        
        high_count = sum(1 for keyword in self.temporal_keywords['high_significance'] 
                        if keyword in content_lower)
        medium_count = sum(1 for keyword in self.temporal_keywords['medium_significance'] 
                          if keyword in content_lower)
        low_count = sum(1 for keyword in self.temporal_keywords['low_significance'] 
                       if keyword in content_lower)
        
        # Calculate weighted score
        total_keywords = high_count + medium_count + low_count
        if total_keywords == 0:
            return 0.3  # Default moderate significance
            
        weighted_score = (high_count * 1.0 + medium_count * 0.6 + low_count * 0.3) / total_keywords
        
        # Consider content length (longer content might be more significant)
        length_bonus = min(0.2, len(content) / 1000)  # Up to 0.2 bonus for long content
        
        return min(1.0, weighted_score + length_bonus)
    
    def _determine_event_type(self, content: str) -> str:
        """Determine the type of event based on content analysis"""
        content_lower = content.lower()
        
        # Define keywords for different event types
        event_type_keywords = {
            'announcement': ['announced', 'launches', 'introduces', 'reveals', 'unveils'],
            'development': ['developed', 'built', 'created', 'improved', 'enhanced'],
            'controversy': ['controversy', 'dispute', 'criticism', 'backlash', 'debate'],
            'tweet': ['tweet', 'posted', 'shared', 'tweeted']
        }
        
        # Count matches for each type
        type_scores = {}
        for event_type, keywords in event_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                type_scores[event_type] = score
                
        # Return type with highest score, default to 'tweet'
        return max(type_scores.items(), key=lambda x: x[1])[0] if type_scores else 'tweet'
    
    def _extract_entities_from_content(self, content: str) -> List[str]:
        """Extract entities (names, organizations, products) from content"""
        entities = []
        
        # Simple entity extraction patterns
        entity_patterns = [
            r'@\w+',  # Twitter handles
            r'#\w+',  # Hashtags
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, content)
            entities.extend(matches)
            
        # Remove duplicates and filter out common words
        common_words = {'The', 'This', 'That', 'And', 'Or', 'But', 'In', 'On', 'At', 'To', 'For'}
        entities = list(set([e for e in entities if e not in common_words]))
        
        return entities[:10]  # Limit to top 10 entities
    
    def _create_event_description(self, content: str, investigation_goal: str) -> str:
        """Create a concise event description from content"""
        # Take first sentence or first 100 characters
        sentences = content.split('.')
        if sentences and len(sentences[0]) <= 100:
            description = sentences[0].strip()
        else:
            description = content[:100].strip()
            
        # Ensure it ends properly
        if not description.endswith('.'):
            description += '...'
            
        return description
    
    def _sort_events_chronologically(self, events: List[TimelineEvent]) -> List[TimelineEvent]:
        """Sort events by timestamp in chronological order"""
        def timestamp_to_date(timestamp_str):
            try:
                return datetime.strptime(timestamp_str, '%Y-%m-%d')
            except:
                return datetime.now()  # Fallback to now if parsing fails
                
        return sorted(events, key=lambda event: timestamp_to_date(event.timestamp))
    
    def _calculate_temporal_consistency(self, events: List[TimelineEvent]) -> float:
        """Calculate how consistent the temporal information is"""
        if len(events) < 2:
            return 0.8  # Assume good consistency for single events
            
        # Check for logical timestamp ordering
        consistency_score = 1.0
        
        # Analyze timestamp gaps
        timestamps = [event.timestamp for event in events]
        dates = []
        for ts in timestamps:
            try:
                dates.append(datetime.strptime(ts, '%Y-%m-%d'))
            except:
                consistency_score -= 0.1  # Penalty for unparseable dates
                
        if len(dates) < 2:
            return max(0.0, consistency_score)
            
        # Check for reasonable date gaps
        dates.sort()
        total_days = (dates[-1] - dates[0]).days
        if total_days > 365 * 2:  # More than 2 years
            consistency_score -= 0.2
        elif total_days < 1:  # All events on same day
            consistency_score -= 0.1
            
        return max(0.0, min(1.0, consistency_score))
    
    def _calculate_temporal_density(self, events: List[TimelineEvent]) -> float:
        """Calculate events per day density"""
        if len(events) < 2:
            return 1.0
            
        timestamps = [event.timestamp for event in events]
        dates = []
        for ts in timestamps:
            try:
                dates.append(datetime.strptime(ts, '%Y-%m-%d'))
            except:
                continue
                
        if len(dates) < 2:
            return 1.0
            
        dates.sort()
        total_days = max(1, (dates[-1] - dates[0]).days)
        return len(events) / total_days
    
    def _analyze_temporal_trends(self, events: List[TimelineEvent], investigation_goal: str) -> Dict[str, Any]:
        """Analyze trends in the temporal data"""
        trends = {
            'activity_pattern': 'unknown',
            'peak_periods': [],
            'significance_trend': 'stable'
        }
        
        if len(events) < 3:
            return trends
            
        # Analyze activity patterns by grouping events by month
        monthly_counts = defaultdict(int)
        monthly_significance = defaultdict(list)
        
        for event in events:
            try:
                date = datetime.strptime(event.timestamp, '%Y-%m-%d')
                month_key = date.strftime('%Y-%m')
                monthly_counts[month_key] += 1
                monthly_significance[month_key].append(event.significance_score)
            except:
                continue
                
        # Determine activity pattern
        if len(monthly_counts) > 0:
            count_values = list(monthly_counts.values())
            if max(count_values) > 2 * (sum(count_values) / len(count_values)):
                trends['activity_pattern'] = 'bursty'
            elif max(count_values) - min(count_values) <= 1:
                trends['activity_pattern'] = 'steady'
            else:
                trends['activity_pattern'] = 'variable'
                
        # Find peak periods (months with highest activity)
        if monthly_counts:
            max_activity = max(monthly_counts.values())
            peak_months = [month for month, count in monthly_counts.items() 
                          if count >= max_activity * 0.8]
            trends['peak_periods'] = peak_months
            
        # Analyze significance trend
        if len(events) >= 5:
            mid_point = len(events) // 2
            early_avg_sig = sum(e.significance_score for e in events[:mid_point]) / mid_point
            late_avg_sig = sum(e.significance_score for e in events[mid_point:]) / (len(events) - mid_point)
            
            if late_avg_sig > early_avg_sig + 0.1:
                trends['significance_trend'] = 'increasing'
            elif late_avg_sig < early_avg_sig - 0.1:
                trends['significance_trend'] = 'decreasing'
            else:
                trends['significance_trend'] = 'stable'
                
        return trends
    
    def _calculate_timeline_confidence(self, timeline: TemporalTimeline, num_findings: int) -> float:
        """Calculate overall confidence score for the timeline analysis"""
        if len(timeline.events) == 0:
            return 0.0
            
        # Base confidence from number of events
        events_confidence = min(1.0, len(timeline.events) / 10.0)
        
        # Temporal consistency confidence
        consistency_confidence = timeline.consistency_score
        
        # Coverage confidence (events vs findings ratio)
        coverage_confidence = min(1.0, len(timeline.events) / max(1, num_findings))
        
        # Temporal spread confidence (events should span some time)
        if timeline.start_date and timeline.end_date:
            try:
                start = datetime.strptime(timeline.start_date, '%Y-%m-%d')
                end = datetime.strptime(timeline.end_date, '%Y-%m-%d')
                days_span = (end - start).days
                spread_confidence = min(1.0, days_span / 30.0) if days_span > 0 else 0.8
            except:
                spread_confidence = 0.5
        else:
            spread_confidence = 0.3
            
        # Weighted average
        overall_confidence = (
            events_confidence * 0.3 +
            consistency_confidence * 0.3 +
            coverage_confidence * 0.2 +
            spread_confidence * 0.2
        )
        
        return min(1.0, overall_confidence)