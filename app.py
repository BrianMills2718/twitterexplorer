# app_new.py - Enhanced Twitter Explorer with Investigation Engine
import streamlit as st
import json
import time
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from datetime import datetime

# Import existing modules
import twitter_config as config
import state_manager
import llm_handler
import api_client
import graph_manager

# Import new investigation system
from investigation_engine import InvestigationEngine, InvestigationConfig, InvestigationSession
from adaptive_planner import AdaptivePlanner
from satisfaction_assessor import SatisfactionAssessor
from twitterexplorer.knowledge_builder import KnowledgeBuilder

# --- Page Config ---
st.set_page_config(page_title="🔍 Advanced Twitter Investigation Engine", layout="wide")

# --- Header ---
st.title("🔍 Advanced Twitter Investigation Engine")
st.caption("Intelligent, iterative investigation system for Twitter research and analysis")

# --- Configuration Sidebar ---
with st.sidebar:
    st.header("🛠️ Investigation Settings")
    
    # Investigation configuration
    with st.expander("Investigation Configuration", expanded=False):
        max_batches = st.slider("Maximum Batches", min_value=3, max_value=25, value=12, step=1,
                               help="Maximum number of search batches before stopping (each batch = ~4 searches)")
        max_searches = max_batches * 4  # Convert batches to searches for internal compatibility
        
        satisfaction_enabled = st.checkbox("Enable Satisfaction Stopping", value=True, 
                                          help="Stop when investigation satisfaction threshold is reached")
        
        satisfaction_threshold = st.slider("Satisfaction Threshold", min_value=0.1, max_value=1.0, 
                                          value=0.8, step=0.05,
                                          help="Stop investigation when this satisfaction level is reached")
        
        min_searches_before_satisfaction = st.slider("Min Searches Before Satisfaction Check", 
                                                     min_value=5, max_value=50, value=10, step=5,
                                                     help="Minimum searches before checking satisfaction")
    
    # Display options  
    with st.expander("Display Options", expanded=True):
        show_search_details = st.checkbox("Show Search Details", value=True,
                                         help="Display detailed search attempt information")
        
        show_strategy_reasoning = st.checkbox("Show Strategy Reasoning", value=True,
                                             help="Display AI reasoning for search strategies")
        
        show_effectiveness_scores = st.checkbox("Show Effectiveness Scores", value=True,
                                               help="Display search effectiveness ratings")
    
    # Quick presets
    st.subheader("⚡ Quick Presets")
    if st.button("🔍 Quick Investigation (6 batches)"):
        st.session_state.config_preset = 'quick'
    if st.button("🔬 Deep Investigation (12 batches)"):
        st.session_state.config_preset = 'deep'
    if st.button("🚀 Exhaustive Investigation (20 batches)"):
        st.session_state.config_preset = 'exhaustive'
    
    # Logging Analysis
    st.subheader("📊 Log Analysis")
    with st.expander("View Investigation Logs", expanded=False):
        st.caption("Analyze your investigation patterns and performance")
        
        if st.button("📈 Show Session Performance"):
            try:
                from log_analyzer import create_analysis_report
                analysis = create_analysis_report()
                st.text_area("Performance Analysis", analysis, height=300)
            except Exception as e:
                st.error(f"Failed to generate analysis: {e}")
        
        if st.button("🔍 Show Search Effectiveness"):
            try:
                from log_analyzer import LogAnalyzer
                analyzer = LogAnalyzer()
                effectiveness = analyzer.analyze_search_effectiveness()
                st.json(effectiveness)
            except Exception as e:
                st.error(f"Failed to analyze search effectiveness: {e}")
        
        if st.button("🤖 Show LLM Performance"):
            try:
                from log_analyzer import LogAnalyzer
                analyzer = LogAnalyzer()
                llm_perf = analyzer.analyze_llm_performance()
                st.json(llm_perf)
            except Exception as e:
                st.error(f"Failed to analyze LLM performance: {e}")
        
        # Session-specific analysis
        if st.session_state.get('investigation_session'):
            session = st.session_state['investigation_session']
            if hasattr(session, 'start_time') and st.button("📋 Current Session Report"):
                try:
                    from log_analyzer import LogAnalyzer
                    analyzer = LogAnalyzer()
                    # Try to find session by looking for recent sessions
                    recent_sessions = analyzer._load_sessions()
                    if recent_sessions:
                        # Get the most recent session (likely the current one)
                        latest_session = max(recent_sessions, key=lambda x: x.get('session_metadata', {}).get('start_time', ''))
                        session_id = latest_session.get('session_metadata', {}).get('session_id')
                        if session_id:
                            report = analyzer.generate_investigation_report(session_id)
                            st.json(report)
                        else:
                            st.info("Current session not yet logged completely")
                    else:
                        st.info("No completed sessions found in logs")
                except Exception as e:
                    st.error(f"Failed to generate session report: {e}")
    
    # Apply presets
    if 'config_preset' in st.session_state:
        if st.session_state.config_preset == 'quick':
            max_batches = 6  # 24 searches total
            max_searches = 24
            satisfaction_threshold = 0.7
        elif st.session_state.config_preset == 'deep':
            max_batches = 12  # 48 searches total  
            max_searches = 48
            satisfaction_threshold = 0.8
        elif st.session_state.config_preset == 'exhaustive':
            max_batches = 20  # 80 searches total
            max_searches = 80
            satisfaction_threshold = 0.9
        del st.session_state.config_preset

# --- Create Investigation Config ---
investigation_config = InvestigationConfig(
    max_searches=max_searches,
    satisfaction_enabled=satisfaction_enabled,
    satisfaction_threshold=satisfaction_threshold,
    min_searches_before_satisfaction=min_searches_before_satisfaction,
    show_search_details=show_search_details,
    show_strategy_reasoning=show_strategy_reasoning,
    show_effectiveness_scores=show_effectiveness_scores
)

# --- Example Queries ---
with st.expander("📋 Example Investigation Queries", expanded=False):
    st.markdown("""
    **Debunking & Fact-Checking Investigations:**
    - "Find information that debunks UFO whistleblower Jonathan Weygandt"
    - "Investigate claims about Bob Lazar and find skeptical analysis"
    - "Research the credibility of David Grusch UFO testimony"
    - "Find fact-checking information about recent UFO disclosure claims"
    
    **General Investigation Examples:**
    - "Investigate controversies around Elon Musk's Twitter acquisition"
    - "Find critical analysis of cryptocurrency influencer claims"
    - "Research skeptical views on popular health trends"
    - "Investigate fact-checks about political figure statements"
    
    **The system will:**
    - Plan multiple search strategies intelligently
    - Adapt based on what it finds (or doesn't find)
    - Show you exactly what it's searching for
    - Build knowledge incrementally across searches
    - Stop when satisfied or at the search limit
    """)

# --- Initialization ---
# Load static data
try:
    state_manager.load_initial_data()
    if not state_manager.endpoints_data or not state_manager.ontology_data_str:
         st.error("Failed to load endpoint or ontology data. Check file paths and content.")
         st.stop()
except Exception as e:
    st.error(f"Error during initial data load: {e}")
    st.stop()

# Initialize API keys as None - will be loaded in main()
OPENAI_API_KEY = None
RAPIDAPI_KEY = None

def load_api_keys():
    """Load API keys from secrets"""
    global OPENAI_API_KEY, RAPIDAPI_KEY
    try:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
        RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
    except KeyError as e:
        st.error(f"Missing API Key in Streamlit Secrets (secrets.toml): {e}")
        st.info("Please create a `.streamlit/secrets.toml` file with your OPENAI_API_KEY and RAPIDAPI_KEY.")
        st.stop()

# Only run this when app is actually running, not during import
if __name__ == "__main__" or "streamlit" in sys.modules:
    # Load API keys before initializing services
    if 'api_keys_loaded' not in st.session_state:
        load_api_keys()
        st.session_state['api_keys_loaded'] = True

# Initialize LLM Handler
try:
    llm_handler.set_llm_model(OPENAI_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize the LLM handler: {e}")
    st.stop()

# Initialize Logging System
try:
    from logging_system import investigation_logger
    st.success("✅ Logging system initialized successfully")
except Exception as e:
    st.warning(f"⚠️ Logging system initialization failed: {e}")
    st.info("Investigation will continue without comprehensive logging")

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "llm_history" not in st.session_state:
    st.session_state.llm_history = []
if 'graph' not in st.session_state:
    st.session_state['graph'] = nx.MultiDiGraph()
if 'investigation_session' not in st.session_state:
    st.session_state['investigation_session'] = None
if 'investigation_active' not in st.session_state:
    st.session_state['investigation_active'] = False

# --- Investigation Status Display ---
if st.session_state.get('investigation_session'):
    session = st.session_state['investigation_session']
    
    # Create metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        current_batches = (session.search_count + 3) // 4
        max_batches_display = (session.config.max_searches + 3) // 4
        st.metric("Batches", f"{current_batches}/{max_batches_display}")
    with col2:
        st.metric("Results Found", session.total_results_found)
    with col3:
        satisfaction = session.satisfaction_metrics.overall_satisfaction()
        st.metric("Satisfaction", f"{satisfaction:.1%}")
    with col4:
        st.metric("Rounds", session.round_count)
    with col5:
        elapsed = (datetime.now() - session.start_time).seconds / 60
        st.metric("Time (min)", f"{elapsed:.1f}")
    
    # Progress bar - show both batches and searches
    progress = session.search_count / session.config.max_searches
    current_batches = (session.search_count + 3) // 4  # Round up to nearest batch
    max_batches_display = (session.config.max_searches + 3) // 4  # Round up to nearest batch
    st.progress(progress, text=f"Progress: {current_batches}/{max_batches_display} batches ({session.search_count}/{session.config.max_searches} searches)")
    
    # Status indicator
    if session.is_active:
        st.info("🔍 Investigation in progress...")
    else:
        if "satisfied" in session.completion_reason.lower():
            st.success(f"✅ Investigation completed: {session.completion_reason}")
        else:
            st.warning(f"⚠️ Investigation stopped: {session.completion_reason}")

# --- Control Buttons ---
control_col1, control_col2, control_col3 = st.columns(3)

with control_col1:
    if st.button("🗑️ Clear All History & Data"):
        st.session_state.messages = []
        st.session_state.llm_history = []
        st.session_state.graph = nx.MultiDiGraph()
        st.session_state.investigation_session = None
        st.session_state.investigation_active = False
        st.success("All data cleared!")
        st.rerun()

with control_col2:
    if st.session_state.get('investigation_active'):
        if st.button("⏸️ Stop Investigation"):
            if st.session_state.get('investigation_session'):
                st.session_state['investigation_session'].is_active = False
                st.session_state['investigation_session'].completion_reason = "Manually stopped by user"
            st.session_state['investigation_active'] = False
            st.success("Investigation stopped!")
            st.rerun()

with control_col3:
    if st.session_state.get('investigation_session') and not st.session_state.get('investigation_active'):
        if st.button("📊 Generate Final Report"):
            # Generate comprehensive final report
            session = st.session_state['investigation_session']
            
            # Build knowledge
            knowledge_builder = KnowledgeBuilder()
            knowledge = knowledge_builder.build_knowledge_from_session(session)
            
            # Generate satisfaction report
            assessor = SatisfactionAssessor()
            satisfaction_report = assessor.generate_satisfaction_report(session)
            
            # Generate knowledge summary
            knowledge_summary = knowledge_builder.generate_knowledge_summary()
            
            # Display final report
            st.markdown("## 📊 FINAL INVESTIGATION REPORT")
            st.markdown("---")
            
            with st.expander("🎯 Satisfaction Analysis", expanded=True):
                st.markdown(satisfaction_report)
            
            with st.expander("🧠 Knowledge Summary", expanded=True):
                st.markdown(knowledge_summary)
            
            with st.expander("💡 Recommendations", expanded=False):
                recommendations = knowledge_builder.get_investigation_recommendations(session)
                if recommendations:
                    for rec in recommendations:
                        st.markdown(f"• {rec}")
                else:
                    st.markdown("No specific recommendations generated.")

# --- Main Chat Interface ---
chat_container = st.container()

with chat_container:
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- Handle User Input & Investigation ---
if prompt := st.chat_input("Enter your investigation query..."):
    # Add user message to display state immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with chat_container:
         with st.chat_message("user"):
            st.markdown(prompt)

    # Start investigation
    with chat_container:
        with st.chat_message("assistant"):
            try:
                # Initialize investigation engine
                investigation_engine = InvestigationEngine(RAPIDAPI_KEY)
                
                # === NEW: Set up progress container for real-time updates ===
                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    progress_container = st.container()
                investigation_engine.set_progress_container(progress_container)
                
                # Display investigation start
                st.markdown(f"🚀 **Starting Investigation:** {prompt}")
                max_batches_config = (investigation_config.max_searches + 3) // 4
                st.markdown(f"**Configuration:** {max_batches_config} max batches ({investigation_config.max_searches} searches), "
                           f"{investigation_config.satisfaction_threshold:.0%} satisfaction threshold")
                st.markdown("---")
                
                # Set investigation as active
                st.session_state['investigation_active'] = True
                
                # Conduct investigation
                session = investigation_engine.conduct_investigation(prompt, investigation_config)
                
                # Store session
                st.session_state['investigation_session'] = session
                st.session_state['investigation_active'] = False
                
                # Display final summary if available
                if hasattr(session, 'final_summary') and session.final_summary:
                    st.markdown("---")
                    st.markdown("## 📊 Investigation Results")
                    st.markdown(session.final_summary)
                    
                    # Add download button for summary
                    st.download_button(
                        label="📥 Download Summary",
                        data=session.final_summary,
                        file_name=f"investigation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                
                # Generate final summary using LLM
                if session.search_history:
                    # Prepare data for LLM summarization
                    summary_data = []
                    for search in session.search_history:
                        if search.results_count > 0:
                            summary_data.append({
                                'endpoint': search.endpoint,
                                'query': search.params.get('query', ''),
                                'results_count': search.results_count,
                                'effectiveness': search.effectiveness_score,
                                'step_executed': search.search_id,
                                'data': f"Found {search.results_count} results for search: {search.params.get('query', '')}"
                            })
                    
                    # Get LLM summary
                    if summary_data:
                        final_summary = llm_handler.get_llm_summary(prompt, summary_data)
                    else:
                        final_summary = "Investigation completed but found no relevant results to summarize."
                    
                    # Build knowledge for additional insights
                    knowledge_builder = KnowledgeBuilder()
                    knowledge = knowledge_builder.build_knowledge_from_session(session)
                    
                    # Enhance summary with knowledge insights
                    if knowledge.key_insights:
                        final_summary += "\n\n**Additional Insights:**\n"
                        for insight in knowledge.key_insights:
                            final_summary += f"• {insight}\n"
                    
                    # Add satisfaction analysis
                    satisfaction = session.satisfaction_metrics.overall_satisfaction()
                    final_summary += f"\n**Investigation Satisfaction:** {satisfaction:.1%}"
                    
                    if satisfaction < 0.5:
                        final_summary += " - Consider continuing with different approaches or platforms."
                    elif satisfaction < 0.8:
                        final_summary += " - Good progress made, some gaps remain."
                    else:
                        final_summary += " - Investigation appears comprehensive."
                
                else:
                    final_summary = "Investigation completed but no searches were successfully executed."
                
                # Display final summary
                st.markdown("## 📋 Investigation Summary")
                st.markdown(final_summary)
                
                # Add to chat history
                st.session_state.messages.append({"role": "assistant", "content": final_summary})
                st.session_state.llm_history.append({
                    "user_query": prompt,
                    "investigation_session": session,
                    "summary": final_summary
                })
                
                # Update graph with all results
                if session.search_history:
                    current_graph = st.session_state['graph']
                    for search in session.search_history:
                        if search.results_count > 0:
                            # Create mock result for graph update
                            mock_result = {
                                'endpoint': search.endpoint,
                                'data': {'timeline': [{'tweet_id': f'search_{search.search_id}'}] * min(search.results_count, 5)},
                                'step_executed': search.search_id
                            }
                            try:
                                graph_manager.parse_and_process_api_result(current_graph, mock_result)
                            except Exception as graph_e:
                                st.warning(f"Graph update failed for search {search.search_id}: {graph_e}")
                    
                    st.session_state['graph'] = current_graph

            except Exception as e:
                st.error(f"Investigation failed: {e}")
                st.session_state['investigation_active'] = False
                
                # Add error to chat
                error_message = f"Investigation encountered an error: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# --- Display Graph ---
graph_container = st.container()

with graph_container:
    st.divider()
    st.subheader("📊 Investigation Network Graph")
    
    graph = st.session_state.get('graph', nx.MultiDiGraph())
    
    if not graph or graph.number_of_nodes() == 0:
        st.caption("Graph is empty. Start an investigation to populate the network visualization!")
    else:
        # Display graph info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nodes", graph.number_of_nodes())
        with col2:
            st.metric("Edges", graph.number_of_edges())
        with col3:
            node_types = {}
            for _, attrs in graph.nodes(data=True):
                ntype = attrs.get('node_type', 'Unknown')
                node_types[ntype] = node_types.get(ntype, 0) + 1
            st.metric("Node Types", len(node_types))
        
        # Generate and display graph visualization
        try:
            net = Network(height='600px', width='100%', directed=True, notebook=False)
            
            net.barnes_hut(
                gravity=-10000,
                central_gravity=0.3,
                spring_length=150,
                spring_strength=0.05,
                damping=0.09,
                overlap=0.5
            )
            
            # Add nodes and edges (simplified version)
            for node_id, attrs in graph.nodes(data=True):
                node_type = attrs.get('node_type', 'Investigation')
                net.add_node(str(node_id), 
                           label=f"Search {node_id}" if str(node_id).startswith('search_') else str(node_id),
                           color='#97C2FC' if node_type == 'Investigation' else '#A5F5A5',
                           size=20,
                           title=f"Type: {node_type}")
            
            for u, v, attrs in graph.edges(data=True):
                net.add_edge(str(u), str(v), color='#DDDDDD')
            
            # Save and display
            net.save_graph("investigation_network.html")
            with open("investigation_network.html", 'r', encoding='utf-8') as f:
                html_data = f.read()
            
            components.html(html_data, height=610, scrolling=False)
            
        except Exception as e:
            st.error(f"Failed to generate graph visualization: {e}")

# --- Footer ---
st.markdown("---")
st.markdown("**🔍 Advanced Twitter Investigation Engine** - Powered by AI-driven iterative research")