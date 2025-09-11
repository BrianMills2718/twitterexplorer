# knowledge_builder.py
from typing import Dict, List, Any, Optional, Set, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json
import re
from datetime import datetime

# Use TYPE_CHECKING to avoid circular import and performance hit
if TYPE_CHECKING:
    from investigation_engine import InvestigationSession, SearchAttempt, Finding
else:
    # At runtime, use forward references to avoid heavy investigation_engine import
    InvestigationSession = 'InvestigationSession'
    SearchAttempt = 'SearchAttempt'
    Finding = 'Finding'

@dataclass
class KnowledgeNode:
    """Represents a piece of accumulated knowledge"""
    id: str
    content: str
    category: str
    confidence: float
    sources: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)
    timestamps: List[str] = field(default_factory=list)
    evidence_strength: str = "unknown"
    
@dataclass
class Contradiction:
    """Represents conflicting information found"""
    claim_a: str
    claim_b: str
    source_a: str
    source_b: str
    confidence_a: float
    confidence_b: float
    resolution_status: str = "unresolved"  # unresolved, resolved, inconclusive
    
@dataclass
class InvestigationMemory:
    """Comprehensive memory system for investigation"""
    knowledge_nodes: Dict[str, KnowledgeNode] = field(default_factory=dict)
    contradictions: List[Contradiction] = field(default_factory=list)
    search_patterns: Dict[str, float] = field(default_factory=dict)  # pattern -> effectiveness
    source_credibility: Dict[str, float] = field(default_factory=dict)
    topic_coverage: Dict[str, List[str]] = field(default_factory=dict)  # topic -> related searches
    key_insights: List[str] = field(default_factory=list)
    research_gaps: List[str] = field(default_factory=list)

class KnowledgeBuilder:
    """Builds and maintains accumulated knowledge from investigation"""
    
    def __init__(self):
        self.memory = InvestigationMemory()
        
        # Topic categorization patterns
        self.topic_patterns = {
            'credibility': ['credible', 'reliable', 'trustworthy', 'verified', 'confirmed'],
            'debunking': ['debunked', 'false', 'hoax', 'fake', 'disproven', 'refuted'],
            'evidence': ['evidence', 'proof', 'documentation', 'witness', 'testimony'],
            'expert_opinion': ['expert', 'analyst', 'researcher', 'scientist', 'professor'],
            'fact_check': ['fact check', 'snopes', 'factcheck', 'verification', 'investigated'],
            'claims': ['claims', 'alleges', 'states', 'asserts', 'maintains'],
            'skepticism': ['skeptical', 'doubtful', 'questionable', 'suspicious', 'unlikely']
        }
        
        # Confidence indicators
        self.high_confidence_sources = [
            'reuters', 'ap news', 'bbc', 'snopes', 'factcheck.org',
            'politifact', 'nature', 'science', 'peer review'
        ]
        
        self.medium_confidence_sources = [
            'wikipedia', 'academic', 'university', 'researcher', 
            'journalist', 'investigation', 'analysis'
        ]
    
    def build_knowledge_from_session(self, session: 'InvestigationSession') -> InvestigationMemory:
        """Build comprehensive knowledge from investigation session"""
        
        # Process all search attempts
        for search in session.search_history:
            self._process_search_attempt(search, session.original_query)
        
        # Analyze patterns across searches
        self._analyze_search_patterns(session)
        
        # Identify contradictions
        self._identify_contradictions()
        
        # Generate insights
        self._generate_insights(session)
        
        # Identify research gaps
        self._identify_research_gaps(session)
        
        return self.memory
    
    def _process_search_attempt(self, search: SearchAttempt, original_query: str):
        """Process a single search attempt to extract knowledge"""
        
        if search.results_count == 0 or search.error:
            return
            
        query = search.params.get('query', '').lower()
        
        # Extract potential knowledge from query and context
        knowledge_items = self._extract_knowledge_from_search(search, original_query)
        
        # Add to memory
        for item in knowledge_items:
            node_id = f"search_{search.search_id}_{len(self.memory.knowledge_nodes)}"
            
            node = KnowledgeNode(
                id=node_id,
                content=item['content'],
                category=item['category'],
                confidence=item['confidence'],
                sources=[f"search_{search.search_id}"],
                timestamps=[datetime.now().isoformat()],
                evidence_strength=item['evidence_strength']
            )
            
            self.memory.knowledge_nodes[node_id] = node
        
        # Track search pattern effectiveness
        search_pattern = self._extract_search_pattern(query)
        if search_pattern:
            effectiveness = search.effectiveness_score / 10.0
            if search_pattern in self.memory.search_patterns:
                # Average with existing effectiveness
                self.memory.search_patterns[search_pattern] = (
                    self.memory.search_patterns[search_pattern] + effectiveness
                ) / 2
            else:
                self.memory.search_patterns[search_pattern] = effectiveness
    
    def _extract_knowledge_from_search(self, search: SearchAttempt, original_query: str) -> List[Dict]:
        """Extract knowledge items from search context"""
        
        query = search.params.get('query', '').lower()
        knowledge_items = []
        
        # Categorize the search intent
        category = self._categorize_search_intent(query)
        
        # Determine confidence based on search effectiveness and query type
        base_confidence = min(0.9, search.effectiveness_score / 10.0)
        
        # Adjust confidence based on search terms
        confidence_modifier = 1.0
        if any(source in query for source in self.high_confidence_sources):
            confidence_modifier = 1.2
        elif any(source in query for source in self.medium_confidence_sources):
            confidence_modifier = 1.1
        
        final_confidence = min(1.0, base_confidence * confidence_modifier)
        
        # Create knowledge item
        if search.results_count > 0:
            content = f"Search for '{search.params.get('query', '')}' yielded {search.results_count} results"
            
            evidence_strength = (
                "very_high" if search.effectiveness_score > 8 else
                "high" if search.effectiveness_score > 6 else
                "medium" if search.effectiveness_score > 4 else
                "low"
            )
            
            knowledge_items.append({
                'content': content,
                'category': category,
                'confidence': final_confidence,
                'evidence_strength': evidence_strength
            })
            
            # Add specific insights based on search type
            if 'debunk' in query and search.results_count > 5:
                knowledge_items.append({
                    'content': f"Active debunking discussion found for topic",
                    'category': 'debunking',
                    'confidence': final_confidence,
                    'evidence_strength': evidence_strength
                })
            
            elif 'fact check' in query and search.results_count > 0:
                knowledge_items.append({
                    'content': f"Fact-checking resources available for topic",
                    'category': 'fact_check',
                    'confidence': final_confidence * 1.1,  # Boost for fact-checking
                    'evidence_strength': evidence_strength
                })
        
        return knowledge_items
    
    def _categorize_search_intent(self, query: str) -> str:
        """Categorize the intent of a search query"""
        
        for category, patterns in self.topic_patterns.items():
            if any(pattern in query for pattern in patterns):
                return category
                
        return 'general'
    
    def _extract_search_pattern(self, query: str) -> Optional[str]:
        """Extract generalizable search pattern from query"""
        
        # Remove specific names and quotes to get general pattern
        pattern = re.sub(r'"[^"]*"', '[NAME]', query)
        pattern = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME]', pattern)
        
        # Normalize whitespace
        pattern = ' '.join(pattern.split())
        
        return pattern if len(pattern.split()) > 1 else None
    
    def _analyze_search_patterns(self, session: 'InvestigationSession'):
        """Analyze effectiveness of different search patterns"""
        
        pattern_stats = defaultdict(list)
        
        for search in session.search_history:
            pattern = self._extract_search_pattern(search.params.get('query', ''))
            if pattern:
                pattern_stats[pattern].append(search.effectiveness_score)
        
        # Calculate average effectiveness for each pattern
        for pattern, scores in pattern_stats.items():
            avg_effectiveness = sum(scores) / len(scores)
            self.memory.search_patterns[pattern] = avg_effectiveness
    
    def _identify_contradictions(self):
        """Identify potential contradictions in accumulated knowledge"""
        
        # Simple contradiction detection based on opposite categories
        opposing_categories = [
            ('credibility', 'debunking'),
            ('evidence', 'skepticism'),
            ('fact_check', 'claims')
        ]
        
        for cat_a, cat_b in opposing_categories:
            nodes_a = [n for n in self.memory.knowledge_nodes.values() if n.category == cat_a]
            nodes_b = [n for n in self.memory.knowledge_nodes.values() if n.category == cat_b]
            
            for node_a in nodes_a:
                for node_b in nodes_b:
                    # Check if they might be contradictory
                    if self._are_potentially_contradictory(node_a, node_b):
                        contradiction = Contradiction(
                            claim_a=node_a.content,
                            claim_b=node_b.content,
                            source_a=node_a.sources[0] if node_a.sources else 'unknown',
                            source_b=node_b.sources[0] if node_b.sources else 'unknown',
                            confidence_a=node_a.confidence,
                            confidence_b=node_b.confidence
                        )
                        self.memory.contradictions.append(contradiction)
    
    def _are_potentially_contradictory(self, node_a: KnowledgeNode, node_b: KnowledgeNode) -> bool:
        """Check if two knowledge nodes are potentially contradictory"""
        
        # Simple heuristic: if one suggests credibility and other suggests debunking
        credibility_terms = ['credible', 'verified', 'confirmed', 'reliable']
        debunking_terms = ['debunked', 'false', 'hoax', 'fake']
        
        content_a = node_a.content.lower()
        content_b = node_b.content.lower()
        
        has_credibility_a = any(term in content_a for term in credibility_terms)
        has_debunking_b = any(term in content_b for term in debunking_terms)
        
        has_credibility_b = any(term in content_b for term in credibility_terms)
        has_debunking_a = any(term in content_a for term in debunking_terms)
        
        return (has_credibility_a and has_debunking_b) or (has_credibility_b and has_debunking_a)
    
    def _generate_insights(self, session: 'InvestigationSession'):
        """Generate key insights from accumulated knowledge"""
        
        insights = []
        
        # Insight 1: Overall finding direction
        debunking_nodes = [n for n in self.memory.knowledge_nodes.values() if n.category == 'debunking']
        credibility_nodes = [n for n in self.memory.knowledge_nodes.values() if n.category == 'credibility']
        
        # Only generate insights if data was actually found
        if len(debunking_nodes) > 0 or len(credibility_nodes) > 0:
            if len(debunking_nodes) > len(credibility_nodes):
                insights.append("Investigation found more debunking/skeptical information than supportive content")
            elif len(credibility_nodes) > len(debunking_nodes):
                insights.append("Investigation found more supportive/credible information than debunking content")
            else:
                insights.append("Investigation found mixed or balanced perspectives")
        
        # Insight 2: Source quality (only if data found)
        if len(self.memory.knowledge_nodes) > 0:
            high_confidence_nodes = [n for n in self.memory.knowledge_nodes.values() if n.confidence > 0.7]
            if len(high_confidence_nodes) > len(self.memory.knowledge_nodes) * 0.5:
                insights.append("Investigation uncovered high-quality, reliable sources")
            else:
                insights.append("Investigation found limited high-confidence information")
        
        # Insight 3: Research depth (only if data found)
        if len(self.memory.knowledge_nodes) > 0:
            categories_found = set(n.category for n in self.memory.knowledge_nodes.values())
            if len(categories_found) >= 4:
                insights.append("Investigation covered multiple aspects of the topic comprehensively")
            else:
                insights.append("Investigation focused on limited aspects of the topic")
        
        # Insight 4: Fact-checking availability (only if data found)
        if len(self.memory.knowledge_nodes) > 0:
            fact_check_nodes = [n for n in self.memory.knowledge_nodes.values() if n.category == 'fact_check']
            if fact_check_nodes:
                insights.append("Professional fact-checking resources were found for this topic")
            else:
                insights.append("Limited professional fact-checking available for this topic")
        
        self.memory.key_insights = insights
    
    def _identify_research_gaps(self, session: 'InvestigationSession'):
        """Identify gaps in the investigation that could be addressed"""
        
        gaps = []
        
        # Check for missing categories
        found_categories = set(n.category for n in self.memory.knowledge_nodes.values())
        important_categories = {'debunking', 'credibility', 'evidence', 'expert_opinion', 'fact_check'}
        
        missing_categories = important_categories - found_categories
        if missing_categories:
            gaps.append(f"Missing investigation areas: {', '.join(missing_categories)}")
        
        # Check for low search diversity
        if len(set(s.params.get('query', '') for s in session.search_history)) < 5:
            gaps.append("Limited search term diversity - could try more varied approaches")
        
        # Check for low result counts
        avg_results = sum(s.results_count for s in session.search_history) / len(session.search_history) if session.search_history else 0
        if avg_results < 3:
            gaps.append("Low average result count - could try broader search terms")
        
        # Check for temporal gaps
        temporal_searches = [s for s in session.search_history if any(term in s.params.get('query', '').lower() 
                           for term in ['2024', '2023', 'recent', 'latest', 'current'])]
        if not temporal_searches:
            gaps.append("No temporal analysis - could investigate recent vs historical discussions")
        
        self.memory.research_gaps = gaps
    
    def generate_knowledge_summary(self) -> str:
        """Generate human-readable knowledge summary"""
        
        summary_parts = []
        summary_parts.append("🧠 **ACCUMULATED KNOWLEDGE SUMMARY**")
        summary_parts.append("=" * 50)
        
        # Knowledge overview
        total_nodes = len(self.memory.knowledge_nodes)
        summary_parts.append(f"**Total Knowledge Items:** {total_nodes}")
        
        if total_nodes > 0:
            # Category breakdown
            category_counts = Counter(n.category for n in self.memory.knowledge_nodes.values())
            summary_parts.append(f"**Knowledge Categories:**")
            for category, count in category_counts.most_common():
                summary_parts.append(f"  • {category.title()}: {count} items")
            
            # Confidence analysis
            avg_confidence = sum(n.confidence for n in self.memory.knowledge_nodes.values()) / total_nodes
            summary_parts.append(f"**Average Confidence:** {avg_confidence:.1%}")
            
            # Key insights
            if self.memory.key_insights:
                summary_parts.append("\n**Key Insights:**")
                for insight in self.memory.key_insights:
                    summary_parts.append(f"  • {insight}")
            
            # Contradictions found
            if self.memory.contradictions:
                summary_parts.append(f"\n**Contradictions Found:** {len(self.memory.contradictions)}")
                for i, contradiction in enumerate(self.memory.contradictions[:3]):  # Show first 3
                    summary_parts.append(f"  {i+1}. {contradiction.claim_a[:50]}... vs {contradiction.claim_b[:50]}...")
            
            # Research gaps
            if self.memory.research_gaps:
                summary_parts.append("\n**Identified Research Gaps:**")
                for gap in self.memory.research_gaps:
                    summary_parts.append(f"  • {gap}")
            
            # Most effective search patterns
            if self.memory.search_patterns:
                best_patterns = sorted(self.memory.search_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
                summary_parts.append("\n**Most Effective Search Patterns:**")
                for pattern, effectiveness in best_patterns:
                    summary_parts.append(f"  • {pattern} (effectiveness: {effectiveness:.1f}/10)")
        
        else:
            summary_parts.append("No significant knowledge accumulated from investigation.")
        
        return "\n".join(summary_parts)
    
    def get_investigation_recommendations(self, session: 'InvestigationSession') -> List[str]:
        """Get specific recommendations based on accumulated knowledge"""
        
        recommendations = []
        
        # Based on knowledge gaps
        found_categories = set(n.category for n in self.memory.knowledge_nodes.values())
        
        if 'fact_check' not in found_categories:
            recommendations.append("Search for professional fact-checking sources (Snopes, FactCheck.org, etc.)")
        
        if 'expert_opinion' not in found_categories:
            recommendations.append("Look for expert analysis or academic perspectives on the topic")
        
        if 'evidence' not in found_categories:
            recommendations.append("Search for specific evidence or documentation related to claims")
        
        # Based on search effectiveness
        if self.memory.search_patterns:
            ineffective_patterns = [p for p, e in self.memory.search_patterns.items() if e < 3.0]
            if ineffective_patterns:
                recommendations.append("Avoid search patterns that haven't been effective")
            
            effective_patterns = [p for p, e in self.memory.search_patterns.items() if e > 6.0]
            if effective_patterns:
                recommendations.append("Build on search patterns that have been successful")
        
        # Based on contradictions
        if self.memory.contradictions:
            recommendations.append("Investigate contradictory information found to resolve conflicts")
        
        # Based on satisfaction level
        if session.satisfaction_metrics.overall_satisfaction() < 0.5:
            recommendations.append("Consider expanding to other platforms or information sources")
            recommendations.append("Try alternative names, spellings, or related topics")
        
        return recommendations