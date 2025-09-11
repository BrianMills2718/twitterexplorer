#!/usr/bin/env python3
"""
Extract and Convert Investigation Graph Data for D3.js Visualization
================================================================

Converts TwitterExplorer investigation results to the D3.js format used in Streamlit app.
"""

import json
import glob
import os
from datetime import datetime

def convert_to_d3_format(graph_data):
    """Convert investigation graph data to D3.js format"""
    
    d3_nodes = []
    d3_links = []
    node_id_map = {}
    
    # Process nodes
    if 'nodes' in graph_data:
        if isinstance(graph_data['nodes'], dict):
            # Handle dictionary format (node_id -> node_data)
            for node_id, node_data in graph_data['nodes'].items():
                node_type = node_data.get('node_type', 'Unknown')
                properties = node_data.get('properties', {})
                
                # Create D3.js node
                d3_node = {
                    'id': node_id,
                    'label': properties.get('text', properties.get('query', node_id[:8])),
                    'type': node_type,
                    'importance': 1.0 if node_type == 'AnalyticQuestion' else 0.8,
                    'description': properties.get('text', ''),
                    'properties': properties
                }
                d3_nodes.append(d3_node)
                node_id_map[node_id] = node_id
        
        elif isinstance(graph_data['nodes'], list):
            # Handle list format
            for node in graph_data['nodes']:
                d3_nodes.append({
                    'id': node.get('id', str(len(d3_nodes))),
                    'label': node.get('label', node.get('text', 'Node')),
                    'type': node.get('type', node.get('node_type', 'Unknown')),
                    'importance': node.get('importance', 0.8),
                    'description': node.get('description', ''),
                    'properties': node.get('properties', {})
                })
    
    # Process edges/links
    if 'edges' in graph_data:
        if isinstance(graph_data['edges'], dict):
            # Handle dictionary format
            for edge_id, edge_data in graph_data['edges'].items():
                source_id = edge_data.get('source_node_id')
                target_id = edge_data.get('target_node_id') 
                edge_type = edge_data.get('edge_type', 'CONNECTS')
                
                if source_id and target_id:
                    d3_links.append({
                        'source': source_id,
                        'target': target_id,
                        'type': edge_type
                    })
    
    elif 'links' in graph_data:
        # Handle links format
        for link in graph_data['links']:
            d3_links.append({
                'source': link.get('source'),
                'target': link.get('target'),
                'type': link.get('type', 'CONNECTS')
            })
    
    return {
        'nodes': d3_nodes,
        'links': d3_links
    }

def find_and_convert_latest_investigation():
    """Find the latest investigation and convert to D3.js format"""
    
    print("Finding Latest Investigation Graph Data")
    print("=" * 40)
    
    # Find all investigation JSON files
    json_files = glob.glob("investigation_graph_*.json")
    
    if not json_files:
        print("No investigation graph files found.")
        return None
    
    # Sort by modification time (most recent first)
    json_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = json_files[0]
    
    print(f"Latest file: {latest_file}")
    print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(latest_file))}")
    
    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
        
        print(f"Original format - Nodes: {len(data.get('nodes', []))}, Links/Edges: {len(data.get('links', data.get('edges', [])))}")
        
        # Convert to D3.js format
        d3_data = convert_to_d3_format(data)
        
        print(f"Converted format - Nodes: {len(d3_data['nodes'])}, Links: {len(d3_data['links'])}")
        
        # Save D3.js format for Streamlit app
        d3_filename = "streamlit_graph_data.json"
        with open(d3_filename, 'w') as f:
            json.dump(d3_data, f, indent=2)
        
        print(f"D3.js data saved to: {d3_filename}")
        
        # Show sample of converted data
        print("\nSample Nodes:")
        for node in d3_data['nodes'][:3]:
            print(f"  - {node['type']}: {node['label'][:50]}...")
        
        if d3_data['links']:
            print(f"\nSample Links:")
            for link in d3_data['links'][:3]:
                print(f"  - {link['type']}: {link['source']} -> {link['target']}")
        
        return d3_data
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return None

def create_standalone_html(d3_data, output_file="bob_lazar_investigation.html"):
    """Create a standalone HTML file with D3.js visualization"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Bob Lazar Investigation - Interactive Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 15px;
        }}
        
        .title {{
            font-size: 28px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
        }}
        
        .subtitle {{
            font-size: 14px;
            color: #7f8c8d;
            margin: 5px 0 0 0;
        }}
        
        #graph {{
            width: 100%;
            height: 700px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            background: white;
        }}
        
        .node {{
            cursor: move;
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .link {{
            fill: none;
            stroke-opacity: 0.6;
        }}
        
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            font-size: 12px;
            max-width: 300px;
            z-index: 1000;
        }}
        
        .node-label {{
            font-family: Arial, sans-serif;
            font-size: 10px;
            text-anchor: middle;
            pointer-events: none;
            fill: #333;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .stat {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">Bob Lazar Investigation - Knowledge Graph</div>
            <div class="subtitle">Interactive visualization of debunking information and expert analysis</div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-value">{len(d3_data['nodes'])}</div>
                <div class="stat-label">Nodes</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(d3_data['links'])}</div>
                <div class="stat-label">Connections</div>
            </div>
            <div class="stat">
                <div class="stat-value">{len(set(node['type'] for node in d3_data['nodes']))}</div>
                <div class="stat-label">Node Types</div>
            </div>
        </div>
        
        <div id="graph"></div>
    </div>
    
    <script>
        const graphData = {json.dumps(d3_data)};
        
        // Set up dimensions
        const width = document.getElementById('graph').offsetWidth;
        const height = 700;
        
        // Create SVG
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom().on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }}));
        
        const g = svg.append("g");
        
        // Create tooltip
        const tooltip = d3.select("body")
            .append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        // Color scale for node types
        const color = d3.scaleOrdinal([
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", 
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ]);
        
        // Create simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("center", d3.forceCenter(width / 2, height / 2));
        
        // Create links
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke", d => color(d.type))
            .attr("stroke-width", 2);
        
        // Create nodes
        const node = g.append("g")
            .selectAll("circle")
            .data(graphData.nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => Math.max(8, Math.min(25, (d.importance || 1) * 20)))
            .attr("fill", d => color(d.type))
            .call(drag(simulation))
            .on("mouseover", function(event, d) {{
                tooltip.transition().duration(200).style("opacity", .9);
                tooltip.html(`
                    <strong>${{d.label}}</strong><br/>
                    Type: ${{d.type}}<br/>
                    ${{d.description ? 'Description: ' + d.description.substring(0, 100) + '...<br/>' : ''}}
                    ${{Object.entries(d.properties || {{}}).slice(0, 3).map(([k,v]) => k + ': ' + (v.toString().substring(0, 50) + (v.toString().length > 50 ? '...' : ''))).join('<br/>') }}
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", function(d) {{
                tooltip.transition().duration(500).style("opacity", 0);
            }});
        
        // Add labels
        const label = g.append("g")
            .selectAll("text")
            .data(graphData.nodes)
            .enter().append("text")
            .attr("class", "node-label")
            .text(d => d.label.length > 15 ? d.label.substring(0, 15) + '...' : d.label)
            .attr("dy", 30);
        
        // Update positions on tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});
        
        // Drag functionality
        function drag(simulation) {{
            return d3.drag()
                .on("start", function(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }})
                .on("drag", function(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }})
                .on("end", function(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }});
        }}
    </script>
</body>
</html>"""

    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"Standalone HTML visualization created: {output_file}")
    return output_file

if __name__ == "__main__":
    d3_data = find_and_convert_latest_investigation()
    
    if d3_data:
        html_file = create_standalone_html(d3_data)
        print(f"\nTo view your Bob Lazar investigation graph:")
        print(f"1. Open: {html_file}")
        print(f"2. Or use: start {html_file}")
        print(f"3. Interactive D3.js graph with drag, zoom, and hover!")
    else:
        print("No investigation data found to convert.")