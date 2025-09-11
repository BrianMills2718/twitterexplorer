#!/usr/bin/env python3
import os
import glob
import json

files = glob.glob('investigation_graph_*.json')
if not files:
    print("No graph files found")
    exit()

latest = max(files, key=os.path.getctime)
print(f'Latest graph: {latest}')

try:
    with open(latest, 'r') as f:
        data = json.load(f)
    
    insights = [n for n in data['nodes'].values() if n.get('node_type') == 'Insight']
    print(f'\nTotal insights: {len(insights)}')
    
    for i, insight in enumerate(insights):
        print(f'Insight {i+1}:')
        print(f'  Title: "{insight.get("properties", {}).get("title", "No Title")}"')
        print(f'  Confidence: {insight.get("properties", {}).get("confidence", "No Confidence")}')
        print(f'  Content: "{insight.get("properties", {}).get("content", "No Content")[:100]}..."')
        print()
        
except Exception as e:
    print(f"Error reading graph file: {e}")