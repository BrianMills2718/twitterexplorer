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
    node_type: str  # 'query', 'search', 'datapoint', 'insight', 'emergentquestion'
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
            'insight': {'background': '#FF9800', 'border': '#F57C00'},  # Orange for insights
            'emergentquestion': {'background': '#E91E63', 'border': '#C2185B'}  # Pink for emergent questions
        }

        shapes = {
            'query': 'star',
            'search': 'box',
            'datapoint': 'ellipse',
            'insight': 'diamond',
            'emergentquestion': 'triangle'
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

    def add_emergentquestion_node(self, question_text: str, priority: float = 0.5,
                                 spawning_insight: str = None) -> str:
        """Add an emergent question node"""
        node_id = self._generate_id(f"emergentquestion_{question_text[:50]}")

        # Create label
        label = f"Question: {question_text[:35]}..." if len(question_text) > 35 else f"Question: {question_text}"

        node = GraphNode(
            id=node_id,
            node_type='emergentquestion',
            label=label,
            content=question_text,
            timestamp=datetime.now().isoformat(),
            metadata={'priority': priority}
        )

        self.nodes[node_id] = node
        self.nx_graph.add_node(node_id, **node.metadata)

        # Connect spawning insight if provided
        if spawning_insight and spawning_insight in self.nodes:
            self.add_edge(spawning_insight, node_id, 'SPAWNS')

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
            'insight': sum(1 for n in self.nodes.values() if n.node_type == 'insight'),
            'emergentquestion': sum(1 for n in self.nodes.values() if n.node_type == 'emergentquestion')
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
        """Generate consistent ID from seed string with collision prevention"""
        base_id = hashlib.md5(seed.encode()).hexdigest()[:12]

        # Ensure uniqueness by adding counter if collision exists
        counter = 0
        unique_id = base_id
        while unique_id in self.nodes:
            counter += 1
            unique_id = f"{base_id}_{counter}"

        return unique_id

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

    def save_wave_visualization(self, filepath: str, wave_data: Dict[str, Any],
                              investigation_title: str = "Wave Investigation") -> str:
        """Save wave-specific visualization showing true dependencies"""
        html = self._generate_wave_html(wave_data, investigation_title)
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

    def _generate_wave_html(self, wave_data: Dict[str, Any], title: str) -> str:
        """Generate HTML for wave visualization showing dependencies and boundaries"""
        nodes = wave_data.get('nodes', [])
        edges = wave_data.get('edges', [])
        wave_count = wave_data.get('wave_count', 0)

        # Wave-specific colors
        wave_colors = {
            'Wave': '#9C27B0',
            'DrivingQuestion': '#E91E63',
            'Search': '#4CAF50',
            'Insight': '#FF9800',
            'EmergentQuestion': '#F44336'
        }

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
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .wave-info {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            text-align: center;
        }}
        .graph-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}
        #wave-chart {{
            width: 100%;
            height: 900px;
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
            font: 11px sans-serif;
            pointer-events: none;
        }}

        .link {{
            fill: none;
            stroke-width: 2px;
            stroke-opacity: 0.6;
        }}

        .dependency-link {{
            stroke: #FF4444;
            stroke-width: 3px;
            stroke-dasharray: 5,5;
        }}

        .wave-boundary {{
            stroke: #9C27B0;
            stroke-width: 2px;
            stroke-dasharray: 8,4;
        }}

        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 6px;
            font-size: 12px;
            max-width: 400px;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: #f8f9fa;
            border-radius: 20px;
            border: 2px solid #e9ecef;
        }}
        .color-box {{
            width: 20px;
            height: 20px;
            border-radius: 3px;
            border: 1px solid rgba(0,0,0,0.2);
        }}
        .wave-boundary-legend {{
            width: 30px;
            height: 3px;
            background: #9C27B0;
            border-radius: 2px;
        }}
        .dependency-legend {{
            width: 30px;
            height: 3px;
            background: #FF4444;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="wave-info">
            <h3>Investigation Flow: {wave_data.get('investigation_goal', 'Unknown Goal')}</h3>
            <p><strong>{wave_count} Waves</strong> showing true dependencies where emergent questions drive next wave searches</p>
        </div>

        <div class="graph-container">
            <div class="legend">
                <div class="legend-item">
                    <span class="color-box" style="background: {wave_colors['Wave']};"></span>
                    <span>Wave</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: {wave_colors['DrivingQuestion']};"></span>
                    <span>Driving Questions</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: {wave_colors['Search']};"></span>
                    <span>Searches</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: {wave_colors['Insight']};"></span>
                    <span>Insights</span>
                </div>
                <div class="legend-item">
                    <span class="color-box" style="background: {wave_colors['EmergentQuestion']};"></span>
                    <span>Emergent Questions</span>
                </div>
                <div class="legend-item">
                    <span class="wave-boundary-legend"></span>
                    <span>Wave Boundaries</span>
                </div>
                <div class="legend-item">
                    <span class="dependency-legend"></span>
                    <span>True Dependencies</span>
                </div>
            </div>

            <svg id="wave-chart"></svg>
        </div>
    </div>

    <script>
        // Wave data from Python
        const waveNodes = {json.dumps(nodes, indent=2)};
        const waveEdges = {json.dumps(edges, indent=2)};

        // Set up SVG dimensions
        const margin = {{top: 60, right: 140, bottom: 60, left: 140}};
        const width = 1400 - margin.left - margin.right;
        const height = 900 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select("#wave-chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Colors by node type
        const colors = {json.dumps(wave_colors)};

        // Create force simulation for better layout
        const simulation = d3.forceSimulation(waveNodes)
            .force("link", d3.forceLink(waveEdges).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("x", d3.forceX(width / 2).strength(0.1))
            .force("y", d3.forceY(height / 2).strength(0.1))
            .force("center", d3.forceCenter(width / 2, height / 2));

        // Group nodes by wave for positioning
        const waveGroups = d3.group(waveNodes, d => d.wave);
        const waveCount = waveGroups.size;

        // Position waves horizontally
        waveNodes.forEach(d => {{
            if (d.wave) {{
                d.fx = (d.wave - 1) * (width / Math.max(waveCount - 1, 1));
                d.fy = height * 0.3 + Math.random() * height * 0.4; // Some vertical spread
            }}
        }});

        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // Add links first (behind nodes)
        const links = g.selectAll(".link")
            .data(waveEdges)
            .enter().append("line")
            .attr("class", "link")
            .style("stroke", function(d) {{
                if (d.dependency) return "#FF4444";
                if (d.wave_boundary) return "#9C27B0";
                return "#999";
            }})
            .style("stroke-dasharray", function(d) {{
                if (d.dependency) return "5,5";
                if (d.wave_boundary) return "8,4";
                return "none";
            }})
            .attr("class", function(d) {{
                if (d.dependency) return "link dependency-link";
                if (d.wave_boundary) return "link wave-boundary";
                return "link";
            }});

        // Add nodes
        const nodes = g.selectAll(".node")
            .data(waveNodes)
            .enter().append("g")
            .attr("class", "node")
            .on("mouseover", function(event, d) {{
                tooltip.transition().duration(200).style("opacity", .9);
                let content = `<strong>${{d.name}}</strong><br/>`;
                content += `<strong>Type:</strong> ${{d.type}}<br/>`;
                content += `<strong>Wave:</strong> ${{d.wave || 'N/A'}}<br/>`;

                if (d.full_text) {{
                    content += `<br/>${{d.full_text.substring(0, 200)}}${{d.full_text.length > 200 ? '...' : ''}}`;
                }}

                if (d.details) {{
                    content += '<br/><strong>Details:</strong><br/>';
                    Object.entries(d.details).forEach(([key, value]) => {{
                        content += `${{key}}: ${{value}}<br/>`;
                    }});
                }}

                tooltip.html(content)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition().duration(500).style("opacity", 0);
            }})
            .on("click", function(event, d) {{
                console.log("Wave node clicked:", d);
            }})
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Add circles for nodes
        nodes.append("circle")
            .attr("r", function(d) {{
                if (d.type === 'Wave') return 15;
                if (d.type === 'DrivingQuestion') return 10;
                return 8;
            }})
            .style("fill", function(d) {{
                return colors[d.type] || colors['Search'];
            }})
            .style("stroke", "#fff")
            .style("stroke-width", 2);

        // Add labels
        nodes.append("text")
            .attr("dy", function(d) {{
                return d.type === 'Wave' ? -20 : 20;
            }})
            .attr("text-anchor", "middle")
            .style("font-size", function(d) {{
                if (d.type === 'Wave') return "12px";
                return "10px";
            }})
            .style("font-weight", function(d) {{
                return d.type === 'Wave' ? "bold" : "normal";
            }})
            .text(function(d) {{
                const name = d.name || d.id || "Unknown";
                return name.length > 20 ? name.substring(0, 20) + "..." : name;
            }});

        // Update positions on simulation tick
        simulation.on("tick", function() {{
            links
                .attr("x1", function(d) {{ return d.source.x; }})
                .attr("y1", function(d) {{ return d.source.y; }})
                .attr("x2", function(d) {{ return d.target.x; }})
                .attr("y2", function(d) {{ return d.target.y; }});

            nodes
                .attr("transform", function(d) {{
                    return `translate(${{d.x}},${{d.y}})`;
                }});
        }});

        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // Zoom functionality
        const zoom = d3.zoom()
            .scaleExtent([0.2, 4])
            .on("zoom", function(event) {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        console.log("Wave visualization loaded with", waveNodes.length, "nodes and", waveEdges.length, "edges");
        console.log("True dependencies highlighted in red dashed lines");
        console.log("Wave boundaries shown in purple dashed lines");
    </script>
</body>
</html>"""

        return html

    def save_wave_hierarchy_visualization(self, filepath: str, wave_data: Dict[str, Any],
                                        investigation_title: str = "Wave Investigation") -> str:
        """Save wave-specific network visualization using D3.js force layout"""
        html = self._generate_wave_network_html(wave_data, investigation_title)
        Path(filepath).write_text(html, encoding='utf-8')
        return filepath

    def _generate_wave_network_html(self, wave_data: Dict[str, Any], title: str) -> str:
        """Generate hierarchical tree layout HTML for wave visualization showing investigation flow"""

        # Build hierarchical structure from the wave data
        hierarchy_data = self._build_investigation_hierarchy(wave_data)

        # Extract convergence edges to show many-to-one relationships
        convergence_edges = self._extract_convergence_edges(wave_data)
        print(f"DEBUG: Extracted {len(convergence_edges)} convergence edges")

        # Node colors for different types in the investigation flow
        node_colors = {
            'AnalyticGoal': '#9C27B0',      # Purple - Root of investigation
            'InvestigationQuestion': '#E91E63',  # Pink - Questions driving investigation
            'Search': '#4CAF50',             # Green - Searches executed
            'DataPoint': '#2196F3',          # Blue - Data collected
            'Insight': '#FF9800',            # Orange - Insights synthesized
            'EmergentQuestion': '#F44336'    # Red - New questions emerged
        }

        # Node sizes for visual hierarchy
        node_sizes = {
            'AnalyticGoal': 18,
            'InvestigationQuestion': 14,
            'Search': 12,
            'DataPoint': 10,
            'Insight': 15,
            'EmergentQuestion': 13
        }

        try:
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
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .investigation-info {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            text-align: center;
        }}
        .graph-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}
        #hierarchy-chart {{
            width: 100%;
            height: 1000px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            background: #fafafa;
        }}

        .node {{
            cursor: pointer;
        }}

        .node circle {{
            stroke: #fff;
            stroke-width: 3px;
        }}

        .node text {{
            font: 11px sans-serif;
            pointer-events: none;
            text-anchor: middle;
            font-weight: 500;
        }}

        .link {{
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
            stroke-opacity: 0.8;
        }}

        .convergence-edge {{
            fill: none;
            stroke-width: 3px;
            stroke-dasharray: 8,4;
            opacity: 0.8;
            pointer-events: none;
        }}

        .tooltip {{
            position: absolute;
            padding: 12px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 6px;
            font-size: 12px;
            max-width: 400px;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            line-height: 1.4;
        }}

        .legend {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: #f8f9fa;
            border-radius: 20px;
            border: 2px solid #e9ecef;
            font-weight: 500;
            font-size: 12px;
        }}

        .color-circle {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            border: 2px solid rgba(0,0,0,0.2);
        }}

        .controls {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 15px 0;
        }}

        .control-btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 20px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.3s ease;
        }}

        .control-btn:hover {{
            background: #5a67d8;
            transform: translateY(-1px);
        }}

        .stats-info {{
            text-align: center;
            color: #666;
            font-size: 14px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="investigation-info">
            <h3>Hierarchical Investigation Flow: {wave_data.get('investigation_goal', 'Investigation')}</h3>
            <p class="stats-info">
                <strong>{len(wave_data.get('nodes', []))} nodes</strong> across <strong>{wave_data.get('wave_count', 0)} computational waves</strong> in tree structure
            </p>
        </div>

        <div class="graph-container">
            <div class="legend">
                <div class="legend-item">
                    <span class="color-circle" style="background: {node_colors['AnalyticGoal']};"></span>
                    <span>Analytic Goal</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: {node_colors['InvestigationQuestion']};"></span>
                    <span>Investigation Questions</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: {node_colors['Search']};"></span>
                    <span>Searches</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: {node_colors['DataPoint']};"></span>
                    <span>Data Points</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: {node_colors['Insight']};"></span>
                    <span>Insights</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: {node_colors['EmergentQuestion']};"></span>
                    <span>Emergent Questions</span>
                </div>
            </div>

            <div class="controls">
                <button class="control-btn" onclick="expandAll()">Expand All</button>
                <button class="control-btn" onclick="collapseAll()">Collapse All</button>
                <button class="control-btn" onclick="centerView()">Center View</button>
            </div>

            <svg id="hierarchy-chart"></svg>
        </div>
    </div>

    <script>
        // Investigation hierarchy data from Python
        const hierarchyData = {json.dumps(hierarchy_data, indent=2)};

        // Set up SVG dimensions
        const margin = {{top: 40, right: 120, bottom: 40, left: 120}};
        const width = 1600 - margin.left - margin.right;
        const height = 1000 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select("#hierarchy-chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Colors and sizes
        const colors = {json.dumps(node_colors)};
        const sizes = {json.dumps(node_sizes)};

        // Create tree layout
        const treemap = d3.tree()
            .size([height, width])
            .separation((a, b) => {{
                return a.parent == b.parent ? 1.2 : 1.5;
            }});

        // Create hierarchy
        const root = d3.hierarchy(hierarchyData);

        // Apply tree layout
        treemap(root);

        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // Add links (connections between nodes)
        const links = g.selectAll(".link")
            .data(root.descendants().slice(1))
            .enter().append("path")
            .attr("class", "link")
            .attr("d", function(d) {{
                return `M${{d.y}},${{d.x}}C${{(d.y + d.parent.y) / 2}},${{d.x}} ${{(d.y + d.parent.y) / 2}},${{d.parent.x}} ${{d.parent.y}},${{d.parent.x}}`;
            }});

        // Add nodes
        const nodes = g.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", function(d) {{
                return `translate(${{d.y}},${{d.x}})`;
            }})
            .on("mouseover", function(event, d) {{
                tooltip.transition().duration(200).style("opacity", .9);

                let content = `<strong>${{d.data.name}}</strong><br/>`;
                content += `<strong>Type:</strong> ${{d.data.type}}<br/>`;

                if (d.data.wave && d.data.wave > 0) {{
                    content += `<strong>Wave:</strong> ${{d.data.wave}}<br/>`;
                }}

                // Show convergence information for Insights and EmergentQuestions
                if (d.data.supported_by && d.data.supported_by.length > 0) {{
                    const supporters = d.data.supported_by;
                    if (d.data.type === 'Insight') {{
                        content += `<br/><strong>Synthesized from ${{supporters.length}} DataPoints:</strong><br/>`;
                    }} else if (d.data.type === 'EmergentQuestion') {{
                        content += `<br/><strong>Emerged from ${{supporters.length}} Insights:</strong><br/>`;
                    }}
                    supporters.forEach(sup => {{
                        content += `• ${{sup.name}}<br/>`;
                    }});
                }}

                if (d.data.full_text) {{
                    content += `<br/>${{d.data.full_text.substring(0, 200)}}${{d.data.full_text.length > 200 ? '...' : ''}}`;
                }}

                if (d.data.details) {{
                    content += '<br/><br/><strong>Details:</strong><br/>';
                    Object.entries(d.data.details).forEach(([key, value]) => {{
                        content += `${{key}}: ${{value}}<br/>`;
                    }});
                }}

                tooltip.html(content)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition().duration(300).style("opacity", 0);
            }})
            .on("click", function(event, d) {{
                console.log("Hierarchy node clicked:", d.data);

                // Toggle children visibility (collapse/expand)
                if (d.children) {{
                    d._children = d.children;
                    d.children = null;
                }} else {{
                    d.children = d._children;
                    d._children = null;
                }}

                update(d);
            }});

        // Add circles for nodes
        nodes.append("circle")
            .attr("r", function(d) {{
                return sizes[d.data.type] || sizes['Search'];
            }})
            .style("fill", function(d) {{
                return colors[d.data.type] || colors['Search'];
            }});

        // Add labels
        nodes.append("text")
            .attr("dy", function(d) {{
                return d.children || d._children ? -20 : 25;
            }})
            .attr("dx", function(d) {{
                return d.children || d._children ? 0 : 0;
            }})
            .style("font-size", function(d) {{
                if (d.data.type === 'AnalyticGoal') return "13px";
                if (d.data.type === 'Insight' || d.data.type === 'EmergentQuestion') return "11px";
                return "10px";
            }})
            .style("font-weight", function(d) {{
                return d.data.type === 'AnalyticGoal' ? "bold" : "normal";
            }})
            .text(function(d) {{
                const name = d.data.name || d.data.id || "Unknown";
                if (d.data.type === 'AnalyticGoal') {{
                    return name.length > 50 ? name.substring(0, 50) + "..." : name;
                }}
                return name.length > 30 ? name.substring(0, 30) + "..." : name;
            }});

        // Update function for expand/collapse
        function update(source) {{
            const treeData = treemap(root);
            const nodes = treeData.descendants();
            const links = treeData.descendants().slice(1);

            // Update nodes
            const node = g.selectAll(".node")
                .data(nodes, function(d) {{ return d.id || (d.id = ++i); }});

            const nodeEnter = node.enter().append("g")
                .attr("class", "node")
                .attr("transform", function(d) {{ return `translate(${{source.y0 || source.y}},${{source.x0 || source.x}})`; }});

            nodeEnter.append("circle")
                .attr("r", 1e-6)
                .style("fill", function(d) {{ return colors[d.data.type] || colors['Search']; }});

            nodeEnter.append("text")
                .attr("dy", ".35em")
                .text(function(d) {{ return d.data.name; }})
                .style("fill-opacity", 1e-6);

            const nodeUpdate = nodeEnter.merge(node);

            nodeUpdate.transition()
                .duration(750)
                .attr("transform", function(d) {{ return `translate(${{d.y}},${{d.x}})`; }});

            nodeUpdate.select("circle")
                .transition()
                .duration(750)
                .attr("r", function(d) {{ return sizes[d.data.type] || sizes['Search']; }});

            const nodeExit = node.exit().transition()
                .duration(750)
                .attr("transform", function(d) {{ return `translate(${{source.y}},${{source.x}})`; }})
                .remove();

            // Update links
            const link = g.selectAll(".link")
                .data(links, function(d) {{ return d.id; }});

            const linkEnter = link.enter().insert("path", "g")
                .attr("class", "link")
                .attr("d", function(d) {{
                    const o = {{x: source.x0 || source.x, y: source.y0 || source.y}};
                    return `M${{o.y}},${{o.x}}C${{o.y}},${{o.x}} ${{o.y}},${{o.x}} ${{o.y}},${{o.x}}`;
                }});

            linkEnter.merge(link).transition()
                .duration(750)
                .attr("d", function(d) {{
                    return `M${{d.y}},${{d.x}}C${{(d.y + d.parent.y) / 2}},${{d.x}} ${{(d.y + d.parent.y) / 2}},${{d.parent.x}} ${{d.parent.y}},${{d.parent.x}}`;
                }});

            link.exit().transition()
                .duration(750)
                .attr("d", function(d) {{
                    const o = {{x: source.x, y: source.y}};
                    return `M${{o.y}},${{o.x}}C${{o.y}},${{o.x}} ${{o.y}},${{o.x}} ${{o.y}},${{o.x}}`;
                }})
                .remove();

            nodes.forEach(function(d) {{
                d.x0 = d.x;
                d.y0 = d.y;
            }});
        }}

        // Add zoom functionality
        const zoom = d3.zoom()
            .scaleExtent([0.2, 3])
            .on("zoom", function(event) {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Control functions
        let i = 0;

        window.expandAll = function() {{
            function expand(d) {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
                if (d.children) {{
                    d.children.forEach(expand);
                }}
            }}
            expand(root);
            update(root);
        }};

        window.collapseAll = function() {{
            function collapse(d) {{
                if (d.children) {{
                    d._children = d.children;
                    d.children = null;
                    d._children.forEach(collapse);
                }}
            }}
            root.children.forEach(collapse);
            update(root);
        }};

        window.centerView = function() {{
            const bounds = g.node().getBBox();
            const fullWidth = width;
            const fullHeight = height;
            const widthScale = fullWidth / bounds.width;
            const heightScale = fullHeight / bounds.height;
            const scale = 0.7 * Math.min(widthScale, heightScale);
            const translate = [
                fullWidth / 2 - scale * bounds.x - scale * bounds.width / 2,
                fullHeight / 2 - scale * bounds.y - scale * bounds.height / 2
            ];

            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }};

        // Draw convergence edges showing many-to-one relationships
        function drawConvergenceEdges() {{
            // Create a flat list of all nodes with their positions
            const allNodes = [];
            function collectNodes(node) {{
                allNodes.push(node);
                if (node.children) {{
                    node.children.forEach(collectNodes);
                }}
                if (node._children) {{
                    node._children.forEach(collectNodes);
                }}
            }}
            collectNodes(root);

            // Create node lookup by ID
            const nodeById = {{}};
            allNodes.forEach(d => {{
                nodeById[d.data.id] = d;
            }});

            // Filter convergence edges to only those with visible nodes
            const visibleConvergenceEdges = convergenceEdges.filter(edge =>
                nodeById[edge.source] && nodeById[edge.target]
            );

            // Draw convergence edges
            const convergenceLinks = g.selectAll(".convergence-edge")
                .data(visibleConvergenceEdges);

            convergenceLinks.enter()
                .insert("path", ".node")
                .attr("class", "convergence-edge")
                .attr("stroke", function(d) {{
                    if (d.type === 'SUPPORTS') return '#4CAF50';
                    if (d.type === 'SPAWNS') return '#F44336';
                    return '#FF9800';
                }})
                .attr("stroke-width", 3)
                .attr("stroke-dasharray", "8,4")
                .attr("fill", "none")
                .attr("opacity", 0.8)
                .attr("marker-end", "url(#convergence-arrow)")
                .attr("d", function(d) {{
                    const source = nodeById[d.source];
                    const target = nodeById[d.target];
                    if (source && target) {{
                        const dx = target.y - source.y;
                        const dy = target.x - source.x;
                        const dr = Math.sqrt(dx * dx + dy * dy);
                        return `M${{source.y}},${{source.x}}A${{dr}},${{dr}} 0 0,1 ${{target.y}},${{target.x}}`;
                    }}
                    return "";
                }});
        }}

        // Define arrow marker for convergence edges
        const defs = svg.select("defs").empty() ? svg.append("defs") : svg.select("defs");
        defs.append("marker")
            .attr("id", "convergence-arrow")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 15)
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#333");

        // Draw convergence edges initially and update when tree changes
        drawConvergenceEdges();

        // Override the update function to redraw convergence edges
        const originalUpdate = update;
        update = function(source) {{
            originalUpdate(source);
            setTimeout(() => drawConvergenceEdges(), 800); // Redraw after tree animation
        }};

        console.log("Hierarchical tree visualization loaded with convergence edges");
        console.log("Tree structure: AnalyticGoal -> Questions -> Searches -> Data -> Insights -> EmergentQuestions");
        console.log("Convergence edges show many-to-one relationships (green=SUPPORTS, red=SPAWNS)");
        console.log("Click nodes to expand/collapse, use controls for full expand/collapse");
    </script>
</body>
</html>"""
        except Exception as e:
            print(f"DEBUG: Template formatting ERROR: {e}")
            print(f"DEBUG: Variables available - hierarchy_data: {type(hierarchy_data)}, convergence_edges: {type(convergence_edges)}")
            import traceback
            traceback.print_exc()
            # Return a simple template for debugging
            html = f"""<!DOCTYPE html>
<html><head><title>{title}</title></head>
<body><h1>Template Error: {e}</h1></body></html>"""

        return html

    def _build_investigation_hierarchy(self, wave_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build hierarchical tree structure showing convergence points where multiple nodes feed into synthesis"""

        nodes = wave_data.get('nodes', [])
        edges = wave_data.get('edges', [])
        investigation_goal = wave_data.get('investigation_goal', 'Investigation')

        # Create lookup dictionaries
        node_dict = {node['id']: node for node in nodes}

        # Group edges by type to understand the convergence patterns
        edges_by_type = {}
        for edge in edges:
            edge_type = edge.get('type', 'UNKNOWN')
            if edge_type not in edges_by_type:
                edges_by_type[edge_type] = []
            edges_by_type[edge_type].append(edge)

        # Group nodes by wave for proper ordering
        nodes_by_wave = {}
        for node in nodes:
            wave = node.get('wave', 0)
            if wave not in nodes_by_wave:
                nodes_by_wave[wave] = []
            nodes_by_wave[wave].append(node)

        def create_tree_node(node_id: str, supporting_nodes: list = None) -> Dict[str, Any]:
            """Create tree node with support information"""
            if node_id not in node_dict:
                return None

            node = node_dict[node_id]
            tree_node = {
                "name": node.get('name', 'Unknown'),
                "type": node.get('type', 'Unknown'),
                "id": node_id,
                "wave": node.get('wave', 0),
                "full_text": node.get('full_text', ''),
                "details": node.get('details', {}),
                "children": []
            }

            # Add support information if this node is supported by multiple others
            if supporting_nodes and len(supporting_nodes) > 1:
                tree_node["supported_by"] = [
                    {"id": sup_id, "name": node_dict.get(sup_id, {}).get('name', 'Unknown')}
                    for sup_id in supporting_nodes if sup_id in node_dict
                ]

            return tree_node

        def find_supporting_nodes(target_id: str, edge_type: str) -> list:
            """Find all nodes that support a target node via specific edge type"""
            supporting = []
            if edge_type in edges_by_type:
                for edge in edges_by_type[edge_type]:
                    if edge['target'] == target_id:
                        supporting.append(edge['source'])
            return supporting

        def build_convergence_hierarchy():
            """Build hierarchy showing convergence patterns"""

            # Find root (AnalyticGoal)
            root_node = None
            for node in nodes:
                if node.get('type') == 'AnalyticGoal':
                    root_node = create_tree_node(node['id'])
                    break

            if not root_node:
                root_node = {
                    "name": investigation_goal,
                    "type": "AnalyticGoal",
                    "id": "root",
                    "wave": 0,
                    "full_text": investigation_goal,
                    "children": []
                }

            processed_nodes = set()

            # Build wave by wave to show progression
            for wave_num in sorted(nodes_by_wave.keys()):
                if wave_num == 0:  # Skip root wave
                    continue

                wave_nodes = nodes_by_wave[wave_num]

                # Process each node type in the proper order for this wave
                for node_type in ['InvestigationQuestion', 'Search', 'DataPoint', 'Insight', 'EmergentQuestion']:

                    type_nodes = [n for n in wave_nodes if n.get('type') == node_type]

                    for node in type_nodes:
                        if node['id'] in processed_nodes:
                            continue

                        # Find where to attach this node based on its type
                        if node_type == 'InvestigationQuestion':
                            # Questions attach to root
                            tree_node = create_tree_node(node['id'])
                            root_node['children'].append(tree_node)
                            processed_nodes.add(node['id'])

                        elif node_type == 'Search':
                            # Searches attach to questions or emergent questions
                            parent_questions = find_supporting_nodes(node['id'], 'LEADS_TO')
                            parent_questions.extend(find_supporting_nodes(node['id'], 'GENERATES'))

                            if parent_questions:
                                # Find the parent question in the tree
                                parent_tree_node = self._find_node_in_tree(root_node, parent_questions[0])
                                if parent_tree_node:
                                    search_tree_node = create_tree_node(node['id'])
                                    parent_tree_node['children'].append(search_tree_node)
                                    processed_nodes.add(node['id'])

                        elif node_type == 'DataPoint':
                            # DataPoints attach to searches
                            parent_searches = find_supporting_nodes(node['id'], 'PRODUCES')

                            for parent_search_id in parent_searches:
                                parent_tree_node = self._find_node_in_tree(root_node, parent_search_id)
                                if parent_tree_node and node['id'] not in processed_nodes:
                                    data_tree_node = create_tree_node(node['id'])
                                    parent_tree_node['children'].append(data_tree_node)
                                    processed_nodes.add(node['id'])

                        elif node_type == 'Insight':
                            # Insights are supported by MULTIPLE DataPoints - show convergence
                            supporting_datapoints = find_supporting_nodes(node['id'], 'SUPPORTS')

                            if supporting_datapoints:
                                # Create insight under the FIRST supporting datapoint, but note all supporters
                                first_parent_id = supporting_datapoints[0]
                                parent_tree_node = self._find_node_in_tree(root_node, first_parent_id)

                                if parent_tree_node and node['id'] not in processed_nodes:
                                    # Create insight node with information about ALL supporting datapoints
                                    insight_tree_node = create_tree_node(node['id'], supporting_datapoints)
                                    parent_tree_node['children'].append(insight_tree_node)
                                    processed_nodes.add(node['id'])

                        elif node_type == 'EmergentQuestion':
                            # EmergentQuestions are spawned by MULTIPLE Insights - show convergence
                            supporting_insights = find_supporting_nodes(node['id'], 'SPAWNS')

                            if supporting_insights:
                                # Create emergent question under the FIRST supporting insight, but note all supporters
                                first_parent_id = supporting_insights[0]
                                parent_tree_node = self._find_node_in_tree(root_node, first_parent_id)

                                if parent_tree_node and node['id'] not in processed_nodes:
                                    # Create emergent question node with information about ALL supporting insights
                                    eq_tree_node = create_tree_node(node['id'], supporting_insights)
                                    parent_tree_node['children'].append(eq_tree_node)
                                    processed_nodes.add(node['id'])

            # Clean up empty children arrays
            self._clean_empty_children(root_node)
            return root_node

        return build_convergence_hierarchy()

    def _extract_convergence_edges(self, wave_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract edges that show convergence patterns (many-to-one relationships)"""
        edges = wave_data.get('edges', [])
        nodes = wave_data.get('nodes', [])
        node_dict = {node['id']: node for node in nodes}

        convergence_edges = []

        # Group edges by target to find convergence points
        edges_by_target = {}
        for edge in edges:
            target = edge['target']
            if target not in edges_by_target:
                edges_by_target[target] = []
            edges_by_target[target].append(edge)

        # Find convergence points (nodes with multiple incoming edges of same type)
        for target_id, target_edges in edges_by_target.items():
            if len(target_edges) > 1:
                # This is a convergence point - multiple sources feeding one target
                target_node = node_dict.get(target_id)
                if target_node:
                    for edge in target_edges:
                        source_node = node_dict.get(edge['source'])
                        if source_node:
                            convergence_edges.append({
                                'source': edge['source'],
                                'target': target_id,
                                'type': edge.get('type', 'UNKNOWN'),
                                'source_node': source_node,
                                'target_node': target_node,
                                'is_convergence': True
                            })

        return convergence_edges

    def _find_node_in_tree(self, root: Dict[str, Any], target_id: str) -> Dict[str, Any]:
        """Find a node in the tree by ID"""
        if root.get('id') == target_id:
            return root

        if 'children' in root:
            for child in root['children']:
                found = self._find_node_in_tree(child, target_id)
                if found:
                    return found

        return None

    def _add_wave_continuation(self, search_tree_node: Dict[str, Any], search_id: str,
                              children_dict: Dict, node_dict: Dict, processed_nodes: set):
        """Recursively add continuation of investigation waves"""

        # Add DataPoints from this search
        if search_id in children_dict:
            for data_id in children_dict[search_id]:
                data_node = node_dict.get(data_id)
                if data_node and data_node.get('type') == 'DataPoint':
                    if data_id not in processed_nodes:
                        data_tree_node = {
                            "name": data_node.get('name', 'Unknown'),
                            "type": data_node.get('type', 'Unknown'),
                            "id": data_id,
                            "wave": data_node.get('wave', 0),
                            "full_text": data_node.get('full_text', ''),
                            "details": data_node.get('details', {}),
                            "children": []
                        }
                        search_tree_node['children'].append(data_tree_node)
                        processed_nodes.add(data_id)

                        # Add Insights from this DataPoint
                        if data_id in children_dict:
                            for insight_id in children_dict[data_id]:
                                insight_node = node_dict.get(insight_id)
                                if insight_node and insight_node.get('type') == 'Insight':
                                    if insight_id not in processed_nodes:
                                        insight_tree_node = {
                                            "name": insight_node.get('name', 'Unknown'),
                                            "type": insight_node.get('type', 'Unknown'),
                                            "id": insight_id,
                                            "wave": insight_node.get('wave', 0),
                                            "full_text": insight_node.get('full_text', ''),
                                            "details": insight_node.get('details', {}),
                                            "children": []
                                        }
                                        data_tree_node['children'].append(insight_tree_node)
                                        processed_nodes.add(insight_id)

                                        # Add EmergentQuestions from this Insight
                                        if insight_id in children_dict:
                                            for eq_id in children_dict[insight_id]:
                                                eq_node = node_dict.get(eq_id)
                                                if eq_node and eq_node.get('type') == 'EmergentQuestion':
                                                    if eq_id not in processed_nodes:
                                                        eq_tree_node = {
                                                            "name": eq_node.get('name', 'Unknown'),
                                                            "type": eq_node.get('type', 'Unknown'),
                                                            "id": eq_id,
                                                            "wave": eq_node.get('wave', 0),
                                                            "full_text": eq_node.get('full_text', ''),
                                                            "details": eq_node.get('details', {}),
                                                            "children": []
                                                        }
                                                        insight_tree_node['children'].append(eq_tree_node)
                                                        processed_nodes.add(eq_id)

    def _clean_empty_children(self, node: Dict[str, Any]):
        """Remove empty children arrays recursively"""
        if 'children' in node:
            if not node['children']:
                del node['children']
            else:
                for child in node['children']:
                    self._clean_empty_children(child)

    def _generate_wave_hierarchy_html(self, wave_data: Dict[str, Any], title: str) -> str:
        """Generate hierarchical HTML for wave visualization showing clear wave structure"""
        nodes = wave_data.get('nodes', [])
        edges = wave_data.get('edges', [])
        wave_count = wave_data.get('wave_count', 0)

        # Build hierarchical structure from wave data
        hierarchy_data = self._build_wave_hierarchy(wave_data)

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
            max-width: 1600px;
            margin: 0 auto;
        }}
        h1 {{
            color: white;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .wave-info {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            text-align: center;
        }}
        .graph-container {{
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }}
        #hierarchy-chart {{
            width: 100%;
            height: 1000px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
        }}

        .node {{
            cursor: pointer;
        }}

        .node circle {{
            stroke: #fff;
            stroke-width: 3px;
        }}

        .node text {{
            font: 12px sans-serif;
            pointer-events: none;
            text-anchor: middle;
        }}

        .link {{
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
        }}

        .wave-link {{
            stroke: #9C27B0;
            stroke-width: 3px;
            stroke-dasharray: 8,4;
        }}

        .dependency-link {{
            stroke: #FF4444;
            stroke-width: 4px;
            stroke-dasharray: 5,5;
        }}

        .tooltip {{
            position: absolute;
            padding: 12px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 8px;
            font-size: 12px;
            max-width: 400px;
            pointer-events: none;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
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
            padding: 10px 18px;
            background: #f8f9fa;
            border-radius: 25px;
            border: 2px solid #e9ecef;
            font-weight: 500;
        }}
        .color-circle {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 2px solid rgba(0,0,0,0.2);
        }}
        .wave-line {{
            width: 35px;
            height: 4px;
            background: #9C27B0;
            border-radius: 2px;
        }}
        .dependency-line {{
            width: 35px;
            height: 4px;
            background: #FF4444;
            border-radius: 2px;
        }}
        .wave-header {{
            font-size: 14px;
            font-weight: bold;
            fill: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>

        <div class="wave-info">
            <h3>Hierarchical Wave Structure: {wave_data.get('investigation_goal', 'Unknown Goal')}</h3>
            <p><strong>{wave_count} Waves</strong> showing true dependencies in tree structure</p>
        </div>

        <div class="graph-container">
            <div class="legend">
                <div class="legend-item">
                    <span class="color-circle" style="background: #9C27B0;"></span>
                    <span>Investigation Root</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: #E91E63;"></span>
                    <span>Wave</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: #4CAF50;"></span>
                    <span>Searches</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: #FF9800;"></span>
                    <span>Insights</span>
                </div>
                <div class="legend-item">
                    <span class="color-circle" style="background: #F44336;"></span>
                    <span>Emergent Questions</span>
                </div>
                <div class="legend-item">
                    <span class="dependency-line"></span>
                    <span>True Dependencies</span>
                </div>
            </div>

            <svg id="hierarchy-chart"></svg>
        </div>
    </div>

    <script>
        // Wave hierarchy data from Python
        const hierarchyData = {json.dumps(hierarchy_data, indent=2)};
        const convergenceEdges = {json.dumps(convergence_edges, indent=2)};

        // Set up SVG dimensions
        const margin = {{top: 60, right: 120, bottom: 60, left: 120}};
        const width = 1400 - margin.left - margin.right;
        const height = 1000 - margin.top - margin.bottom;

        // Create SVG
        const svg = d3.select("#hierarchy-chart")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g")
            .attr("transform", `translate(${{margin.left}},${{margin.top}})`);

        // Create tree layout
        const treemap = d3.tree()
            .size([width, height])
            .separation((a, b) => {{
                // More spacing between waves
                if (a.data.type === 'Wave' || b.data.type === 'Wave') {{
                    return 2;
                }}
                return 1;
            }});

        // Colors by node type
        const colors = {{
            'Root': '#9C27B0',
            'Wave': '#E91E63',
            'DrivingQuestion': '#E91E63',
            'Search': '#4CAF50',
            'DataPoint': '#2196F3',
            'Insight': '#FF9800',
            'EmergentQuestion': '#F44336'
        }};

        // Node sizes by type
        const sizes = {{
            'Root': 18,
            'Wave': 15,
            'DrivingQuestion': 10,
            'Search': 8,
            'DataPoint': 6,
            'Insight': 12,
            'EmergentQuestion': 10
        }};

        // Create hierarchy
        const root = d3.hierarchy(hierarchyData);

        // Apply tree layout
        treemap(root);

        // Tooltip
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // Add links (before nodes so they appear behind)
        const links = g.selectAll(".link")
            .data(root.descendants().slice(1))
            .enter().append("path")
            .attr("class", function(d) {{
                // Style dependency links differently
                if (d.data.dependency) return "link dependency-link";
                if (d.data.wave_boundary) return "link wave-link";
                return "link";
            }})
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
                let content = `<strong>${{d.data.name}}</strong><br/>`;
                content += `<strong>Type:</strong> ${{d.data.type}}<br/>`;

                if (d.data.wave) {{
                    content += `<strong>Wave:</strong> ${{d.data.wave}}<br/>`;
                }}

                if (d.data.full_text) {{
                    content += `<br/>${{d.data.full_text.substring(0, 300)}}${{d.data.full_text.length > 300 ? '...' : ''}}`;
                }}

                if (d.data.details) {{
                    content += '<br/><strong>Details:</strong><br/>';
                    Object.entries(d.data.details).forEach(([key, value]) => {{
                        content += `${{key}}: ${{value}}<br/>`;
                    }});
                }}

                tooltip.html(content)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition().duration(500).style("opacity", 0);
            }})
            .on("click", function(event, d) {{
                console.log("Hierarchy node clicked:", d.data);
            }});

        // Add circles for nodes
        nodes.append("circle")
            .attr("r", function(d) {{
                return sizes[d.data.type] || sizes['Search'];
            }})
            .style("fill", function(d) {{
                return colors[d.data.type] || colors['Search'];
            }});

        // Add labels
        nodes.append("text")
            .attr("dy", function(d) {{
                // Position text based on node type and hierarchy level
                if (d.data.type === 'Root' || d.data.type === 'Wave') {{
                    return -25; // Above large nodes
                }}
                return d.children ? -15 : 20; // Above parent nodes, below leaf nodes
            }})
            .attr("class", function(d) {{
                return d.data.type === 'Wave' ? 'wave-header' : '';
            }})
            .style("font-size", function(d) {{
                if (d.data.type === 'Root') return "16px";
                if (d.data.type === 'Wave') return "14px";
                return "11px";
            }})
            .style("font-weight", function(d) {{
                return (d.data.type === 'Root' || d.data.type === 'Wave') ? "bold" : "normal";
            }})
            .text(function(d) {{
                const name = d.data.name || d.data.id || "Unknown";
                if (d.data.type === 'Root') return name;
                if (d.data.type === 'Wave') return name;
                return name.length > 25 ? name.substring(0, 25) + "..." : name;
            }});

        // Add zoom functionality
        const zoom = d3.zoom()
            .scaleExtent([0.2, 4])
            .on("zoom", function(event) {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Initial fit to content
        setTimeout(() => {{
            const bounds = g.node().getBBox();
            const fullWidth = width;
            const fullHeight = height;
            const widthScale = fullWidth / bounds.width;
            const heightScale = fullHeight / bounds.height;
            const scale = 0.7 * Math.min(widthScale, heightScale);
            const translate = [
                fullWidth / 2 - scale * bounds.x - scale * bounds.width / 2,
                fullHeight / 2 - scale * bounds.y - scale * bounds.height / 2
            ];

            svg.call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
        }}, 100);

        console.log("Hierarchical wave visualization loaded with", root.descendants().length, "nodes");
        console.log("Wave dependencies shown in tree structure");
    </script>
</body>
</html>"""

        return html

    def _build_wave_hierarchy(self, wave_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build hierarchical structure from wave data for D3.js tree layout"""

        investigation_goal = wave_data.get('investigation_goal', 'Investigation')
        nodes = wave_data.get('nodes', [])
        edges = wave_data.get('edges', [])

        # Create root node
        root = {
            "name": investigation_goal[:60] + "..." if len(investigation_goal) > 60 else investigation_goal,
            "type": "Root",
            "id": "root",
            "full_text": investigation_goal,
            "children": []
        }

        # Group nodes by wave
        waves_dict = {}
        for node in nodes:
            wave_num = node.get('wave', 0)
            if wave_num not in waves_dict:
                waves_dict[wave_num] = {
                    'wave_nodes': [],
                    'driving_questions': [],
                    'searches': [],
                    'insights': [],
                    'emergent_questions': []
                }

            node_type = node.get('type', '')
            if node_type == 'Wave':
                waves_dict[wave_num]['wave_nodes'].append(node)
            elif node_type == 'DrivingQuestion':
                waves_dict[wave_num]['driving_questions'].append(node)
            elif node_type == 'Search':
                waves_dict[wave_num]['searches'].append(node)
            elif node_type == 'Insight':
                waves_dict[wave_num]['insights'].append(node)
            elif node_type == 'EmergentQuestion':
                waves_dict[wave_num]['emergent_questions'].append(node)

        # Build wave hierarchy
        for wave_num in sorted(waves_dict.keys()):
            if wave_num == 0:  # Skip wave 0 (root level)
                continue

            wave_data = waves_dict[wave_num]

            # Create wave node
            wave_node = {
                "name": f"Wave {wave_num}",
                "type": "Wave",
                "id": f"wave_{wave_num}",
                "wave": wave_num,
                "children": []
            }

            # Add searches as children of wave
            for search in wave_data['searches']:
                search_node = {
                    "name": search.get('name', f"Search {search.get('id', '')}"),
                    "type": "Search",
                    "id": search.get('id'),
                    "wave": wave_num,
                    "full_text": search.get('full_text', ''),
                    "details": search.get('details', {}),
                    "children": []
                }
                wave_node["children"].append(search_node)

            # Add insights as children of wave
            for insight in wave_data['insights']:
                insight_node = {
                    "name": insight.get('name', f"Insight {insight.get('id', '')}"),
                    "type": "Insight",
                    "id": insight.get('id'),
                    "wave": wave_num,
                    "full_text": insight.get('full_text', ''),
                    "children": []
                }
                wave_node["children"].append(insight_node)

                # Add emergent questions as children of insights
                for eq in wave_data['emergent_questions']:
                    eq_node = {
                        "name": eq.get('name', f"Question {eq.get('id', '')}"),
                        "type": "EmergentQuestion",
                        "id": eq.get('id'),
                        "wave": wave_num,
                        "full_text": eq.get('full_text', ''),
                        "dependency": True  # Mark as dependency for next wave
                    }
                    insight_node["children"].append(eq_node)

            root["children"].append(wave_node)

        return root


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