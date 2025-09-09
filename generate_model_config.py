#!/usr/bin/env python3
"""
Generate model configuration files from templates
"""

import sys
import os
import yaml
import argparse
from pathlib import Path
from datetime import datetime

def load_templates():
    """Load configuration templates"""
    templates_path = Path(__file__).parent / "config" / "models_templates.yaml"
    
    if not templates_path.exists():
        raise FileNotFoundError(f"Templates file not found: {templates_path}")
    
    with open(templates_path, 'r') as f:
        return yaml.safe_load(f)

def generate_config(template_name, output_path):
    """Generate configuration file from template"""
    
    templates = load_templates()
    
    if template_name not in templates:
        available = ", ".join(templates.keys())
        raise ValueError(f"Template '{template_name}' not found. Available: {available}")
    
    config = templates[template_name]
    
    # Add metadata
    config['_metadata'] = {
        'generated_from_template': template_name,
        'generated_at': str(datetime.now()),
        'note': 'Edit this file to customize model assignments'
    }
    
    # Create directory if it doesn't exist, but handle the case where output_path has no directory
    output_dir = os.path.dirname(output_path)
    if output_dir:  # Only create directory if there is one
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(f"# TwitterExplorer Model Configuration\n")
        f.write(f"# Generated from template: {template_name}\n")
        f.write(f"# Edit this file to customize model assignments\n\n")
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"[OK] Configuration generated: {output_path}")
    print(f"[INFO] Template used: {template_name}")

def main():
    parser = argparse.ArgumentParser(description='Generate TwitterExplorer model configuration')
    parser.add_argument('template', choices=['cost_optimized', 'speed_optimized', 'quality_optimized', 'balanced'],
                        help='Configuration template to use')
    parser.add_argument('--output', default='config/models.yaml', 
                        help='Output configuration file path')
    
    args = parser.parse_args()
    
    try:
        generate_config(args.template, args.output)
    except Exception as e:
        print(f"[ERROR] Failed to generate configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()