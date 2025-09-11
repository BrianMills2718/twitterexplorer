# satisfaction_assessor.py
from typing import List, Dict, Any, Tuple, TYPE_CHECKING
import re
from dataclasses import dataclass

# Use TYPE_CHECKING to avoid circular import - only import types during type checking
if TYPE_CHECKING:
    from investigation_engine import InvestigationSession, SearchAttempt, SatisfactionMetrics, Finding
else:
    # At runtime, use forward references to avoid heavy investigation_engine import
    InvestigationSession = 'InvestigationSession'
    SearchAttempt = 'SearchAttempt' 
    SatisfactionMetrics = 'SatisfactionMetrics'
    Finding = 'Finding'

def _lazy_import_satisfaction_metrics():
    """Lazy import SatisfactionMetrics only when needed to avoid startup delay"""
    from investigation_engine import SatisfactionMetrics
    return SatisfactionMetrics

@dataclass
class ContentAnalysis:
    """Analysis of content quality and relevance"""
    skeptical_indicators: int = 0
    credibility_signals: int = 0  
    fact_check_mentions: int = 0
    expert_voices: int = 0
    specific_claims: int = 0
    general_mentions: int = 0
    
class SatisfactionAssessor:
    """Advanced system for assessing investigation quality and completeness"""
    
    def __init__(self):
        # Keywords that indicate skeptical/debunking content
        self.skeptical_keywords = [
            'debunked', 'false', 'hoax', 'fake', 'disproven', 'refuted',
            'myth', 'misinformation', 'conspiracy', 'unsubstantiated',
            'lacks evidence', 'no proof', 'fabricated', 'fictitious'
        ]
        
        # Keywords that indicate credible fact-checking
        self.credibility_keywords = [
            'fact check', 'snopes', 'factcheck.org', 'politifact', 
            'reuters fact check', 'ap fact check', 'investigated',
            'verified', 'confirmed', 'expert analysis', 'peer review'
        ]
        
        # Indicators of expert voices
        self.expert_indicators = [
            'dr.', 'professor', 'phd', 'researcher', 'scientist', 
            'investigator', 'journalist', 'analyst', 'expert',
            'specialist', 'authority', 'academic'
        ]
        
        # Indicators of specific vs general content
        self.specificity_indicators = [
            'evidence', 'documents', 'timeline', 'dates', 'locations',
            'witnesses', 'recordings', 'photos', 'inconsistencies',
            'contradictions', 'claims vs reality'
        ]
    
    def assess_investigation_satisfaction(self, session: 'InvestigationSession') -> 'SatisfactionMetrics':
        """Comprehensive assessment of investigation satisfaction"""
        
        # Analyze all search results
        content_analysis = self._analyze_search_content(session)
        
        # Calculate each dimension of satisfaction
        information_coverage = self._calculate_information_coverage(session, content_analysis)
        source_diversity = self._calculate_source_diversity(session)
        evidence_quality = self._calculate_evidence_quality(session, content_analysis)
        claim_specificity = self._calculate_claim_specificity(content_analysis)
        contradiction_resolution = self._calculate_contradiction_resolution(session, content_analysis)
        
        SatisfactionMetrics = _lazy_import_satisfaction_metrics()
        return SatisfactionMetrics(
            information_coverage=information_coverage,
            source_diversity=source_diversity,
            evidence_quality=evidence_quality,
            claim_specificity=claim_specificity,
            contradiction_resolution=contradiction_resolution
        )
    
    def _analyze_search_content(self, session: 'InvestigationSession') -> ContentAnalysis:
        """Analyze content across all searches to assess quality"""
        
        analysis = ContentAnalysis()
        
        for search in session.search_history:
            if search.results_count > 0 and search.effectiveness_score > 3.0:
                # Simulate content analysis (in real implementation, would analyze actual tweet content)
                query = search.params.get('query', '').lower()
                
                # Count skeptical indicators
                analysis.skeptical_indicators += sum(1 for word in self.skeptical_keywords if word in query)
                
                # Count credibility signals
                analysis.credibility_signals += sum(1 for word in self.credibility_keywords if word in query)
                
                # Count fact check mentions
                if any(word in query for word in ['fact check', 'snopes', 'factcheck']):
                    analysis.fact_check_mentions += 1
                
                # Count expert indicators
                analysis.expert_voices += sum(1 for word in self.expert_indicators if word in query)
                
                # Count specificity indicators
                analysis.specific_claims += sum(1 for word in self.specificity_indicators if word in query)
                
                # Count general mentions
                if search.results_count > 0:
                    analysis.general_mentions += 1
        
        return analysis
    
    def _calculate_information_coverage(self, session: 'InvestigationSession', content_analysis: ContentAnalysis) -> float:
        """Calculate how well the investigation covers the topic (0-1)"""
        
        # Base coverage on variety of search approaches tried
        unique_search_terms = set()
        for search in session.search_history:
            query = search.params.get('query', '')
            unique_search_terms.add(query.lower())
        
        # Coverage dimensions for debunking investigations
        coverage_aspects = {
            'direct_debunking': any('debunk' in term for term in unique_search_terms),
            'hoax_analysis': any('hoax' in term for term in unique_search_terms), 
            'fact_checking': any('fact' in term for term in unique_search_terms),
            'expert_analysis': any('expert' in term or 'analysis' in term for term in unique_search_terms),
            'credibility_assessment': any('credibility' in term or 'reliable' in term for term in unique_search_terms),
            'specific_claims': content_analysis.specific_claims > 0,
            'general_context': content_analysis.general_mentions > 2,
            'alternative_angles': len(unique_search_terms) > 5
        }
        
        # Calculate coverage score
        coverage_score = sum(coverage_aspects.values()) / len(coverage_aspects)
        
        # Boost if we found actual results
        if session.total_results_found > 10:
            coverage_score = min(1.0, coverage_score * 1.2)
        
        return coverage_score
    
    def _calculate_source_diversity(self, session: 'InvestigationSession') -> float:
        """Calculate diversity of information sources (0-1)"""
        
        # Count different types of searches attempted
        search_types = set()
        for search in session.search_history:
            query = search.params.get('query', '').lower()
            
            # Categorize search types
            if any(word in query for word in ['#', 'hashtag']):
                search_types.add('hashtag_search')
            elif '"' in query:
                search_types.add('exact_phrase')
            elif any(word in query for word in self.expert_indicators):
                search_types.add('expert_search')
            elif any(word in query for word in self.credibility_keywords):
                search_types.add('fact_check_search')
            elif any(word in query for word in self.skeptical_keywords):
                search_types.add('skeptical_search')
            else:
                search_types.add('general_search')
        
        # Diversity score based on search type variety
        max_diversity_types = 6
        diversity_score = len(search_types) / max_diversity_types
        
        # Boost for successful result diversity
        successful_searches = [s for s in session.search_history if s.results_count > 0]
        if len(successful_searches) > 1:
            diversity_score = min(1.0, diversity_score * 1.3)
        
        return diversity_score
    
    def _calculate_evidence_quality(self, session: 'InvestigationSession', content_analysis: ContentAnalysis) -> float:
        """Calculate quality of evidence found (0-1)"""
        
        quality_factors = []
        
        # Factor 1: Presence of credibility signals
        credibility_score = min(1.0, content_analysis.credibility_signals / 3.0)
        quality_factors.append(credibility_score)
        
        # Factor 2: Fact-checking sources
        fact_check_score = min(1.0, content_analysis.fact_check_mentions / 2.0)
        quality_factors.append(fact_check_score)
        
        # Factor 3: Expert voices
        expert_score = min(1.0, content_analysis.expert_voices / 2.0)
        quality_factors.append(expert_score)
        
        # Factor 4: Search effectiveness (proxy for result quality)
        effective_searches = [s for s in session.search_history if s.effectiveness_score > 5.0]
        effectiveness_score = min(1.0, len(effective_searches) / max(1, len(session.search_history)))
        quality_factors.append(effectiveness_score)
        
        # Average quality across factors
        return sum(quality_factors) / len(quality_factors)
    
    def _calculate_claim_specificity(self, content_analysis: ContentAnalysis) -> float:
        """Calculate how specific vs general the findings are (0-1)"""
        
        total_findings = content_analysis.specific_claims + content_analysis.general_mentions
        if total_findings == 0:
            return 0.0
        
        # Ratio of specific to general findings
        specificity_ratio = content_analysis.specific_claims / total_findings
        
        # Boost if we have evidence-based content
        if content_analysis.credibility_signals > 0:
            specificity_ratio = min(1.0, specificity_ratio * 1.5)
        
        return specificity_ratio
    
    def _calculate_contradiction_resolution(self, session: 'InvestigationSession', content_analysis: ContentAnalysis) -> float:
        """Calculate how well contradictions and disputes are addressed (0-1)"""
        
        # Check if investigation found both supporting and opposing views
        has_skeptical_content = content_analysis.skeptical_indicators > 0
        has_credibility_analysis = content_analysis.credibility_signals > 0
        
        resolution_factors = []
        
        # Factor 1: Presence of both perspectives
        if has_skeptical_content and has_credibility_analysis:
            resolution_factors.append(0.8)
        elif has_skeptical_content or has_credibility_analysis:
            resolution_factors.append(0.5)
        else:
            resolution_factors.append(0.2)
        
        # Factor 2: Evidence-based analysis
        if content_analysis.fact_check_mentions > 0:
            resolution_factors.append(0.7)
        else:
            resolution_factors.append(0.3)
        
        # Factor 3: Multiple search angles attempted
        unique_approaches = len(set(s.params.get('query', '') for s in session.search_history))
        approach_score = min(1.0, unique_approaches / 8.0)  # 8 different approaches = full score
        resolution_factors.append(approach_score)
        
        return sum(resolution_factors) / len(resolution_factors)
    
    def assess_search_round_quality(self, searches: List[SearchAttempt]) -> Dict[str, Any]:
        """Assess the quality of a specific round of searches"""
        
        round_assessment = {
            'total_results': sum(s.results_count for s in searches),
            'avg_effectiveness': sum(s.effectiveness_score for s in searches) / len(searches) if searches else 0,
            'successful_searches': len([s for s in searches if s.effectiveness_score > 5.0]),
            'failed_searches': len([s for s in searches if s.effectiveness_score < 2.0]),
            'round_quality_score': 0.0,
            'insights': [],
            'recommendations': []
        }
        
        # Calculate round quality score
        if searches:
            effectiveness_component = round_assessment['avg_effectiveness'] / 10.0
            success_component = round_assessment['successful_searches'] / len(searches)
            results_component = min(1.0, round_assessment['total_results'] / 20.0)  # 20 results = max score
            
            round_assessment['round_quality_score'] = (
                effectiveness_component * 0.4 +
                success_component * 0.3 + 
                results_component * 0.3
            )
        
        # Generate insights
        if round_assessment['successful_searches'] > 0:
            round_assessment['insights'].append(f"Found {round_assessment['total_results']} relevant results")
        
        if round_assessment['failed_searches'] > len(searches) / 2:
            round_assessment['insights'].append("Many searches yielded no results - consider broader terms")
        
        # Generate recommendations
        if round_assessment['round_quality_score'] < 0.3:
            round_assessment['recommendations'].append("Try alternative search approaches")
            round_assessment['recommendations'].append("Consider broader or more specific terms")
        
        return round_assessment
    
    def generate_satisfaction_report(self, session: 'InvestigationSession') -> str:
        """Generate human-readable satisfaction report"""
        
        metrics = self.assess_investigation_satisfaction(session)
        content_analysis = self._analyze_search_content(session)
        
        report_parts = []
        report_parts.append("📊 **INVESTIGATION SATISFACTION REPORT**")
        report_parts.append("=" * 50)
        
        # Overall satisfaction
        overall = metrics.overall_satisfaction()
        satisfaction_level = (
            "Excellent" if overall > 0.8 else
            "Good" if overall > 0.6 else
            "Fair" if overall > 0.4 else
            "Poor"
        )
        
        report_parts.append(f"**Overall Satisfaction:** {overall:.1%} ({satisfaction_level})")
        report_parts.append("")
        
        # Detailed metrics
        report_parts.append("**Detailed Assessment:**")
        report_parts.append(f"• Information Coverage: {metrics.information_coverage:.1%}")
        report_parts.append(f"• Source Diversity: {metrics.source_diversity:.1%}") 
        report_parts.append(f"• Evidence Quality: {metrics.evidence_quality:.1%}")
        report_parts.append(f"• Claim Specificity: {metrics.claim_specificity:.1%}")
        report_parts.append(f"• Contradiction Resolution: {metrics.contradiction_resolution:.1%}")
        report_parts.append("")
        
        # Content analysis summary
        report_parts.append("**Content Analysis:**")
        report_parts.append(f"• Skeptical Indicators Found: {content_analysis.skeptical_indicators}")
        report_parts.append(f"• Credibility Signals: {content_analysis.credibility_signals}")
        report_parts.append(f"• Fact-Check References: {content_analysis.fact_check_mentions}")
        report_parts.append(f"• Expert Voice Indicators: {content_analysis.expert_voices}")
        report_parts.append("")
        
        # Recommendations
        report_parts.append("**Recommendations:**")
        if overall < 0.5:
            report_parts.append("• Continue investigation with different search strategies")
            report_parts.append("• Try more specific search terms or alternative platforms")
        elif overall < 0.8:
            report_parts.append("• Good progress - consider drilling deeper into promising leads")
            report_parts.append("• Look for more specific evidence or expert analysis")
        else:
            report_parts.append("• Investigation appears comprehensive")
            report_parts.append("• Consider concluding or exploring remaining edge cases")
        
        return "\n".join(report_parts)
    
    def should_continue_investigation(self, session: 'InvestigationSession') -> Tuple[bool, str, List[str]]:
        """Determine if investigation should continue with specific reasons and suggestions"""
        
        metrics = self.assess_investigation_satisfaction(session)
        overall_satisfaction = metrics.overall_satisfaction()
        
        # Reasons to continue
        continue_reasons = []
        suggestions = []
        
        if overall_satisfaction < session.config.satisfaction_threshold:
            if metrics.information_coverage < 0.6:
                continue_reasons.append("Incomplete topic coverage")
                suggestions.append("Try broader search terms or alternative angles")
            
            if metrics.source_diversity < 0.5:
                continue_reasons.append("Limited source diversity")
                suggestions.append("Search different communities or expert sources")
            
            if metrics.evidence_quality < 0.5:
                continue_reasons.append("Low evidence quality")
                suggestions.append("Look for fact-checking sources or expert analysis")
            
            if metrics.claim_specificity < 0.4:
                continue_reasons.append("Findings too general")
                suggestions.append("Search for specific claims or evidence")
        
        # Check if we're making progress
        if len(session.satisfaction_history) >= 3:
            recent_trend = session.satisfaction_history[-1] - session.satisfaction_history[-3]
            if recent_trend < 0.05:  # Less than 5% improvement
                continue_reasons.append("Progress has stalled")
                suggestions.append("Try completely different search strategy")
        
        should_continue = len(continue_reasons) > 0 and session.search_count < session.config.max_searches
        
        if not should_continue and overall_satisfaction >= session.config.satisfaction_threshold:
            reason = f"Investigation satisfied (score: {overall_satisfaction:.1%})"
        elif not should_continue:
            reason = "Investigation exhausted without full satisfaction"
        else:
            reason = f"Continuing investigation: {', '.join(continue_reasons)}"
        
        return should_continue, reason, suggestions