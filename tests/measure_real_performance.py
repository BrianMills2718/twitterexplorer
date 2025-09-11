#!/usr/bin/env python3
"""
Real-world performance measurement for Streamlit app
Tests actual end-to-end user experience scenarios
"""

import time
import subprocess
import requests
import json
from urllib.parse import urljoin

def measure_app_startup():
    """Measure how long it takes to start the Streamlit app"""
    print("1. Measuring App Startup Performance...")
    
    # Kill any existing processes and start fresh
    try:
        subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], 
                      capture_output=True, text=True, timeout=10)
        time.sleep(2)  # Allow processes to fully terminate
    except:
        pass  # Ignore if no processes to kill
    
    start_time = time.time()
    
    # Start Streamlit on a new port
    process = subprocess.Popen([
        "python", "-m", "streamlit", "run", "streamlit_app_modern.py", 
        "--server.headless", "true", "--server.port", "8504"
    ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for app to be ready
    app_ready = False
    timeout = 30  # 30 second timeout
    check_start = time.time()
    
    while not app_ready and (time.time() - check_start) < timeout:
        try:
            response = requests.get("http://localhost:8504/", timeout=1)
            if response.status_code == 200:
                app_ready = True
        except:
            time.sleep(0.5)
    
    startup_time = time.time() - start_time
    
    if app_ready:
        print(f"   ✅ App startup time: {startup_time:.2f} seconds")
        return startup_time, process
    else:
        print(f"   ❌ App failed to start within {timeout} seconds")
        process.terminate()
        return None, None

def measure_page_load_time(base_url):
    """Measure how long it takes to load the main page"""
    print("2. Measuring Page Load Performance...")
    
    load_times = []
    
    for i in range(3):  # Test 3 times for average
        start_time = time.time()
        try:
            response = requests.get(base_url, timeout=10)
            load_time = time.time() - start_time
            
            if response.status_code == 200:
                load_times.append(load_time)
                print(f"   Load {i+1}: {load_time:.3f}s")
            else:
                print(f"   Load {i+1}: Failed (HTTP {response.status_code})")
        except Exception as e:
            print(f"   Load {i+1}: Failed ({e})")
        
        time.sleep(1)  # Brief pause between tests
    
    if load_times:
        avg_load = sum(load_times) / len(load_times)
        print(f"   ✅ Average page load: {avg_load:.3f}s")
        return avg_load
    else:
        print("   ❌ All page loads failed")
        return None

def measure_component_initialization():
    """Test how long component initialization takes in isolation"""
    print("3. Measuring Component Initialization...")
    
    test_script = """
import time
import sys
sys.path.append('.')

start = time.time()
from streamlit_app_modern import StreamlitInvestigationSession
session = StreamlitInvestigationSession()
init_time = time.time() - start

start = time.time()
session.initialize_components("dummy_key")
component_time = time.time() - start

print(f"Session: {init_time:.4f}s")
print(f"Components: {component_time:.4f}s")
print(f"Total: {init_time + component_time:.4f}s")
"""
    
    try:
        result = subprocess.run(["python", "-c", test_script], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                print(f"   {line}")
            
            # Extract total time
            for line in lines:
                if line.startswith("Total:"):
                    total_time = float(line.split()[1].rstrip('s'))
                    return total_time
        else:
            print(f"   ❌ Component test failed: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ Component test error: {e}")
    
    return None

def measure_d3_generation_real_world():
    """Measure D3.js generation with realistic graphs"""
    print("4. Measuring D3.js Generation (Real-world scenarios)...")
    
    test_script = """
import time
import json
import sys
sys.path.append('.')

from streamlit_app_modern import generate_d3_graph_html

# Test with realistic investigation graph sizes
test_cases = [
    {"name": "Small Investigation", "nodes": 8, "links": 7},
    {"name": "Medium Investigation", "nodes": 15, "links": 18}, 
    {"name": "Large Investigation", "nodes": 25, "links": 30},
    {"name": "Complex Investigation", "nodes": 40, "links": 50}
]

for case in test_cases:
    # Generate realistic graph structure
    nodes = []
    for i in range(case["nodes"]):
        if i == 0:
            node_type = "AnalyticQuestion"
        elif i < 5:
            node_type = "DataPoint" 
        elif i < 10:
            node_type = "Finding"
        elif i < 15:
            node_type = "Insight"
        else:
            node_type = "EmergentQuestion"
            
        nodes.append({
            "id": f"node_{i}",
            "label": f"Node {i} - {node_type}",
            "type": node_type,
            "importance": 0.5 + (i % 5) * 0.1,
            "description": f"Description for {node_type} node {i} with some meaningful content"
        })
    
    links = []
    for i in range(case["links"]):
        source_idx = i % len(nodes)
        target_idx = (i + 1) % len(nodes) 
        link_types = ["MOTIVATES", "DISCOVERS", "SUPPORTS", "SPAWNS", "CONTRADICTS"]
        
        links.append({
            "source": nodes[source_idx]["id"],
            "target": nodes[target_idx]["id"], 
            "type": link_types[i % len(link_types)]
        })
    
    graph_data = {"nodes": nodes, "links": links}
    
    # Measure generation time
    start = time.time()
    html = generate_d3_graph_html(graph_data)
    gen_time = time.time() - start
    
    print(f"{case['name']}: {gen_time:.4f}s ({len(html)} chars)")
"""
    
    try:
        result = subprocess.run(["python", "-c", test_script], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                print(f"   {line}")
            return True
        else:
            print(f"   ❌ D3.js test failed: {result.stderr}")
            
    except Exception as e:
        print(f"   ❌ D3.js test error: {e}")
    
    return False

def measure_memory_usage():
    """Check memory usage of the running app"""
    print("5. Measuring Memory Usage...")
    
    try:
        # Use psutil if available, otherwise skip
        import psutil
        
        # Find Python processes
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and 'streamlit' in ' '.join(cmdline):
                        python_processes.append({
                            'pid': proc.info['pid'],
                            'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                            'cmdline': ' '.join(cmdline)
                        })
            except:
                continue
        
        if python_processes:
            total_memory = sum(p['memory_mb'] for p in python_processes)
            print(f"   Found {len(python_processes)} Streamlit process(es)")
            for proc in python_processes:
                print(f"   PID {proc['pid']}: {proc['memory_mb']:.1f} MB")
            print(f"   Total memory usage: {total_memory:.1f} MB")
            return total_memory
        else:
            print("   No Streamlit processes found")
            
    except ImportError:
        print("   psutil not available, skipping memory measurement")
    except Exception as e:
        print(f"   Memory measurement error: {e}")
    
    return None

def main():
    """Run comprehensive performance measurement"""
    print("Real-World Streamlit Performance Measurement")
    print("=" * 50)
    
    results = {}
    
    # Test 1: App startup
    startup_time, app_process = measure_app_startup()
    if startup_time:
        results['startup_time'] = startup_time
        
        # Test 2: Page loading (only if app started successfully)
        base_url = "http://localhost:8504/"
        page_load_time = measure_page_load_time(base_url)
        if page_load_time:
            results['page_load_time'] = page_load_time
        
        # Cleanup
        app_process.terminate()
        time.sleep(2)
    
    # Test 3: Component initialization (independent test)
    component_time = measure_component_initialization()
    if component_time:
        results['component_init_time'] = component_time
    
    # Test 4: D3.js generation performance
    d3_success = measure_d3_generation_real_world()
    if d3_success:
        results['d3_generation'] = True
    
    # Test 5: Memory usage (of existing processes)
    memory_usage = measure_memory_usage()
    if memory_usage:
        results['memory_usage_mb'] = memory_usage
    
    # Summary
    print("\n" + "=" * 50)
    print("PERFORMANCE MEASUREMENT RESULTS")
    print("=" * 50)
    
    if 'startup_time' in results:
        print(f"App Startup Time: {results['startup_time']:.2f}s")
        
        if results['startup_time'] > 10:
            print("  ⚠️  SLOW - App takes >10s to start")
        elif results['startup_time'] > 5:
            print("  ⚠️  MODERATE - App takes >5s to start") 
        else:
            print("  ✅ GOOD - App starts quickly")
    
    if 'page_load_time' in results:
        print(f"Page Load Time: {results['page_load_time']:.3f}s")
        
        if results['page_load_time'] > 2:
            print("  ⚠️  SLOW - Page takes >2s to load")
        elif results['page_load_time'] > 1:
            print("  ⚠️  MODERATE - Page takes >1s to load")
        else:
            print("  ✅ GOOD - Page loads quickly")
    
    if 'component_init_time' in results:
        print(f"Component Init Time: {results['component_init_time']:.3f}s")
        
        if results['component_init_time'] > 1:
            print("  ⚠️  SLOW - Components take >1s to initialize")
        else:
            print("  ✅ GOOD - Components initialize quickly")
    
    if 'memory_usage_mb' in results:
        print(f"Memory Usage: {results['memory_usage_mb']:.1f} MB")
        
        if results['memory_usage_mb'] > 500:
            print("  ⚠️  HIGH - Using >500MB memory")
        elif results['memory_usage_mb'] > 200:
            print("  ⚠️  MODERATE - Using >200MB memory")
        else:
            print("  ✅ GOOD - Reasonable memory usage")
    
    print(f"\nD3.js Generation: {'✅ Working' if results.get('d3_generation') else '❌ Failed'}")
    
    # Overall assessment
    issues = []
    if results.get('startup_time', 0) > 5:
        issues.append("Slow app startup")
    if results.get('page_load_time', 0) > 1:
        issues.append("Slow page loading")
    if results.get('component_init_time', 0) > 1:
        issues.append("Slow component initialization")
    if results.get('memory_usage_mb', 0) > 300:
        issues.append("High memory usage")
    
    print("\n" + "-" * 50)
    if issues:
        print("⚠️  PERFORMANCE ISSUES DETECTED:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nRecommendations:")
        print("   - Kill redundant processes")
        print("   - Optimize component loading")
        print("   - Review memory usage patterns")
    else:
        print("✅ PERFORMANCE LOOKS GOOD")
        print("   - All metrics within acceptable ranges")
    
    return len(issues) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)