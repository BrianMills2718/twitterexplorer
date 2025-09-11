# investigation_graph.py
"""
Core Graph Data Structures for Strategic Investigation System

This implements a graph-based architecture where every piece of information 
is retained and connected in a living investigation graph, enabling strategic
coherence and full context awareness.
"""

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
from enum import Enum


class NodeType(Enum):
    """Enumeration of node types in the investigation graph"""
    ANALYTIC_QUESTION = 'analytic_question'
    INVESTIGATION_QUESTION = 'investigation_question'
    SEARCH_QUERY = 'search_query'
    DATAPOINT = 'datapoint'
    INSIGHT = 'insight'
    EMERGENT_QUESTION = 'emergent_question'

@dataclass
class Node:
    """Base node in the investigation graph"""
    id: str
    node_type: str  # AnalyticQuestion, InvestigationQuestion, SearchQuery, DataPoint, Insight, EmergentQuestion
    properties: Dict[str, Any]
    created_at: datetime
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary"""
        return cls(**data)

@dataclass  
class Edge:
    """Edge connecting nodes in the investigation graph"""
    id: str
    source_id: str
    target_id: str
    edge_type: str  # MOTIVATES, OPERATIONALIZES, GENERATES, SUPPORTS, ANSWERS, SPAWNS, etc.
    properties: Dict[str, Any]
    created_at: datetime
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary for serialization"""
        result = asdict(self)
        result['created_at'] = self.created_at.isoformat()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create edge from dictionary"""
        return cls(**data)

@dataclass
class AnalyticQuestionNode(Node):
    """Root question driving the investigation"""
    def __init__(self, text: str, **kwargs):
        super().__init__(
            id=str(uuid.uuid4()),
            node_type="AnalyticQuestion",
            properties={"text": text, **kwargs},
            created_at=datetime.now()
        )
    
    @property
    def text(self) -> str:
        return self.properties["text"]

@dataclass
class InvestigationQuestionNode(Node):
    """Specific question that operationalizes the analytic question"""
    def __init__(self, text: str, parent_analytic_question: str = None, **kwargs):
        super().__init__(
            id=str(uuid.uuid4()),
            node_type="InvestigationQuestion", 
            properties={"text": text, "parent_analytic_question": parent_analytic_question, **kwargs},
            created_at=datetime.now()
        )
    
    @property
    def text(self) -> str:
        return self.properties["text"]
    
    @property
    def parent_analytic_question(self) -> str:
        return self.properties.get("parent_analytic_question")

@dataclass
class SearchQueryNode(Node):
    """Executable search query against an API endpoint"""
    def __init__(self, endpoint: str, parameters: Dict[str, Any], **kwargs):
        super().__init__(
            id=str(uuid.uuid4()),
            node_type="SearchQuery",
            properties={"endpoint": endpoint, "parameters": parameters, **kwargs},
            created_at=datetime.now()
        )
    
    @property
    def endpoint(self) -> str:
        return self.properties["endpoint"]
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return self.properties["parameters"]

@dataclass
class DataPointNode(Node):
    """Individual piece of data/evidence from search results"""
    def __init__(self, content: str, source_info: Dict[str, Any], **kwargs):
        super().__init__(
            id=str(uuid.uuid4()),
            node_type="DataPoint",
            properties={"content": content, "source_info": source_info, **kwargs},
            created_at=datetime.now()
        )
    
    @property
    def content(self) -> str:
        return self.properties["content"]
    
    @property
    def source_info(self) -> Dict[str, Any]:
        return self.properties["source_info"]

@dataclass
class InsightNode(Node):
    """Insight or pattern derived from analysis of data points"""
    def __init__(self, content: str, insight_type: str, **kwargs):
        super().__init__(
            id=str(uuid.uuid4()),
            node_type="Insight",
            properties={"content": content, "insight_type": insight_type, **kwargs},
            created_at=datetime.now()
        )
    
    @property
    def content(self) -> str:
        return self.properties["content"]
    
    @property
    def insight_type(self) -> str:
        return self.properties["insight_type"]

@dataclass
class EmergentQuestionNode(Node):
    """New question that emerged during investigation"""
    def __init__(self, text: str, emergence_reason: str, **kwargs):
        super().__init__(
            id=str(uuid.uuid4()),
            node_type="EmergentQuestion",
            properties={"text": text, "emergence_reason": emergence_reason, **kwargs},
            created_at=datetime.now()
        )
    
    @property
    def text(self) -> str:
        return self.properties["text"]
    
    @property
    def emergence_reason(self) -> str:
        return self.properties["emergence_reason"]

class InvestigationGraph:
    """
    Graph-based investigation system that retains all information and relationships
    for strategic coherence and full context awareness.
    """
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.analytic_question: Optional[Node] = None
        
        # Performance indexes
        self._edges_by_source: Dict[str, List[Edge]] = defaultdict(list)
        self._edges_by_target: Dict[str, List[Edge]] = defaultdict(list) 
        self._nodes_by_type: Dict[str, List[Node]] = defaultdict(list)
    
    # Node creation methods
    def create_analytic_question_node(self, text: str, **kwargs) -> AnalyticQuestionNode:
        """Create the root analytic question for this investigation"""
        node = AnalyticQuestionNode(text, **kwargs)
        self.nodes[node.id] = node
        self._nodes_by_type["AnalyticQuestion"].append(node)
        
        # Set as the primary analytic question
        if self.analytic_question is None:
            self.analytic_question = node
            
        return node
    
    def create_investigation_question_node(self, text: str, parent_id: str = None) -> InvestigationQuestionNode:
        """Create an investigation question that operationalizes the analytic question"""
        if parent_id is None and self.analytic_question:
            parent_id = self.analytic_question.id
            
        node = InvestigationQuestionNode(text, parent_id)
        self.nodes[node.id] = node
        self._nodes_by_type["InvestigationQuestion"].append(node)
        
        return node
    
    def create_search_query_node(self, endpoint: str, parameters: Dict[str, Any]) -> SearchQueryNode:
        """Create a search query node representing an API call"""
        node = SearchQueryNode(endpoint, parameters)
        self.nodes[node.id] = node
        self._nodes_by_type["SearchQuery"].append(node)
        return node
    
    def create_data_point_node(self, content: str, source_info: Dict[str, Any]) -> DataPointNode:
        """Create a data point from search results"""
        node = DataPointNode(content, source_info)
        self.nodes[node.id] = node
        self._nodes_by_type["DataPoint"].append(node)
        return node
    
    def create_insight_node(self, content: str, insight_type: str) -> InsightNode:
        """Create an insight derived from analysis"""
        node = InsightNode(content, insight_type)
        self.nodes[node.id] = node
        self._nodes_by_type["Insight"].append(node)
        return node
    
    def create_emergent_question_node(self, text: str, emergence_reason: str) -> EmergentQuestionNode:
        """Create an emergent question that arose during investigation"""
        node = EmergentQuestionNode(text, emergence_reason)
        self.nodes[node.id] = node
        self._nodes_by_type["EmergentQuestion"].append(node)
        return node
    
    # Enhanced DataPoint and Insight methods for tests
    def create_datapoint_node(self, content: str, source: str, timestamp: str = None, **kwargs) -> 'DataPointNodeWrapper':
        """Create a DataPoint node with enhanced attributes"""
        source_info = {'source': source}
        if timestamp:
            source_info['timestamp'] = timestamp
        source_info.update(kwargs)
        
        node = self.create_data_point_node(content, source_info)
        
        # Return a wrapper for test compatibility
        return DataPointNodeWrapper(node, self)
    
    def create_insight_node_enhanced(self, content: str, confidence: float, supporting_datapoints: List[str], title: str = None) -> 'InsightNodeWrapper':
        """Create an Insight node with confidence, supporting datapoints, and title"""
        node = self.create_insight_node(content, "derived")
        
        # Add enhanced attributes
        node.properties['confidence'] = confidence
        node.properties['supporting_datapoints'] = supporting_datapoints
        
        # CRITICAL FIX: Set title if provided to prevent "Untitled" insights
        if title and title.strip():
            node.properties['title'] = title.strip()
        
        # Create edges from datapoints to this insight
        for dp_id in supporting_datapoints:
            if dp_id in self.nodes:
                self.create_edge(self.nodes[dp_id], node, "SUPPORTS")
        
        return InsightNodeWrapper(node, self)
    
    def create_datapoints_from_search(self, search_result: Dict[str, Any]) -> List['DataPointNodeWrapper']:
        """Create DataPoint nodes from search results"""
        datapoints = []
        
        endpoint = search_result.get('endpoint', 'unknown')
        query = search_result.get('query', '')
        results = search_result.get('results', [])
        
        for result in results:
            content = result.get('text', str(result))
            source_info = {
                'source': endpoint,
                'query': query,
                'author': result.get('author', 'unknown')
            }
            
            node = self.create_data_point_node(content, source_info)
            datapoints.append(DataPointNodeWrapper(node, self))
        
        return datapoints
    
    def generate_insight_from_datapoints(self, datapoints: List['DataPointNodeWrapper'], insight_text: str) -> 'InsightNodeWrapper':
        """Generate an insight from a list of DataPoint nodes"""
        # Extract IDs from wrapper objects
        dp_ids = []
        for dp in datapoints:
            if hasattr(dp, 'node'):
                dp_ids.append(dp.node.id)
            elif hasattr(dp, 'id'):
                dp_ids.append(dp.id)
        
        # Calculate confidence based on number of supporting datapoints
        confidence = min(0.9, 0.5 + (len(dp_ids) * 0.08))
        
        return self.create_insight_node_enhanced(insight_text, confidence, dp_ids)
    
    # Edge creation methods
    def create_edge(self, source: Node, target: Node, edge_type: str, properties: Dict[str, Any] = None) -> Edge:
        """Create an edge connecting two nodes with validation"""
        if properties is None:
            properties = {}
        
        # Validate nodes exist
        if source is None or target is None:
            raise ValueError("Cannot create edge with None source or target")
        
        if not hasattr(source, 'id') or not hasattr(target, 'id'):
            raise ValueError("Invalid node objects for edge creation")
        
        # Validate nodes are in graph
        if source.id not in self.nodes:
            raise ValueError(f"Source node {source.id} not in graph")
        if target.id not in self.nodes:
            raise ValueError(f"Target node {target.id} not in graph")
            
        edge = Edge(
            id=str(uuid.uuid4()),
            source_id=source.id,
            target_id=target.id, 
            edge_type=edge_type,
            properties=properties,
            created_at=datetime.now()
        )
        
        self.edges.append(edge)
        self._edges_by_source[source.id].append(edge)
        self._edges_by_target[target.id].append(edge)
        
        return edge
    
    # Query methods
    def get_nodes_by_type(self, node_type: str) -> List[Node]:
        """Get all nodes of a specific type"""
        return self._nodes_by_type.get(node_type, [])
    
    def find_search_query_node(self, endpoint: str, parameters: Dict[str, Any]) -> Optional[Node]:
        """Find existing SearchQuery node by endpoint and parameters"""
        search_nodes = self.get_nodes_by_type("SearchQuery")
        for node in search_nodes:
            if (node.properties.get("endpoint") == endpoint and 
                node.properties.get("parameters") == parameters):
                return node
        return None
    
    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Get edges originating from a node"""
        return self._edges_by_source.get(node_id, [])
    
    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """Get edges targeting a node"""
        return self._edges_by_target.get(node_id, [])
    
    def get_connected_nodes(self, node_id: str) -> List[Node]:
        """Get all nodes connected to this node"""
        connected = set()
        
        for edge in self.get_outgoing_edges(node_id):
            if edge.target_id in self.nodes:
                connected.add(edge.target_id)
        
        for edge in self.get_incoming_edges(node_id):
            if edge.source_id in self.nodes:
                connected.add(edge.source_id)
        
        return [self.nodes[node_id] for node_id in connected]
    
    # Strategic analysis methods
    def get_information_gaps(self) -> List[str]:
        """Identify information gaps in the investigation"""
        gaps = []
        
        # Find investigation questions without supporting data
        investigation_questions = self.get_nodes_by_type("InvestigationQuestion")
        
        for q_node in investigation_questions:
            # Check if this question has been operationalized with searches
            outgoing_edges = self.get_outgoing_edges(q_node.id)
            search_edges = [e for e in outgoing_edges if e.edge_type == "OPERATIONALIZES"]
            
            if not search_edges:
                gaps.append(f"Question '{q_node.text}' has no search strategy")
                continue
            
            # Check if searches have generated data
            has_data = False
            for edge in search_edges:
                search_node = self.nodes[edge.target_id]
                search_outgoing = self.get_outgoing_edges(search_node.id)
                data_edges = [e for e in search_outgoing if e.edge_type == "GENERATES"]
                if data_edges:
                    has_data = True
                    break
            
            if not has_data:
                gaps.append(f"Question '{q_node.text}' searches yielded no data")
        
        # Check for obvious missing aspects if we have analytic question
        if self.analytic_question:
            goal_text = self.analytic_question.text.lower()
            
            # Check for missing perspectives on controversial topics
            if "trump" in goal_text and "epstein" in goal_text:
                trump_covered = any("trump" in node.properties.get("text", "").lower() 
                                  for node in investigation_questions)
                epstein_covered = any("epstein" in node.properties.get("text", "").lower() 
                                    for node in investigation_questions) 
                
                if not trump_covered:
                    gaps.append("Missing investigation into Trump's perspective/statements")
                if not epstein_covered:
                    gaps.append("Missing investigation into Epstein background/context")
        
        return gaps if gaps else ["Continue building comprehensive understanding"]
    
    def get_disconnected_threads(self) -> List[List[Node]]:
        """Find groups of nodes that aren't connected to each other (disconnected components)"""
        
        if not self.nodes:
            return []
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        def dfs(node_id: str, component: List[Node]):
            if node_id in visited:
                return
            
            visited.add(node_id)
            if node_id in self.nodes:
                component.append(self.nodes[node_id])
                
                # Visit connected nodes
                for connected_node in self.get_connected_nodes(node_id):
                    if connected_node.id not in visited:
                        dfs(connected_node.id, component)
        
        # Find all components
        for node_id in self.nodes:
            if node_id not in visited:
                component = []
                dfs(node_id, component)
                if component:
                    components.append(component)
        
        # Return components with more than 1 node (meaningful threads)
        return [comp for comp in components if len(comp) > 1]
    
    def get_prioritized_questions(self) -> List[Node]:
        """Get investigation questions ordered by priority"""
        questions = self.get_nodes_by_type("InvestigationQuestion")
        
        # Score questions based on connections and progress
        scored_questions = []
        for q in questions:
            score = 0.0
            
            # Higher score for questions with more incoming connections (more important)
            incoming = len(self.get_incoming_edges(q.id))
            score += incoming * 0.3
            
            # Lower score for questions already operationalized
            outgoing = len(self.get_outgoing_edges(q.id)) 
            score -= outgoing * 0.1
            
            # Higher score for questions without data yet
            has_data = any(self.get_outgoing_edges(edge.target_id) 
                          for edge in self.get_outgoing_edges(q.id)
                          if edge.target_id in self.nodes)
            if not has_data:
                score += 0.5
            
            scored_questions.append((q, score))
        
        # Sort by score (highest first)
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        return [q for q, score in scored_questions]
    
    def get_strategic_context_for_llm(self) -> str:
        """Generate comprehensive context for strategic decision making"""
        context_parts = []
        
        # Original goal
        if self.analytic_question:
            context_parts.append(f"ORIGINAL GOAL: {self.analytic_question.text}")
        else:
            context_parts.append("ORIGINAL GOAL: Not defined")
        
        # Investigation progress
        context_parts.append(f"\nINVESTIGATION PROGRESS:")
        context_parts.append(f"- Questions Asked: {len(self.get_nodes_by_type('InvestigationQuestion'))}")
        context_parts.append(f"- Questions Answered: {len(self.get_answered_questions())}")
        context_parts.append(f"- Searches Conducted: {len(self.get_nodes_by_type('SearchQuery'))}")
        context_parts.append(f"- Data Points Collected: {len(self.get_nodes_by_type('DataPoint'))}")
        context_parts.append(f"- Insights Generated: {len(self.get_nodes_by_type('Insight'))}")
        
        # Current information gaps
        gaps = self.get_information_gaps()
        context_parts.append(f"\nCURRENT INFORMATION GAPS:")
        for gap in gaps[:5]:  # Limit for readability
            context_parts.append(f"- {gap}")
        
        # Disconnected threads
        threads = self.get_disconnected_threads()
        context_parts.append(f"\nDISCONNECTED THREADS:")
        for i, thread in enumerate(threads[:3]):  # Limit for readability
            thread_desc = [node.properties.get('text', str(node.id))[:50] for node in thread[:3]]
            context_parts.append(f"- Thread {i+1}: {thread_desc}")
        
        # Failed approaches
        failed_patterns = self.get_failed_patterns()
        context_parts.append(f"\nFAILED APPROACHES (avoid repetition):")
        for pattern in failed_patterns[:5]:  # Limit for readability
            context_parts.append(f"- {pattern}")
        
        # Strategic decision point
        context_parts.append(f"\nSTRATEGIC COHERENCE DECISION POINT:")
        context_parts.append("Given this complete context, what is the most strategically coherent next action?")
        context_parts.append("Consider: thread connectivity, gap coverage, systematic exploration, global optimization.")
        
        return "\n".join(context_parts)
    
    def get_answered_questions(self) -> List[Node]:
        """Get investigation questions that have been answered (have insights)"""
        answered = []
        questions = self.get_nodes_by_type("InvestigationQuestion")
        
        for q in questions:
            # Check if there's a path from this question to insights
            if self._has_path_to_insights(q.id):
                answered.append(q)
        
        return answered
    
    def _has_path_to_insights(self, node_id: str, visited: set = None) -> bool:
        """Check if there's a path from this node to any insights"""
        if visited is None:
            visited = set()
        
        if node_id in visited:
            return False
        
        visited.add(node_id)
        
        # Check direct connections
        for edge in self.get_outgoing_edges(node_id):
            target_node = self.nodes.get(edge.target_id)
            if target_node and target_node.node_type == "Insight":
                return True
            
            # Recursive check
            if self._has_path_to_insights(edge.target_id, visited):
                return True
        
        return False
    
    def get_failed_patterns(self) -> List[str]:
        """Identify search patterns that consistently failed"""
        failed_patterns = []
        search_nodes = self.get_nodes_by_type("SearchQuery")
        
        # Group searches by query pattern
        query_stats = defaultdict(list)
        
        for search in search_nodes:
            # Extract query for pattern matching
            query_key = search.parameters.get("query", "").lower()
            if not query_key:
                query_key = f"{search.endpoint}:{search.parameters}"
            
            effectiveness = search.properties.get("effectiveness_score", 0.0)
            query_stats[query_key].append(effectiveness)
        
        # Identify patterns that failed multiple times
        for query_pattern, effectiveness_scores in query_stats.items():
            if len(effectiveness_scores) >= 3:  # Repeated 3+ times
                avg_effectiveness = sum(effectiveness_scores) / len(effectiveness_scores)
                if avg_effectiveness < 3.0:  # Consistently low effectiveness
                    failed_patterns.append(
                        f"'{query_pattern}': {len(effectiveness_scores)} attempts, "
                        f"avg effectiveness: {avg_effectiveness:.1f}/10"
                    )
        
        return failed_patterns
    
    # Serialization methods
    def to_json(self) -> str:
        """Serialize graph to JSON string"""
        data = {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
            "analytic_question": self.analytic_question.id if self.analytic_question else None,
            "created_at": datetime.now().isoformat()
        }
        return json.dumps(data, indent=2)
    
    def from_json(self, json_str: str) -> None:
        """Restore graph from JSON string"""
        data = json.loads(json_str)
        
        # Clear existing data
        self.nodes.clear()
        self.edges.clear()
        self._edges_by_source.clear()
        self._edges_by_target.clear()
        self._nodes_by_type.clear()
        
        # Restore nodes
        for node_id, node_data in data["nodes"].items():
            node = Node.from_dict(node_data)
            self.nodes[node_id] = node
            self._nodes_by_type[node.node_type].append(node)
        
        # Restore edges
        for edge_data in data["edges"]:
            edge = Edge.from_dict(edge_data)
            self.edges.append(edge)
            self._edges_by_source[edge.source_id].append(edge)
            self._edges_by_target[edge.target_id].append(edge)
        
        # Restore analytic question reference
        analytic_id = data.get("analytic_question")
        if analytic_id and analytic_id in self.nodes:
            self.analytic_question = self.nodes[analytic_id]


@dataclass
class InvestigationContext:
    """Enhanced investigation context with graph integration"""
    goal: str
    graph: InvestigationGraph
    current_understanding: str = "Starting investigation"
    confidence_level: float = 0.0
    
    def __post_init__(self):
        if self.graph is None:
            self.graph = InvestigationGraph()


# Wrapper classes for test compatibility
class DataPointNodeWrapper:
    """Wrapper for DataPointNode to provide test compatibility"""
    def __init__(self, node: DataPointNode, graph: InvestigationGraph):
        self.node = node
        self.graph = graph
        self.id = node.id
        self.type = NodeType.DATAPOINT
        self.attributes = node.properties
        
        # Add source and timestamp to attributes if present
        if 'source_info' in node.properties:
            source_info = node.properties['source_info']
            if 'source' in source_info:
                self.attributes['source'] = source_info['source']
            if 'timestamp' in source_info:
                self.attributes['timestamp'] = source_info['timestamp']
    
    @property
    def properties(self):
        """Provide properties interface for API consistency"""
        return self.attributes


class InsightNodeWrapper:
    """Wrapper for InsightNode to provide test compatibility"""
    def __init__(self, node: InsightNode, graph: InvestigationGraph):
        self.node = node
        self.graph = graph
        self.id = node.id
        self.type = NodeType.INSIGHT
        self.attributes = node.properties
    
    @property
    def properties(self):
        """Provide properties interface for API consistency"""
        return self.attributes