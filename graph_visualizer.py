"""Systematic graph visualization module for investigation knowledge graphs"""
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import networkx as nx
from pathlib import Path


@dataclass
class GraphNode:
    """Represents a node in the investigation graph"""
    id: str
    node_type: str  # 'query', 'search', 'datapoint', 'insight'
    label: str
    content: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_vis_format(self) -> Dict[str, Any]:
        """Convert to vis.js node format"""
        colors = {
            'query': {'background': '#9C27B0', 'border': '#7B1FA2'},  # Purple for initial query
            'search': {'background': '#4CAF50', 'border': '#388E3C'},  # Green for searches
            'datapoint': {'background': '#2196F3', 'border': '#1976D2'},  # Blue for findings
            'insight': {'background': '#FF9800', 'border': '#F57C00'}  # Orange for insights
        }
        
        shapes = {
            'query': 'star',
            'search': 'box',
            'datapoint': 'ellipse',
            'insight': 'diamond'
        }
        
        return {
            'id': self.id,
            'label': self.label,
            'title': self.content[:500] if len(self.content) > 100 else self.content,
            'color': colors.get(self.node_type, colors['datapoint']),
            'shape': shapes.get(self.node_type, 'ellipse'),
            'size': 30 if self.node_type == 'query' else 20,
            'font': {'size': 14 if self.node_type == 'query' else 12}
        }


@dataclass
class GraphEdge:
    """Represents an edge in the investigation graph"""
    source: str
    target: str
    edge_type: str  # 'INITIATED', 'DISCOVERED', 'SUPPORTS', 'REFINED'
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_vis_format(self) -> Dict[str, Any]:
        """Convert to vis.js edge format"""
        edge_styles = {
            'INITIATED': {'color': '#9C27B0', 'width': 2, 'dashes': False},
            'DISCOVERED': {'color': '#4CAF50', 'width': 1.5, 'dashes': False},
            'SUPPORTS': {'color': '#FF9800', 'width': 1, 'dashes': True},
            'REFINED': {'color': '#2196F3', 'width': 1, 'dashes': [5, 5]}
        }
        
        style = edge_styles.get(self.edge_type, {'color': '#999', 'width': 1, 'dashes': False})
        
        return {
            'from': self.source,
            'to': self.target,
            'label': self.edge_type if self.edge_type != 'INITIATED' else '',
            'arrows': 'to',
            'color': {'color': style['color']},
            'width': style['width'],
            'dashes': style['dashes'],
            'smooth': {'enabled': True, 'type': 'dynamic'}
        }


class InvestigationGraphVisualizer:
    """Systematic graph visualization for investigation results"""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.nx_graph = nx.DiGraph()
        
    def add_query_node(self, query: str, timestamp: Optional[str] = None) -> str:
        """Add the initial investigation query as the root node"""
        node_id = self._generate_id(f"query_{query}")
        
        node = GraphNode(
            id=node_id,
            node_type='query',
            label=f"Query: {query[:30]}..." if len(query) > 30 else f"Query: {query}",
            content=query,
            timestamp=timestamp or datetime.now().isoformat(),
            metadata={'original_query': query}
        )
        
        self.nodes[node_id] = node
        self.nx_graph.add_node(node_id, **node.metadata)
        return node_id
    
    def add_search_node(self, search_params: Dict[str, Any], 
                       endpoint: str, search_num: int,
                       parent_id: Optional[str] = None) -> str:
        """Add a search query node"""
        # Create search identifier
        search_key = search_params.get('query', search_params.get('screenname', str(search_params)))
        node_id = self._generate_id(f"search_{search_num}_{search_key}")
        
        # Create label
        if 'query' in search_params:
            label = f"Search #{search_num}: {search_params['query'][:25]}..."
        elif 'screenname' in search_params:
            label = f"Timeline #{search_num}: @{search_params['screenname']}"
        else:
            label = f"Search #{search_num}: {endpoint}"
        
        node = GraphNode(
            id=node_id,
            node_type='search',
            label=label,
            content=f"{endpoint} with params: {json.dumps(search_params)}",
            timestamp=datetime.now().isoformat(),
            metadata={'endpoint': endpoint, 'params': search_params, 'search_num': search_num}
        )
        
        self.nodes[node_id] = node
        self.nx_graph.add_node(node_id, **node.metadata)
        
        # Connect to parent (usually the query node)
        if parent_id and parent_id in self.nodes:
            self.add_edge(parent_id, node_id, 'INITIATED')
        
        return node_id
    
    def add_datapoint_node(self, content: str, source: str,
                          search_id: Optional[str] = None,
                          relevance: float = 0.5) -> str:
        """Add a finding/datapoint node"""
        node_id = self._generate_id(f"dp_{content[:50]}")
        
        # Create concise label
        label = f"Finding: {content[:40]}..." if len(content) > 40 else f"Finding: {content}"
        
        node = GraphNode(
            id=node_id,
            node_type='datapoint',
            label=label,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata={'source': source, 'relevance': relevance}
        )
        
        self.nodes[node_id] = node
        self.nx_graph.add_node(node_id, **node.metadata)
        
        # Connect to search that discovered it
        if search_id and search_id in self.nodes:
            self.add_edge(search_id, node_id, 'DISCOVERED')
        
        return node_id
    
    def add_insight_node(self, synthesis: str, confidence: float,
                        supporting_nodes: List[str] = None) -> str:
        """Add an insight/pattern node"""
        node_id = self._generate_id(f"insight_{synthesis[:50]}")
        
        # Create label
        label = f"Insight: {synthesis[:35]}..." if len(synthesis) > 35 else f"Insight: {synthesis}"
        
        node = GraphNode(
            id=node_id,
            node_type='insight',
            label=label,
            content=synthesis,
            timestamp=datetime.now().isoformat(),
            metadata={'confidence': confidence}
        )
        
        self.nodes[node_id] = node
        self.nx_graph.add_node(node_id, **node.metadata)
        
        # Connect supporting datapoints
        if supporting_nodes:
            for support_id in supporting_nodes:
                if support_id in self.nodes:
                    self.add_edge(support_id, node_id, 'SUPPORTS')
        
        return node_id
    
    def add_edge(self, source: str, target: str, edge_type: str, weight: float = 1.0):
        """Add an edge between nodes"""
        if source in self.nodes and target in self.nodes:
            edge = GraphEdge(source, target, edge_type, weight)
            self.edges.append(edge)
            self.nx_graph.add_edge(source, target, type=edge_type, weight=weight)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        node_counts = {
            'query': sum(1 for n in self.nodes.values() if n.node_type == 'query'),
            'search': sum(1 for n in self.nodes.values() if n.node_type == 'search'),
            'datapoint': sum(1 for n in self.nodes.values() if n.node_type == 'datapoint'),
            'insight': sum(1 for n in self.nodes.values() if n.node_type == 'insight')
        }
        
        edge_counts = {}
        for edge in self.edges:
            edge_counts[edge.edge_type] = edge_counts.get(edge.edge_type, 0) + 1
        
        # Calculate graph metrics
        metrics = {}
        if self.nx_graph.number_of_nodes() > 0:
            metrics['density'] = nx.density(self.nx_graph)
            metrics['avg_degree'] = sum(dict(self.nx_graph.degree()).values()) / self.nx_graph.number_of_nodes()
            
            # Find dead-end searches (searches with no outgoing edges)
            dead_ends = []
            for node_id, node in self.nodes.items():
                if node.node_type == 'search':
                    if self.nx_graph.out_degree(node_id) == 0:
                        dead_ends.append(node.label)
            metrics['dead_end_searches'] = dead_ends
        
        return {
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'node_counts': node_counts,
            'edge_counts': edge_counts,
            'metrics': metrics
        }
    
    def export_vis_data(self) -> Dict[str, Any]:
        """Export graph data in vis.js format"""
        nodes_data = [node.to_vis_format() for node in self.nodes.values()]
        edges_data = [edge.to_vis_format() for edge in self.edges]
        
        return {
            'nodes': nodes_data,
            'edges': edges_data,
            'statistics': self.get_statistics()
        }
    
    def export_hierarchy_data(self) -> Dict[str, Any]:
        """Export graph data in D3.js hierarchy format"""
        def build_hierarchy_tree():
            # Find root nodes (typically query nodes)
            root_nodes = [node for node in self.nodes.values() if node.node_type == 'query']
            
            if not root_nodes:
                # If no query node, use any node without incoming edges as root
                incoming_edges = {edge.target for edge in self.edges}
                all_nodes = set(self.nodes.keys())
                root_candidates = all_nodes - incoming_edges
                root_nodes = [self.nodes[node_id] for node_id in root_candidates if node_id in self.nodes]
                
            if not root_nodes:
                # Fallback: use first node as root
                root_nodes = [list(self.nodes.values())[0]] if self.nodes else []
            
            def node_to_d3_format(node: GraphNode, visited: set = None) -> Dict[str, Any]:
                if visited is None:
                    visited = set()
                
                if node.id in visited:
                    return {"name": node.label, "type": node.node_type, "id": node.id, "circular": True}
                
                visited.add(node.id)
                
                # Find children (nodes connected by outgoing edges)
                children = []
                for edge in self.edges:
                    if edge.source == node.id and edge.target in self.nodes:
                        child_node = self.nodes[edge.target]
                        children.append(node_to_d3_format(child_node, visited.copy()))
                
                return {
                    "name": node.label,
                    "type": node.node_type,
                    "id": node.id,
                    "content": node.content,
                    "timestamp": node.timestamp,
                    "metadata": node.metadata,
                    "children": children if children else None
                }
            
            # Build hierarchy tree starting from root nodes
            if len(root_nodes) == 1:
                return node_to_d3_format(root_nodes[0])
            else:
                # Multiple roots - create virtual root
                return {
                    "name": "Investigation",
                    "type": "root",
                    "id": "virtual_root",
                    "children": [node_to_d3_format(root) for root in root_nodes]
                }
        
        hierarchy_tree = build_hierarchy_tree()
        
        return {
            'hierarchy': hierarchy_tree,
            'statistics': self.get_statistics()
        }
    
    def generate_html(self, title: str = "Investigation Knowledge Graph",
                     include_stats: bool = True) -> str:
        """Generate standalone HTML visualization using D3.js hierarchy"""
        data = self.export_hierarchy_data()
        stats = data['statistics']
        
        stats_html = ""
        if include_stats:
            stats_html = f"""
    <div class="stats-panel">
        <h3>Investigation Statistics</h3>
        <div class="stat-grid">
            <div class="stat-item">
                <span class="stat-label">Total Nodes:</span>
                <span class="stat-value">{stats['total_nodes']}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Searches:</span>
                <span class="stat-value">{stats['node_counts']['search']}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Findings:</span>
                <span class="stat-value">{stats['node_counts']['datapoint']}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Insights:</span>
                <span class="stat-value">{stats['node_counts']['insight']}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Connections:</span>
                <span class="stat-value">{stats['total_edges']}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">Graph Density:</span>
                <span class="stat-value">{stats['metrics'].get('density', 0):.3f}</span>
            </div>
        </div>
        {self._format_dead_ends(stats['metrics'].get('dead_end_searches', []))}
    </div>"""
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .graph-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 20px;
        }}
        #hierarchy-chart {{
            width: 100%;
            height: 800px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
        }}
        
        .node {{
            cursor: pointer;
        }}
        
        .node circle {{
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .node text {{
            font: 12px sans-serif;
            pointer-events: none;
        }}
        
        .link {{
            fill: none;
            stroke: #999;
            stroke-width: 2px;
            stroke-opacity: 0.6;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 8px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            max-width: 300px;
            pointer-events: none;
            z-index: 1000;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: #f5f5f5;
            border-radius: 20px;
        }}
        .color-box {{
            width: 24px;
            height: 24px;
            border-radius: 4px;
            border: 2px solid rgba(0,0,0,0.2);
        }}
        .stats-panel {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .stats-panel h3 {{
            margin-top: 0;
            color: #333;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-item {{
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-label {{
            display: block;
            font-size: 12px;
            color: #666;
            margin-bottom: 4px;
        }}
        .stat-value {{
            display: block;
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
        .dead-ends {{
            margin-top: 15px;
            padding: 10px;
            background: #fff3cd;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
        }}
        .dead-ends h4 {{
            margin: 0 0 8px 0;
            color: #856404;
        }}
        .dead-end-list {{
            margin: 0;
            padding-left: 20px;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div class="graph-container">
            <div class="legend">
                <div class="legend-item">
                    <span class="color-box" style="background: #9C27B0;"></span>
                    <span>Initial Query</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: #4CAF50;"></span>
                    <span>Search Queries</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: #2196F3;"></span>
                    <span>Findings (DataPoints)</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: #FF9800;"></span>
                    <span>Insights (Patterns)</span>
                </div>
            </div>
            
            <svg id="hierarchy-chart"></svg>
        </div>
        
        {stats_html}
    </div>

    <script>
        // Hierarchy data from Python
        const hierarchyData = {json.dumps(data['hierarchy'], indent=2)};
        
        // Set up SVG dimensions
        const margin = {{top: 40, right: 120, bottom: 40, left: 120}};
        const width = 1200 - margin.left - margin.right;
        const height = 800 - margin.top - margin.bottom;
        
        // Create SVG
        const svg = d3.select("#hierarchy-chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);
            
        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);
        
        // Create hierarchy tree layout
        const treemap = d3.tree().size([width, height]);
        
        // Hierarchy root
        const root = d3.hierarchy(hierarchyData);
        
        // Assign positions
        treemap(root);
        
        // Node colors by type
        const colors = {{
            'query': '#9C27B0',
            'search': '#4CAF50', 
            'datapoint': '#2196F3',
            'insight': '#FF9800',
            'root': '#E91E63'
        }};
        
        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Add links
        const links = g.selectAll(".link")
            .data(root.descendants().slice(1))
            .enter().append("path")
            .attr("class", "link")
            .attr("d", function(d) {{
                return `M${{d.x}},${{d.y}}C${{d.x}},${{(d.y + d.parent.y) / 2}} ${{d.parent.x}},${{(d.y + d.parent.y) / 2}} ${{d.parent.x}},${{d.parent.y}}`;
            }});
        
        // Add nodes
        const nodes = g.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) {{ 
                return `translate(${{d.x}},${{d.y}})`; 
            }})
            .on("mouseover", function(event, d) {{
                tooltip.transition().duration(200).style("opacity", .9);
                const content = d.data.content || d.data.name || "No content";
                tooltip.html(`<strong>${{d.data.name}}</strong><br/>${{content.substring(0, 200)}}${{content.length > 200 ? '...' : ''}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition().duration(500).style("opacity", 0);
            }})
            .on("click", function(event, d) {{
                console.log("Node clicked:", d.data);
            }});
            
        // Add circles
        nodes.append("circle")
            .attr("r", function(d) {{
                return d.data.type === 'query' || d.data.type === 'root' ? 12 : 8;
            }})
            .style("fill", function(d) {{
                return colors[d.data.type] || colors['datapoint'];
            }});
            
        // Add labels
        nodes.append("text")
            .attr("dy", function(d) {{
                return d.children || d._children ? -18 : 18;
            }})
            .attr("text-anchor", "middle")
            .style("font-size", function(d) {{
                return d.data.type === 'query' || d.data.type === 'root' ? "14px" : "11px";
            }})
            .style("font-weight", function(d) {{
                return d.data.type === 'query' || d.data.type === 'root' ? "bold" : "normal";
            }})
            .text(function(d) {{ 
                const name = d.data.name || d.data.id || "Unknown";
                return name.length > 25 ? name.substring(0, 25) + "..." : name;
            }});
            
        // Zoom and pan
        const zoom = d3.zoom()
            .scaleExtent([0.1, 3])
            .on("zoom", function(event) {{
                g.attr("transform", event.transform);
            }});
            
        svg.call(zoom);
        
        // Initial fit
        const bounds = g.node().getBBox();
        const fullWidth = width;
        const fullHeight = height;
        const widthScale = fullWidth / bounds.width;
        const heightScale = fullHeight / bounds.height;
        const scale = 0.8 * Math.min(widthScale, heightScale);
        const translate = [fullWidth / 2 - scale * bounds.x - scale * bounds.width / 2, fullHeight / 2 - scale * bounds.y - scale * bounds.height / 2];
        
        svg.call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        
        console.log("D3.js Hierarchy visualization loaded with", root.descendants().length, "nodes");
    </script>
</body>
</html>"""
        
        return html
    
    def _generate_id(self, seed: str) -> str:
        """Generate consistent ID from seed string"""
        return hashlib.md5(seed.encode()).hexdigest()[:12]
    
    def _format_dead_ends(self, dead_ends: List[str]) -> str:
        """Format dead-end searches for display"""
        if not dead_ends:
            return ""
        
        items = "\n".join(f"<li>{search}</li>" for search in dead_ends)
        return f"""
        <div class="dead-ends">
            <h4>Dead-end Searches (no significant findings):</h4>
            <ul class="dead-end-list">
                {items}
            </ul>
        </div>"""
    
    def save_visualization(self, filepath: str = "investigation_graph.html"):
        """Save the visualization to an HTML file"""
        html = self.generate_html()
        Path(filepath).write_text(html, encoding='utf-8')
        return filepath
    
    def get_streamlit_component(self) -> Tuple[Dict[str, Any], str]:
        """Get data and HTML for Streamlit integration"""
        data = self.export_vis_data()
        
        # Simplified HTML for embedding in Streamlit
        html = f"""
        <div id="investigation-network" style="height: 500px;"></div>
        <script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
        <script>
            const graphData = {json.dumps(data)};
            const container = document.getElementById('investigation-network');
            const data = {{
                nodes: new vis.DataSet(graphData.nodes),
                edges: new vis.DataSet(graphData.edges)
            }};
            const options = {{
                layout: {{
                    hierarchical: {{
                        enabled: true,
                        direction: 'UD'
                    }}
                }},
                physics: {{enabled: true}}
            }};
            new vis.Network(container, data, options);
        </script>
        """
        
        return data, html


# Utility function to create graph from investigation session
def create_graph_from_investigation(investigation_session, llm_graph=None) -> InvestigationGraphVisualizer:
    """Create a visualization from an InvestigationSession object"""
    visualizer = InvestigationGraphVisualizer()
    
    # Add initial query node
    query_id = visualizer.add_query_node(
        investigation_session.original_query,
        investigation_session.start_time.isoformat() if hasattr(investigation_session, 'start_time') else None
    )
    
    # Add search nodes and findings
    search_id_map = {}
    
    for round_data in investigation_session.rounds:
        for search in round_data.searches:
            # Add search node
            search_id = visualizer.add_search_node(
                search.params,
                search.endpoint,
                search.search_id,
                parent_id=query_id
            )
            search_id_map[search.search_id] = search_id
            
            # Add datapoints if available from LLM graph
            if llm_graph and hasattr(llm_graph, 'nodes'):
                # Find DataPoint nodes connected to this search
                for node_id, node in llm_graph.nodes.items():
                    if 'DataPoint' in str(type(node)):
                        # Check if this datapoint is connected to this search
                        for edge in llm_graph.edges:
                            if edge.source_id == search_id and edge.target_id == node_id:
                                dp_id = visualizer.add_datapoint_node(
                                    node.properties.get('content', ''),
                                    node.properties.get('source', ''),
                                    search_id,
                                    node.properties.get('relevance', 0.5)
                                )
    
    # Add insights if available
    if llm_graph and hasattr(llm_graph, 'nodes'):
        for node_id, node in llm_graph.nodes.items():
            if 'Insight' in str(type(node)):
                # Find supporting datapoints
                supporting = []
                for edge in llm_graph.edges:
                    if edge.target_id == node_id and edge.edge_type == 'SUPPORTS':
                        supporting.append(edge.source_id)
                
                visualizer.add_insight_node(
                    node.properties.get('content', 'Pattern detected'),
                    node.properties.get('confidence', 0.5),
                    supporting
                )
    
    return visualizer