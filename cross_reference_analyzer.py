"""Cross-Reference Pattern Detection for Twitter Explorer Investigation System"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import json
import re
from collections import defaultdict, Counter

@dataclass
class Pattern:
    """Represents a detected pattern across multiple findings"""
    pattern_type: str  # 'entity_cluster', 'claim_consistency', 'temporal_trend', 'source_correlation'
    entities_involved: List[str]
    supporting_findings: List[str]  # Finding content snippets
    confidence_score: float  # 0.0-1.0
    description: str
    evidence_count: int
    strength: str  # 'weak', 'medium', 'strong'

@dataclass
class Contradiction:
    """Represents a contradiction between findings"""
    conflicting_claims: Tuple[str, str]
    supporting_evidence: Tuple[List[str], List[str]]
    contradiction_type: str  # 'factual', 'opinion', 'temporal', 'source_based'
    severity: float  # 0.0-1.0
    resolution_needed: bool
    affected_entities: List[str]

@dataclass
class CredibilityConflict:
    """Represents conflicts in source credibility assessment"""
    source_name: str
    credibility_scores: List[float]
    conflicting_assessments: List[str]
    resolution_confidence: float
    recommended_credibility: float

@dataclass
class CrossReferenceAnalysis:
    """Complete cross-reference analysis of investigation findings"""
    patterns: List[Pattern] = field(default_factory=list)
    contradictions: List[Contradiction] = field(default_factory=list)
    credibility_conflicts: List[CredibilityConflict] = field(default_factory=list)
    confidence_score: float = 0.0
    entity_frequency: Dict[str, int] = field(default_factory=dict)
    source_reliability_map: Dict[str, float] = field(default_factory=dict)
    temporal_consistency: float = 0.0
    overall_coherence: float = 0.0

class CrossReferenceAnalyzer:
    """Analyzes relationships, patterns, and contradictions across investigation findings"""
    
    def __init__(self, llm_client=None, model_manager=None):
        if llm_client is None:
            from llm_client import get_litellm_client
            self.llm_client = get_litellm_client()
        else:
            self.llm_client = llm_client
        
        # Initialize model manager
        if model_manager is None:
            from llm_model_manager import LLMModelManager
            self.model_manager = LLMModelManager()
        else:
            self.model_manager = model_manager
            
        # Entity extraction patterns
        self.entity_patterns = {
            'person': r'@\w+|[A-Z][a-z]+\s+[A-Z][a-z]+',
            'organization': r'[A-Z]{2,}|[A-Z][a-zA-Z]+\s+(Inc|Corp|LLC|Ltd|Foundation|Institute)',
            'location': r'\b[A-Z][a-z]+,?\s+[A-Z][a-z]+\b',
            'hashtag': r'#\w+',
            'url': r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }
        
    def analyze_findings(self, findings: List[Any], investigation_goal: str) -> CrossReferenceAnalysis:
        """
        Main method to perform cross-reference analysis on investigation findings
        
        Args:
            findings: List of Finding objects from investigation
            investigation_goal: Original investigation query for context
            
        Returns:
            CrossReferenceAnalysis with detected patterns and contradictions
        """
        analysis = CrossReferenceAnalysis()
        
        if len(findings) < 2:
            analysis.confidence_score = 0.0
            return analysis
            
        # Extract entities from all findings
        entities_per_finding = self._extract_entities_from_findings(findings)
        analysis.entity_frequency = self._calculate_entity_frequency(entities_per_finding)
        
        # Detect patterns
        analysis.patterns = self._detect_patterns(findings, entities_per_finding, investigation_goal)
        
        # Detect contradictions using LLM
        analysis.contradictions = self._detect_contradictions_with_llm(findings, investigation_goal)
        
        # Analyze source credibility
        analysis.credibility_conflicts = self._analyze_source_credibility(findings)
        analysis.source_reliability_map = self._build_source_reliability_map(findings)
        
        # Calculate overall metrics
        analysis.temporal_consistency = self._calculate_temporal_consistency(findings)
        analysis.overall_coherence = self._calculate_overall_coherence(analysis)
        analysis.confidence_score = self._calculate_confidence_score(analysis, len(findings))
        
        return analysis
    
    def _extract_entities_from_findings(self, findings: List[Any]) -> Dict[int, Dict[str, Set[str]]]:
        """Extract entities from each finding using regex patterns"""
        entities_per_finding = {}
        
        for idx, finding in enumerate(findings):
            content = getattr(finding, 'content', '')
            entities_per_finding[idx] = {
                'person': set(),
                'organization': set(),
                'location': set(),
                'hashtag': set(),
                'url': set()
            }
            
            for entity_type, pattern in self.entity_patterns.items():
                matches = re.findall(pattern, content)
                entities_per_finding[idx][entity_type].update(matches)
                
        return entities_per_finding
        
    def _calculate_entity_frequency(self, entities_per_finding: Dict[int, Dict[str, Set[str]]]) -> Dict[str, int]:
        """Calculate frequency of entities across all findings"""
        frequency = Counter()
        
        for finding_entities in entities_per_finding.values():
            for entity_type, entities in finding_entities.items():
                for entity in entities:
                    frequency[entity] += 1
                    
        return dict(frequency)
        
    def _detect_patterns(self, findings: List[Any], entities_per_finding: Dict[int, Dict[str, Set[str]]], investigation_goal: str) -> List[Pattern]:
        """Detect various types of patterns in the findings"""
        patterns = []
        
        # Entity cluster patterns - entities that appear together frequently
        entity_clusters = self._detect_entity_clusters(entities_per_finding)
        for cluster in entity_clusters:
            if len(cluster['entities']) >= 2 and cluster['frequency'] >= 2:
                patterns.append(Pattern(
                    pattern_type='entity_cluster',
                    entities_involved=cluster['entities'],
                    supporting_findings=cluster['supporting_findings'],
                    confidence_score=min(1.0, cluster['frequency'] / len(findings)),
                    description=f"Entities {', '.join(cluster['entities'])} frequently appear together",
                    evidence_count=cluster['frequency'],
                    strength='strong' if cluster['frequency'] >= 3 else 'medium'
                ))
        
        # Temporal trend patterns - if timestamps are available
        temporal_patterns = self._detect_temporal_patterns(findings)
        patterns.extend(temporal_patterns)
        
        # Source correlation patterns
        source_patterns = self._detect_source_patterns(findings)
        patterns.extend(source_patterns)
        
        return patterns
        
    def _detect_entity_clusters(self, entities_per_finding: Dict[int, Dict[str, Set[str]]]) -> List[Dict]:
        """Detect clusters of entities that appear together across findings"""
        clusters = []
        entity_co_occurrence = defaultdict(lambda: defaultdict(int))
        
        # Count entity co-occurrences
        for finding_entities in entities_per_finding.values():
            all_entities = set()
            for entity_type, entities in finding_entities.items():
                all_entities.update(entities)
                
            # Record co-occurrences
            entities_list = list(all_entities)
            for i, entity1 in enumerate(entities_list):
                for entity2 in entities_list[i+1:]:
                    entity_co_occurrence[entity1][entity2] += 1
                    entity_co_occurrence[entity2][entity1] += 1
        
        # Find clusters with significant co-occurrence
        processed_entities = set()
        for entity1, co_entities in entity_co_occurrence.items():
            if entity1 in processed_entities:
                continue
                
            cluster_entities = [entity1]
            supporting_findings = []
            total_frequency = 0
            
            for entity2, frequency in co_entities.items():
                if frequency >= 2:  # Minimum co-occurrence threshold
                    cluster_entities.append(entity2)
                    processed_entities.add(entity2)
                    total_frequency += frequency
                    
            if len(cluster_entities) > 1:
                # Find supporting findings for this cluster
                for idx, finding_entities in entities_per_finding.items():
                    all_entities = set()
                    for entities in finding_entities.values():
                        all_entities.update(entities)
                    
                    if any(entity in all_entities for entity in cluster_entities):
                        finding_content = findings[idx].content if hasattr(findings[idx], 'content') else ''
                        supporting_findings.append(finding_content[:100] + "..." if len(finding_content) > 100 else finding_content)
                
                clusters.append({
                    'entities': cluster_entities,
                    'frequency': total_frequency,
                    'supporting_findings': supporting_findings[:5]  # Limit to top 5
                })
                processed_entities.add(entity1)
                
        return clusters
        
    def _detect_temporal_patterns(self, findings: List[Any]) -> List[Pattern]:
        """Detect temporal patterns in findings (if timestamp information is available)"""
        patterns = []
        # Implementation would analyze timestamps if available in findings
        # For now, return empty list as timestamp extraction needs to be implemented
        return patterns
        
    def _detect_source_patterns(self, findings: List[Any]) -> List[Pattern]:
        """Detect patterns related to sources"""
        patterns = []
        source_frequency = Counter()
        
        for finding in findings:
            source = getattr(finding, 'source', 'unknown')
            source_frequency[source] += 1
            
        # Detect dominant sources
        total_findings = len(findings)
        for source, count in source_frequency.items():
            if count >= 3 and count / total_findings >= 0.2:  # At least 20% of findings
                supporting_findings = []
                for finding in findings:
                    if getattr(finding, 'source', '') == source:
                        content = getattr(finding, 'content', '')
                        supporting_findings.append(content[:100] + "..." if len(content) > 100 else content)
                
                patterns.append(Pattern(
                    pattern_type='source_correlation',
                    entities_involved=[source],
                    supporting_findings=supporting_findings[:5],
                    confidence_score=count / total_findings,
                    description=f"Source '{source}' dominates with {count} findings ({count/total_findings:.1%})",
                    evidence_count=count,
                    strength='strong' if count >= 5 else 'medium'
                ))
                
        return patterns
        
    def _detect_contradictions_with_llm(self, findings: List[Any], investigation_goal: str) -> List[Contradiction]:
        """Use LLM to detect semantic contradictions between findings"""
        contradictions = []
        
        if len(findings) < 2:
            return contradictions
            
        # Limit analysis to prevent excessive LLM calls
        findings_to_analyze = findings[:10]  # Analyze first 10 findings
        
        try:
            findings_text = []
            for i, finding in enumerate(findings_to_analyze):
                content = getattr(finding, 'content', '')
                source = getattr(finding, 'source', 'unknown')
                findings_text.append(f"Finding {i+1} (from {source}): {content[:200]}")
            
            contradiction_prompt = f"""
            Analyze these findings from an investigation about "{investigation_goal}" for contradictions.
            
            Findings:
            {chr(10).join(findings_text)}
            
            Identify any contradictions between the findings. Look for:
            1. Factual contradictions (different claims about the same facts)
            2. Opinion conflicts (opposing viewpoints)
            3. Temporal inconsistencies (timeline conflicts)
            
            Return a JSON array of contradictions with this structure:
            [{{
                "conflicting_claims": ["claim1", "claim2"],
                "contradiction_type": "factual|opinion|temporal",
                "severity": 0.8,
                "evidence": [["supporting evidence 1"], ["supporting evidence 2"]],
                "affected_entities": ["entity1", "entity2"]
            }}]
            
            If no contradictions found, return empty array: []
            """
            
            model = self.model_manager.get_model_for_operation("cross_reference")
            response = self.llm_client.completion(
                model=model,
                messages=[{"role": "user", "content": contradiction_prompt}]
            )
            
            response_content = response.choices[0].message.content
            contradiction_data = json.loads(response_content)
            
            # Handle different possible response formats
            if isinstance(contradiction_data, dict) and 'contradictions' in contradiction_data:
                contradiction_list = contradiction_data['contradictions']
            elif isinstance(contradiction_data, list):
                contradiction_list = contradiction_data
            else:
                contradiction_list = []
            
            for item in contradiction_list:
                if isinstance(item, dict) and 'conflicting_claims' in item:
                    contradictions.append(Contradiction(
                        conflicting_claims=(item['conflicting_claims'][0], item['conflicting_claims'][1]),
                        supporting_evidence=(item.get('evidence', [[], []])[0], item.get('evidence', [[], []])[1]),
                        contradiction_type=item.get('contradiction_type', 'factual'),
                        severity=float(item.get('severity', 0.5)),
                        resolution_needed=item.get('severity', 0.5) > 0.6,
                        affected_entities=item.get('affected_entities', [])
                    ))
                    
        except Exception as e:
            print(f"Error in LLM contradiction detection: {e}")
            # Continue without contradictions rather than failing
            
        return contradictions
        
    def _analyze_source_credibility(self, findings: List[Any]) -> List[CredibilityConflict]:
        """Analyze credibility conflicts between sources"""
        conflicts = []
        source_credibility = defaultdict(list)
        
        for finding in findings:
            source = getattr(finding, 'source', 'unknown')
            credibility = getattr(finding, 'credibility_score', 0.5)
            source_credibility[source].append(credibility)
            
        for source, scores in source_credibility.items():
            if len(scores) > 1:
                score_variance = max(scores) - min(scores)
                if score_variance > 0.3:  # Significant variance threshold
                    conflicts.append(CredibilityConflict(
                        source_name=source,
                        credibility_scores=scores,
                        conflicting_assessments=[f"Score range: {min(scores):.2f} - {max(scores):.2f}"],
                        resolution_confidence=1.0 - score_variance,
                        recommended_credibility=sum(scores) / len(scores)
                    ))
                    
        return conflicts
        
    def _build_source_reliability_map(self, findings: List[Any]) -> Dict[str, float]:
        """Build a reliability map for all sources"""
        source_reliability = {}
        source_scores = defaultdict(list)
        
        for finding in findings:
            source = getattr(finding, 'source', 'unknown')
            credibility = getattr(finding, 'credibility_score', 0.5)
            source_scores[source].append(credibility)
            
        for source, scores in source_scores.items():
            source_reliability[source] = sum(scores) / len(scores)
            
        return source_reliability
        
    def _calculate_temporal_consistency(self, findings: List[Any]) -> float:
        """Calculate temporal consistency score (placeholder implementation)"""
        # Would analyze timestamp consistency if available
        return 0.8  # Default assumption of good temporal consistency
        
    def _calculate_overall_coherence(self, analysis: CrossReferenceAnalysis) -> float:
        """Calculate overall coherence score based on patterns and contradictions"""
        pattern_score = min(1.0, len(analysis.patterns) * 0.2)  # More patterns = higher coherence
        contradiction_penalty = min(1.0, len(analysis.contradictions) * 0.3)  # More contradictions = lower coherence
        credibility_penalty = min(1.0, len(analysis.credibility_conflicts) * 0.2)
        
        coherence = max(0.0, 0.7 + pattern_score - contradiction_penalty - credibility_penalty)
        return coherence
        
    def _calculate_confidence_score(self, analysis: CrossReferenceAnalysis, num_findings: int) -> float:
        """Calculate overall confidence score for the cross-reference analysis"""
        if num_findings < 2:
            return 0.0
            
        # Base confidence from number of findings
        findings_confidence = min(1.0, num_findings / 10.0)
        
        # Pattern detection confidence
        pattern_confidence = min(1.0, len(analysis.patterns) * 0.15)
        
        # Reliability based on coherence
        coherence_confidence = analysis.overall_coherence
        
        # Entity frequency confidence (more entities = more confidence)
        entity_confidence = min(1.0, len(analysis.entity_frequency) * 0.05)
        
        overall_confidence = (
            findings_confidence * 0.3 +
            pattern_confidence * 0.25 + 
            coherence_confidence * 0.3 +
            entity_confidence * 0.15
        )
        
        return min(1.0, overall_confidence)