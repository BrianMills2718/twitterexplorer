#!/usr/bin/env python3
"""
TwitterExplorer Investigation Results Examiner
============================================

Tool to examine and analyze recent investigation results and output files.
"""

import json
import os
from pathlib import Path
from datetime import datetime
import glob

def find_recent_files():
    """Find the most recent investigation output files"""
    
    print("TwitterExplorer Investigation Results")
    print("=" * 37)
    
    # Find recent JSON investigation files
    json_files = glob.glob("investigation_graph_*.json")
    html_files = glob.glob("investigation_graph_*.html") 
    
    if json_files:
        # Sort by modification time
        json_files.sort(key=os.path.getmtime, reverse=True)
        latest_json = json_files[0]
        
        print(f"Latest Investigation Graph: {latest_json}")
        print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(latest_json))}")
        
        # Load and examine the JSON data
        try:
            with open(latest_json, 'r') as f:
                data = json.load(f)
            
            print(f"\nInvestigation Summary:")
            if 'session_id' in data:
                print(f"Session ID: {data['session_id']}")
            if 'query' in data:
                print(f"Query: {data['query']}")
            if 'nodes' in data:
                print(f"Graph Nodes: {len(data['nodes'])}")
                
                # Count node types
                node_types = {}
                for node in data['nodes']:
                    node_type = node.get('type', 'Unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1
                
                print("Node Types:")
                for node_type, count in node_types.items():
                    print(f"  - {node_type}: {count}")
            
            if 'links' in data:
                print(f"Graph Edges: {len(data['links'])}")
                
                # Count edge types  
                edge_types = {}
                for edge in data['links']:
                    edge_type = edge.get('type', 'Unknown')
                    edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
                
                print("Edge Types:")
                for edge_type, count in edge_types.items():
                    print(f"  - {edge_type}: {count}")
        
        except Exception as e:
            print(f"Error reading JSON: {e}")
        
        # Check for corresponding HTML file
        html_file = latest_json.replace('.json', '.html')
        if os.path.exists(html_file):
            print(f"\nVisualization available: {html_file}")
            print("Open this HTML file in your browser to see the interactive graph!")
    
    else:
        print("No investigation graph files found.")
    
    # Check session logs
    print(f"\n{'-'*50}")
    print("Recent Session Logs:")
    
    logs_dir = Path("logs/sessions")
    if logs_dir.exists():
        today = datetime.now().strftime("%Y-%m-%d")
        today_dir = logs_dir / today
        
        if today_dir.exists():
            log_files = list(today_dir.glob("*.jsonl"))
            if log_files:
                latest_log = max(log_files, key=os.path.getmtime)
                print(f"Latest session log: {latest_log}")
                print(f"Modified: {datetime.fromtimestamp(os.path.getmtime(latest_log))}")
                
                # Read first line to get session info
                try:
                    with open(latest_log, 'r') as f:
                        first_line = f.readline()
                        if first_line.strip():
                            session_data = json.loads(first_line)
                            if 'user_query' in session_data:
                                print(f"Query: {session_data['user_query']}")
                            if 'config' in session_data:
                                config = session_data['config']
                                print(f"Max searches: {config.get('max_searches', 'N/A')}")
                                print(f"Satisfaction threshold: {config.get('satisfaction_threshold', 'N/A')}")
                except Exception as e:
                    print(f"Error reading log: {e}")
            else:
                print("No session logs found for today.")
        else:
            print("No session logs for today.")
    else:
        print("Session logs directory not found.")
    
    # Check for other output files
    print(f"\n{'-'*50}")
    print("Other Output Files:")
    
    other_files = [
        "current_investigation_graph.json",
        "complete_ontology_graph.html", 
        "interactive_ontology_graph.html"
    ]
    
    for file_path in other_files:
        if os.path.exists(file_path):
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"- {file_path} (modified: {mod_time})")
    
    print(f"\n{'-'*50}")
    print("How to view your results:")
    print("1. JSON files: Contains structured investigation data")
    print("2. HTML files: Interactive visualizations - open in browser")
    print("3. Session logs: Detailed investigation process logs")
    print("4. Use the Streamlit app's export feature for formatted reports")

if __name__ == "__main__":
    find_recent_files()