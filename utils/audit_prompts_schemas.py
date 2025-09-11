#!/usr/bin/env python3
"""
Audit script to locate all prompts and schemas across the codebase
"""
import os
import re
from pathlib import Path

def find_prompts_and_schemas():
    """Find all LLM prompts and Pydantic schemas in the codebase"""
    
    results = {
        'schemas': [],
        'prompts': [],
        'files_analyzed': []
    }
    
    codebase_dir = Path('.')
    python_files = list(codebase_dir.glob('*.py'))
    
    for file_path in python_files:
        if file_path.name.startswith('.'):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                results['files_analyzed'].append(str(file_path))
                
                # Find Pydantic schemas (BaseModel classes)
                schema_pattern = r'class\s+(\w+)\(BaseModel\):(.*?)(?=\n(?:class|\Z))'
                schema_matches = re.findall(schema_pattern, content, re.DOTALL)
                
                for schema_name, schema_body in schema_matches:
                    # Extract field descriptions
                    field_pattern = r'(\w+):\s*[^=]*=\s*Field\(description="([^"]+)"'
                    fields = re.findall(field_pattern, schema_body)
                    
                    results['schemas'].append({
                        'file': str(file_path),
                        'class_name': schema_name,
                        'fields': fields,
                        'line_start': content[:content.find(f'class {schema_name}(BaseModel)')].count('\n') + 1 if f'class {schema_name}(BaseModel)' in content else 0
                    })
                
                # Find LLM prompts (multiline strings with f""")
                prompt_patterns = [
                    r'prompt\s*=\s*f?"""(.*?)"""',
                    r'prompt\s*=\s*f?\'\'\'(.*?)\'\'\'',
                    r'messages\s*=\s*\[.*?"content":\s*f?"""(.*?)""".*?\]',
                    r'TASK:|INVESTIGATION:|REQUIREMENTS:|FOCUS:|EXAMPLES:'
                ]
                
                for pattern in prompt_patterns:
                    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        prompt_text = match.group(1) if match.groups() else match.group(0)
                        
                        # Skip very short matches (likely false positives)
                        if len(prompt_text.strip()) < 50:
                            continue
                            
                        results['prompts'].append({
                            'file': str(file_path),
                            'line': line_num,
                            'preview': prompt_text.strip()[:200] + '...' if len(prompt_text) > 200 else prompt_text.strip(),
                            'length': len(prompt_text.strip()),
                            'type': 'multiline_string' if '"""' in match.group(0) else 'keyword'
                        })
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return results

def print_audit_report():
    """Print comprehensive audit report"""
    results = find_prompts_and_schemas()
    
    print("# TwitterExplorer Prompt & Schema Audit Report")
    print("=" * 60)
    
    print(f"\nFiles Analyzed: {len(results['files_analyzed'])}")
    for file in sorted(results['files_analyzed']):
        print(f"  - {file}")
    
    print(f"\n## Pydantic Schemas Found: {len(results['schemas'])}")
    print("-" * 40)
    
    schema_files = {}
    for schema in results['schemas']:
        file_name = schema['file']
        if file_name not in schema_files:
            schema_files[file_name] = []
        schema_files[file_name].append(schema)
    
    for file, schemas in sorted(schema_files.items()):
        print(f"\n### {file}")
        for schema in schemas:
            print(f"  **{schema['class_name']}** (line {schema['line_start']})")
            if schema['fields']:
                for field_name, field_desc in schema['fields']:
                    print(f"    - {field_name}: {field_desc}")
            else:
                print("    - No Field descriptions found")
    
    print(f"\n## LLM Prompts Found: {len(results['prompts'])}")
    print("-" * 40)
    
    prompt_files = {}
    for prompt in results['prompts']:
        file_name = prompt['file']
        if file_name not in prompt_files:
            prompt_files[file_name] = []
        prompt_files[file_name].append(prompt)
    
    for file, prompts in sorted(prompt_files.items()):
        print(f"\n### {file}")
        for prompt in prompts:
            print(f"  **Line {prompt['line']}** ({prompt['length']} chars, {prompt['type']})")
            print(f"    Preview: {prompt['preview']}")
            print()
    
    print("\n## Summary Analysis")
    print("-" * 40)
    
    # Distribution analysis
    schema_distribution = {}
    prompt_distribution = {}
    
    for schema in results['schemas']:
        file = schema['file']
        schema_distribution[file] = schema_distribution.get(file, 0) + 1
    
    for prompt in results['prompts']:
        file = prompt['file']
        prompt_distribution[file] = prompt_distribution.get(file, 0) + 1
    
    print("\n**Schema Distribution:**")
    for file, count in sorted(schema_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {file}: {count} schemas")
    
    print("\n**Prompt Distribution:**")  
    for file, count in sorted(prompt_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {file}: {count} prompts")
    
    # Identify potential consolidation opportunities
    total_schemas = len(results['schemas'])
    total_prompts = len(results['prompts'])
    files_with_schemas = len(schema_distribution)
    files_with_prompts = len(prompt_distribution)
    
    print(f"\n**Consolidation Assessment:**")
    print(f"  Total schemas: {total_schemas} across {files_with_schemas} files")
    print(f"  Total prompts: {total_prompts} across {files_with_prompts} files")
    print(f"  Average schemas per file: {total_schemas/files_with_schemas:.1f}")
    print(f"  Average prompts per file: {total_prompts/files_with_prompts:.1f}")
    
    if files_with_schemas > 3:
        print(f"  [!] SCATTERED: Schemas spread across {files_with_schemas} files - consider consolidation")
    else:
        print(f"  [OK] CONCENTRATED: Schemas reasonably centralized")
        
    if files_with_prompts > 5:
        print(f"  [!] SCATTERED: Prompts spread across {files_with_prompts} files - consider consolidation")
    else:
        print(f"  [OK] CONCENTRATED: Prompts reasonably centralized")

if __name__ == "__main__":
    print_audit_report()