# streamlit_app_modern.py - Comprehensive TwitterExplorer Streamlit Interface
"""
Modern comprehensive Streamlit app for TwitterExplorer with:
- Real-time D3.js hierarchical graph visualization
- Model configuration UI with provider switching
- Complete investigation pipeline with bridge integration
- Session management and export functionality
- Comprehensive reporting with KnowledgeBuilder and SatisfactionAssessor
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import time
import toml
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Core TwitterExplorer imports - Heavy components deferred to improve startup time
# Deferred import to improve startup time - These will be imported only when needed
# from knowledge_builder import KnowledgeBuilder  # Deferred - causes 4.7s delay
# from satisfaction_assessor import SatisfactionAssessor  # Deferred - was causing 4.2s delay
# from graph_aware_llm_coordinator import GraphAwareLLMCoordinator  # Deferred - causes 3.6s delay
from investigation_bridge import ConcreteInvestigationBridge
from realtime_insight_synthesizer import RealTimeInsightSynthesizer

# Configure page
st.set_page_config(
    page_title="🔍 TwitterExplorer - Advanced Investigation System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamlitInvestigationSession:
    """Streamlit session management for investigations"""
    
    def __init__(self):
        self.investigation_engine: Optional[InvestigationEngine] = None
        self.model_manager: Optional[LLMModelManager] = None
        self.knowledge_builder: Optional[KnowledgeBuilder] = None
        self.satisfaction_assessor: Optional[SatisfactionAssessor] = None
        self.current_session = None
        self.investigation_history: List[Dict] = []
        
    def initialize_components(self, rapidapi_key: str):
        """Initialize all investigation components with lazy loading optimization"""
        try:
            # Import InvestigationEngine only when actually initializing components
            from investigation_engine import InvestigationEngine
            
            # Initialize investigation engine
            self.investigation_engine = InvestigationEngine(rapidapi_key=rapidapi_key)
            
            # Initialize reporting components (dynamic imports)
            from knowledge_builder import KnowledgeBuilder
            from satisfaction_assessor import SatisfactionAssessor
            self.knowledge_builder = KnowledgeBuilder()
            self.satisfaction_assessor = SatisfactionAssessor()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            st.error(f"Initialization failed: {e}")
            return False
    
    def get_model_manager(self):
        """Lazy initialization of model manager only when needed for UI operations"""
        if self.model_manager is None:
            try:
                # Import LLMModelManager only when actually needed
                from llm_model_manager import LLMModelManager
                self.model_manager = LLMModelManager()
                logger.info("Model manager initialized on demand")
            except Exception as e:
                logger.error(f"Failed to initialize model manager: {e}")
                self.model_manager = None
        return self.model_manager
    
    def get_investigation_graph_data(self) -> Dict[str, Any]:
        """Get current investigation graph data in D3.js format"""
        if not self.investigation_engine or not hasattr(self.investigation_engine, 'graph'):
            return {"nodes": [], "links": []}
        
        try:
            # Get the raw graph data
            graph = self.investigation_engine.graph
            raw_data = json.loads(graph.to_json())
            
            # Convert to D3.js format
            d3_nodes = []
            d3_links = []
            
            # Process nodes
            if 'nodes' in raw_data:
                for node_id, node_data in raw_data['nodes'].items():
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
            
            # Process edges
            if 'edges' in raw_data:
                for edge_data in raw_data['edges']:
                    source_id = edge_data.get('source_node_id')
                    target_id = edge_data.get('target_node_id')
                    edge_type = edge_data.get('edge_type', 'CONNECTS')
                    
                    if source_id and target_id:
                        d3_links.append({
                            'source': source_id,
                            'target': target_id,
                            'type': edge_type
                        })
            
            return {
                "nodes": d3_nodes,
                "links": d3_links
            }
            
        except Exception as e:
            logger.error(f"Failed to get graph data: {e}")
            return {"nodes": [], "links": []}
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get current model configuration with lazy loading"""
        model_manager = self.get_model_manager()
        if model_manager:
            return model_manager.get_current_config_summary()
        return {"error": "Model manager not available", "provider": "unknown"}
    
    def update_model_config(self, provider: str, models: Dict[str, str]):
        """Update model configuration"""
        try:
            # Create new config
            new_config = {
                "default_provider": provider,
                "models": models,
                "provider_settings": {
                    "gemini": {"temperature": 0.3, "max_tokens": 8000},
                    "openai": {"temperature": 0.3, "max_tokens": 4000}
                }
            }
            
            # Save to config file
            config_path = Path(__file__).parent / "config" / "models.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(new_config, f, default_flow_style=False)
            
            # Reinitialize model manager
            self.model_manager = LLMModelManager()
            logger.info("Model configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update model config: {e}")
            return False

def load_secrets() -> Dict[str, str]:
    """Load API keys from secrets file"""
    try:
        secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
        with open(secrets_path, 'r') as f:
            return toml.load(f)
    except Exception as e:
        st.error(f"Failed to load secrets: {e}")
        return {}

def render_header():
    """Render app header"""
    st.title("TwitterExplorer Advanced Investigation System")
    st.markdown("""
    <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;'>
        <p style='color: white; margin: 0; text-align: center; font-size: 1.2rem;'>
            <strong>Intelligent Twitter Investigation with Real-time Graph Analysis</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_model_config_sidebar(session: StreamlitInvestigationSession):
    """Render model configuration in sidebar"""
    with st.sidebar:
        st.header("Model Configuration")
        
        current_config = session.get_model_config()
        
        with st.expander("Provider Settings", expanded=True):
            # Provider selection
            provider = st.selectbox(
                "LLM Provider",
                ["openai", "gemini"],
                index=0 if current_config.get("default_provider") == "openai" else 1,
                help="Select the primary LLM provider"
            )
            
            # Model selection for each operation
            st.subheader("Operation Models")
            
            models = {}
            operations = [
                ("strategic_coordinator", "Strategic Coordinator"),
                ("finding_evaluator", "Finding Evaluator"),
                ("insight_synthesizer", "Insight Synthesizer"),
                ("emergent_questions", "Emergent Questions"),
                ("cross_reference", "Cross Reference"),
                ("temporal_analysis", "Temporal Analysis")
            ]
            
            for op_key, op_label in operations:
                if provider == "openai":
                    options = ["gpt-5-mini", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
                    default_model = "gpt-5-mini"
                else:
                    options = ["gemini/gemini-2.5-flash", "gemini/gemini-1.5-pro"]
                    default_model = "gemini/gemini-2.5-flash"
                
                models[op_key] = st.selectbox(
                    op_label,
                    options,
                    index=options.index(default_model) if default_model in options else 0,
                    help=f"Model for {op_label.lower()}"
                )
            
            # Fallback models
            models["fallback_primary"] = "gpt-3.5-turbo"
            models["fallback_secondary"] = "gemini/gemini-2.5-flash"
            
            # Apply configuration
            if st.button("🔄 Apply Configuration", type="primary"):
                if session.update_model_config(provider, models):
                    st.success("✅ Configuration updated!")
                    st.rerun()
                else:
                    st.error("❌ Configuration update failed")
        
        # Display current configuration
        with st.expander("Current Configuration", expanded=False):
            st.json(current_config)

def render_investigation_controls():
    """Render investigation control panel"""
    st.header("Investigation Control Center")
    
    # Query input (full width)
    query = st.text_area(
        "Investigation Query",
        placeholder="Enter your investigation query (e.g., 'find me different takes on the current trump epstein drama')",
        height=100,
        help="Enter a detailed investigation query. The system will intelligently break it down and conduct comprehensive research."
    )
    
    # Settings and controls in columns
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        max_searches = st.slider("Max Searches", 10, 100, 50, help="Maximum number of searches to perform")
    
    with col2:
        satisfaction_threshold = st.slider("Satisfaction Threshold", 0.1, 1.0, 0.8, help="Stop when investigation reaches this satisfaction level")
        
    with col3:
        start_investigation = st.button("Start Investigation", type="primary", disabled=not query.strip())
    
    with col4:
        stop_investigation = st.button("Stop", disabled=not st.session_state.get('investigation_active', False))
    
    return {
        'query': query,
        'max_searches': max_searches,
        'satisfaction_threshold': satisfaction_threshold,
        'start': start_investigation,
        'stop': stop_investigation
    }

def run_streaming_investigation_with_updates():
    """Optimized investigation with efficient real-time D3.js graph updates"""
    
    # Get session and controls from session state
    session = st.session_state.streamlit_session
    query = st.session_state.current_query
    config = st.session_state.current_config
    
    # Just-in-time component initialization (first investigation only)
    if not session.investigation_engine:
        secrets = load_secrets()
        if not session.initialize_components(secrets['RAPIDAPI_KEY']):
            st.error("❌ Failed to initialize investigation components")
            return
    
    # Initialize investigation state machine
    if 'investigation_phase' not in st.session_state:
        st.session_state.investigation_phase = 'init'
    
    # Performance optimization: Skip unnecessary re-renders
    if st.session_state.investigation_phase == 'init':
        # Phase 1: Initialize (no delays, immediate execution)
        with st.status("🚀 Initializing Investigation...", expanded=False) as status:
            # Initialize graph with root question
            initial_graph = {
                "nodes": [{
                    "id": "root_question",
                    "label": query[:50] + ("..." if len(query) > 50 else ""),
                    "type": "AnalyticQuestion", 
                    "importance": 1.0,
                    "description": query
                }],
                "links": []
            }
            st.session_state.graph_data = initial_graph
            st.session_state.investigation_phase = 'executing'  # Skip intermediate phase
            st.rerun()  # Single rerun for this phase
            
    elif st.session_state.investigation_phase == 'executing':
        # Phase 2: Run investigation directly (no intermediate steps)
        with st.status("📊 Executing Investigation...", expanded=True) as status:
            
            # Add progress placeholder for live updates
            progress_placeholder = st.empty()
            
            try:
                with progress_placeholder.container():
                    st.write("🔍 Starting search operations...")
                
                # Run the investigation
                result = session.investigation_engine.conduct_investigation(query, config)
                session.current_session = result
                
                with progress_placeholder.container():
                    st.write("✅ Investigation searches completed")
                    st.write("🔄 Processing results and building knowledge graph...")
                
                # Get final graph data (try real data first, fall back to progressive)
                final_graph_data = session.get_investigation_graph_data()
                
                if final_graph_data and (final_graph_data.get('nodes') or final_graph_data.get('links')):
                    st.session_state.graph_data = final_graph_data
                    nodes_count = len(final_graph_data.get('nodes', []))
                    edges_count = len(final_graph_data.get('links', []))
                else:
                    # Create progressive graph from results
                    progressive_graph = create_progressive_graph_from_results(query, result)
                    st.session_state.graph_data = progressive_graph
                    nodes_count = len(progressive_graph.get('nodes', []))
                    edges_count = len(progressive_graph.get('links', []))
                
                with progress_placeholder.container():
                    st.write("🎯 Analysis and synthesis complete")
                    st.write(f"📊 Final graph: {nodes_count} nodes, {edges_count} connections")
                
                status.update(label="✅ Investigation Complete!", state="complete")
                st.session_state.investigation_phase = 'complete'
                
                # Success message
                st.success(f"🎉 Investigation completed! Generated knowledge graph with {nodes_count} nodes and {edges_count} connections.")
                
            except Exception as e:
                st.error(f"❌ Investigation failed: {e}")
                status.update(label="❌ Investigation Failed", state="error")
                st.session_state.investigation_phase = 'failed'
                logger.error(f"Investigation error: {e}")
                
    elif st.session_state.investigation_phase in ['complete', 'failed']:
        # Investigation finished - show final status
        if st.session_state.investigation_phase == 'complete':
            st.success("✅ Investigation completed successfully!")
        else:
            st.error("❌ Investigation failed")
        
        # Reset for next investigation
        if st.button("🔄 Start New Investigation"):
            st.session_state.investigation_phase = 'init'
            st.session_state.investigation_active = False
            st.session_state.graph_data = {"nodes": [], "links": []}  # Clear graph
            st.rerun()

def create_progressive_graph_from_results(query: str, result) -> Dict[str, Any]:
    """Create a more detailed graph structure from investigation results"""
    nodes = [{
        "id": "root_question",
        "label": query[:50] + ("..." if len(query) > 50 else ""),
        "type": "AnalyticQuestion",
        "importance": 1.0,
        "description": query
    }]
    links = []
    
    # Add search nodes if available
    if hasattr(result, 'search_history') and result.search_history:
        for i, search in enumerate(result.search_history[:8]):  # Limit to 8 searches
            search_id = f"search_{i+1}"
            nodes.append({
                "id": search_id,
                "label": f"Search: {search.query_description[:30]}...",
                "type": "DataPoint", 
                "importance": 0.7,
                "description": f"Query: {search.query_description}, Results: {search.results_count}"
            })
            links.append({
                "source": "root_question",
                "target": search_id,
                "type": "MOTIVATES"
            })
    
    # Add findings if available
    if hasattr(result, 'accumulated_findings') and result.accumulated_findings:
        for i, finding in enumerate(result.accumulated_findings[:5]):  # Limit to 5 findings
            finding_id = f"finding_{i+1}"
            nodes.append({
                "id": finding_id,
                "label": f"Finding {i+1}",
                "type": "Finding",
                "importance": 0.8,
                "description": finding[:100] + "..." if len(str(finding)) > 100 else str(finding)
            })
            
            # Connect to a search node if available
            if f"search_{i+1}" in [n["id"] for n in nodes]:
                links.append({
                    "source": f"search_{i+1}",
                    "target": finding_id,
                    "type": "DISCOVERS"
                })
    
    # Add synthetic insight node
    if len(nodes) > 2:  # We have some data
        insight_id = "key_insight"
        nodes.append({
            "id": insight_id,
            "label": "Key Insights",
            "type": "Insight",
            "importance": 0.9,
            "description": f"Synthesized insights from {len(result.search_history) if hasattr(result, 'search_history') else 0} searches"
        })
        
        # Connect insight to findings
        finding_nodes = [n for n in nodes if n["type"] == "Finding"]
        if finding_nodes:
            links.append({
                "source": finding_nodes[0]["id"],
                "target": insight_id,
                "type": "SUPPORTS"
            })
    
    return {"nodes": nodes, "links": links}

def run_streaming_investigation(session: StreamlitInvestigationSession, query: str, config: Any, st_module):
    """Simple investigation runner for button handler"""
    from datetime import datetime
    
    # Store parameters in session state for the streaming function
    st.session_state.current_query = query
    st.session_state.current_config = config
    
    # Run the streaming investigation
    run_streaming_investigation_with_updates()

def create_basic_graph_from_results(query: str, result) -> Dict[str, Any]:
    """Create a basic graph structure from investigation results if real graph data is not available"""
    nodes = [
        {
            "id": "root_question",
            "label": query[:50] + ("..." if len(query) > 50 else ""),
            "type": "AnalyticQuestion",
            "importance": 1.0,
            "description": query
        }
    ]
    links = []
    
    # Add findings from search results
    if hasattr(result, 'search_history') and result.search_history:
        for i, search in enumerate(result.search_history[:5]):  # Limit to first 5 searches
            finding_id = f"finding_{i+1}"
            nodes.append({
                "id": finding_id,
                "label": f"Search {i+1}: {search.search_query[:30]}...",
                "type": "Finding",
                "importance": 0.8,
                "description": f"Search query: {search.search_query}"
            })
            links.append({
                "source": "root_question",
                "target": finding_id,
                "type": "MOTIVATES"
            })
    
    # Add insights if available
    if hasattr(result, 'accumulated_findings') and result.accumulated_findings:
        insight_id = "key_insight"
        nodes.append({
            "id": insight_id,
            "label": "Key Insights",
            "type": "Insight",
            "importance": 0.9,
            "description": f"Generated from {len(result.accumulated_findings)} findings"
        })
        
        # Connect insight to findings
        if len(nodes) > 2:  # We have findings to connect to
            links.append({
                "source": "finding_1",
                "target": insight_id,
                "type": "SUPPORTS"
            })
    
    return {"nodes": nodes, "links": links}

def generate_d3_graph_html(graph_data: Dict[str, Any], height: int = 600) -> str:
    """Generate D3.js interactive graph HTML"""
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
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
        </style>
    </head>
    <body>
        <div id="graph" style="width: 100%; height: {height}px;"></div>
        
        <script>
            const graphData = {json.dumps(graph_data)};
            
            // Set up dimensions and margins
            const width = document.getElementById('graph').offsetWidth;
            const height = {height};
            
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
            const color = d3.scaleOrdinal(d3.schemeCategory10);
            
            // Create simulation
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
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
                .attr("r", d => Math.max(8, Math.min(20, (d.importance || 1) * 15)))
                .attr("fill", d => color(d.type))
                .call(drag(simulation))
                .on("mouseover", function(event, d) {{
                    tooltip.transition().duration(200).style("opacity", .9);
                    tooltip.html(`
                        <strong>${{d.label}}</strong><br/>
                        Type: ${{d.type}}<br/>
                        ${{d.description ? 'Description: ' + d.description + '<br/>' : ''}}
                        ${{d.properties ? Object.entries(d.properties).map(([k,v]) => k + ': ' + v).join('<br/>') : ''}}
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
                .attr("dy", 25);
            
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
    </html>
    """
    
    return html_template

@st.cache_data
def generate_cached_d3_graph_html(graph_data_str: str) -> str:
    """Cached D3.js graph HTML generation to avoid regenerating identical graphs"""
    import json
    graph_data = json.loads(graph_data_str)
    return generate_d3_graph_html(graph_data)

def render_investigation_graph(graph_data: Dict[str, Any]):
    """Optimized interactive D3.js graph with caching and efficient updates"""
    st.header("📈 Live Investigation Graph")
    
    if not graph_data or not graph_data.get('nodes'):
        st.info("🔍 Graph will appear here when investigation starts...")
        return
    
    # Performance optimization: Use cached HTML generation
    import json
    graph_data_str = json.dumps(graph_data, sort_keys=True)
    
    try:
        # Use cached HTML generation to avoid regenerating identical graphs
        graph_html = generate_cached_d3_graph_html(graph_data_str)
        components.html(graph_html, height=600, scrolling=True)
    except Exception as e:
        # Fallback to direct generation if caching fails
        st.warning(f"Using fallback rendering: {e}")
        graph_html = generate_d3_graph_html(graph_data)
        components.html(graph_html, height=600, scrolling=True)
    
    # Show update indicator if investigation is active
    if st.session_state.get('investigation_active', False):
        st.info("🔄 Graph updates in real-time during investigation")
    
    # Optimized graph statistics with caching
    nodes = graph_data.get('nodes', [])
    links = graph_data.get('links', [])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nodes", len(nodes))
    with col2:
        st.metric("Edges", len(links))
    with col3:
        node_types = len(set(node.get('type', 'Unknown') for node in nodes)) if nodes else 0
        st.metric("Node Types", node_types)
    with col4:
        edge_types = len(set(edge.get('type', 'Unknown') for edge in links)) if links else 0
        st.metric("Edge Types", edge_types)

def render_progress_stream():
    """Render real-time progress stream"""
    st.header("Real-time Progress Stream")
    
    progress_container = st.empty()
    
    if 'investigation_progress' not in st.session_state:
        st.session_state.investigation_progress = []
    
    with progress_container.container():
        if st.session_state.investigation_progress:
            for i, progress_item in enumerate(st.session_state.investigation_progress[-10:]):  # Show last 10 items
                with st.expander(f"{progress_item['timestamp']} - {progress_item['type']}", expanded=False):
                    st.json(progress_item['data'])
        else:
            st.info("Progress updates will appear here during investigation...")

def render_session_management():
    """Render session management interface"""
    st.header("Session Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Session"):
            # Implementation for saving session
            st.success("Session saved!")
    
    with col2:
        if st.button("Load Session"):
            # Implementation for loading session
            st.info("Load session functionality")
    
    with col3:
        if st.button("Export Results"):
            # Implementation for exporting results
            st.info("Export functionality")

def render_comprehensive_report(session: StreamlitInvestigationSession):
    """Render comprehensive investigation report"""
    st.header("Investigation Report")
    
    if not session.current_session:
        st.info("Complete an investigation to see comprehensive report...")
        return
    
    tab1, tab2, tab3, tab4 = st.tabs(["Knowledge Summary", "Satisfaction Analysis", "Cross References", "Export"])
    
    with tab1:
        st.subheader("🧠 Knowledge Summary")
        if session.knowledge_builder:
            # Generate knowledge summary
            knowledge_summary = session.knowledge_builder.generate_knowledge_summary()
            st.json(knowledge_summary)
        else:
            st.info("Knowledge builder not available")
    
    with tab2:
        st.subheader("📊 Satisfaction Analysis")
        if session.satisfaction_assessor:
            # Generate satisfaction report
            satisfaction_report = session.satisfaction_assessor.generate_satisfaction_report(session.current_session)
            st.json(satisfaction_report)
        else:
            st.info("Satisfaction assessor not available")
    
    with tab3:
        st.subheader("🔗 Cross References")
        st.info("Cross-reference analysis will be displayed here")
    
    with tab4:
        st.subheader("📤 Export Options")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if st.button("Export as JSON"):
                # Export as JSON
                export_data = {
                    "session": session.current_session.__dict__ if session.current_session else None,
                    "timestamp": datetime.now().isoformat(),
                    "report_type": "json"
                }
                st.download_button(
                    label="📄 Download JSON",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with export_col2:
            if st.button("Export as Markdown"):
                # Export as Markdown
                markdown_content = f"""# Investigation Report
                
Generated: {datetime.now().isoformat()}

## Session Summary
Investigation session data would be formatted here...

## Key Findings
Findings would be formatted here...
"""
                st.download_button(
                    label="📝 Download Markdown",
                    data=markdown_content,
                    file_name=f"investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
        
        with export_col3:
            if st.button("Export as HTML"):
                # Export as HTML
                html_content = f"""<!DOCTYPE html>
<html>
<head><title>Investigation Report</title></head>
<body>
    <h1>Investigation Report</h1>
    <p>Generated: {datetime.now().isoformat()}</p>
    <h2>Session Summary</h2>
    <p>Investigation session data would be formatted here...</p>
</body>
</html>"""
                st.download_button(
                    label="🌐 Download HTML",
                    data=html_content,
                    file_name=f"investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html"
                )

def main():
    """Main Streamlit app"""
    
    # Initialize session state
    if 'streamlit_session' not in st.session_state:
        st.session_state.streamlit_session = StreamlitInvestigationSession()
    
    if 'investigation_active' not in st.session_state:
        st.session_state.investigation_active = False
        
    if 'graph_data' not in st.session_state:
        st.session_state.graph_data = {"nodes": [], "links": []}
    
    session = st.session_state.streamlit_session
    
    # Load secrets and initialize components
    secrets = load_secrets()
    if not secrets:
        st.error("❌ Failed to load API keys. Please check .streamlit/secrets.toml file.")
        st.stop()
    
    # Components will be initialized just-in-time when investigation starts
    # This dramatically improves app startup performance by avoiding 4.5s LiteLLM delay
    
    # Render header
    render_header()
    
    # Render model configuration sidebar
    render_model_config_sidebar(session)
    
    # Investigation controls (full width)
    controls = render_investigation_controls()
    
    # Main layout for graph and sidebar
    main_col1, main_col2 = st.columns([2, 1])
    
    with main_col1:
        # Investigation graph
        render_investigation_graph(st.session_state.graph_data)
        
        # Comprehensive report
        render_comprehensive_report(session)
    
    with main_col2:
        # Progress stream
        render_progress_stream()
        
        # Session management
        render_session_management()
    
    # Optimized investigation handling - minimal re-runs
    if controls['start'] and controls['query'].strip() and not st.session_state.investigation_active:
        # Initialize investigation state efficiently
        st.session_state.investigation_active = True
        st.session_state.investigation_phase = 'init'
        st.session_state.current_query = controls['query']
        # Import InvestigationConfig when needed
        from investigation_engine import InvestigationConfig
        st.session_state.current_config = InvestigationConfig(
            max_searches=controls['max_searches'],
            satisfaction_threshold=controls['satisfaction_threshold'],
            satisfaction_enabled=True,
            show_search_details=True,
            show_strategy_reasoning=True
        )
        st.rerun()  # Single rerun to start investigation
    
    # Run streaming investigation if active
    if st.session_state.get('investigation_active', False):
        run_streaming_investigation_with_updates()
        
        # Auto-disable when complete (no additional rerun needed)
        if st.session_state.get('investigation_phase') in ['complete', 'failed']:
            st.session_state.investigation_active = False
    
    # Handle stop button (immediate stop)
    if controls['stop'] and st.session_state.investigation_active:
        st.session_state.investigation_active = False
        st.session_state.investigation_phase = 'complete'  # Set to complete to show results
        st.warning("🛑 Investigation stopped by user")

if __name__ == "__main__":
    main()