# app.py
import streamlit as st
import json
import time
import networkx as nx
# from streamlit_agraph import agraph, Node, Edge, Config # REMOVE or comment out agraph imports
from pyvis.network import Network # <-- ADD Pyvis import
import streamlit.components.v1 as components # <-- ADD components import

# Import your existing modules
import config
import state_manager
import llm_handler
import api_client
import graph_manager # Import the new module

# --- Page Config ---
st.set_page_config(page_title="LLM Twitter Explorer", layout="wide")
st.title("🕵️ LLM Twitter Explorer")
st.caption("Ask questions about Twitter users, tweets, etc. Graph will build below.")

# --- Example Queries ---
with st.expander("📋 Example Queries (Click to expand)", expanded=False):
    st.markdown("""
    **Basic Info:**
    - screenname.php: "Tell me about the user @github."
    - screenname.php: "What is the location listed for @Google?"
    - tweet.php: "Show details for tweet 1905679299966914783." (Use an ID from the timeline response)
    - tweet.php: "How many retweets does tweet 1905677405760462873 have?"
    
    **Lists & Timelines:**
    - timeline.php: "What are the 5 most recent tweets from @YouTube?" (Test implicit page limit)
    - timeline.php (Pagination): "Show me 2 pages of the timeline for @reactjs."
    - usermedia.php: "Show recent photos or videos posted by @NatGeo."
    - replies.php: "What are some replies made by @nodejs?" (Test this endpoint as documented)
    - latest_replies.php: "Get replies to tweet 1905676627373113669." (Use a known tweet ID)
    - tweet_thread.php: "Show the conversation thread starting with tweet 1905679299966914783." (Use ID of a likely thread start)
    
    **Followers/Following:**
    - followers.php: "List some followers of @Docker."
    - followers.php (Pagination): "Get 2 pages of followers for @pythonlang."
    - following.php: "Who is @BillGates following?"
    - checkfollow.php: "Does @GoogleAI follow @MetaAI?"
    
    **Retweets & Interactions:**
    - retweets.php: "Who are some users that retweeted tweet 1905611611580084360?" (Use a known tweet ID)
    - checkretweet.php: "Did user @elonmusk retweet tweet 1905611611580084360?"
    
    **Search & Trends:**
    - search.php: "Search for recent tweets about 'artificial intelligence'."
    - search.php (Type): "Find 'People' accounts related to 'web development'."
    - search.php (Type): "Show the 'Latest' tweets containing #opensource."
    - trends.php: "What is trending in Canada?"
    
    **Lists (Requires Valid List IDs):**
    To find List IDS use twitter search in browser then click the Lists tab after searching a topic, then click on the list and the id is at the end of the url like this https://x.com/i/lists/1558590202385518594
    
    - listtimeline.php: "Show tweets from Twitter list ID 1558590202385518594."
    - list_members.php: "Who are the members of list 1558590202385518594?"
    - list_followers.php: "Get followers of list 1558590202385518594."
    
    **Communities & Spaces (Requires Valid IDs):**
    - community_timeline.php: "Show posts from community 1683580737021177863." To find community id go to the left hand sidebar in your twitter browser, search your topic, then click the community then the id is at the end of the url such as https://x.com/i/communities/1816527453755703497
    
    - spaces.php: "Get info about Twitter Space 1yoKMoOZwewJQ." How to find a Space's URL: Tap the share icon then tap Copy Link. The URL should now be copied to your clipboard.
    
    **Bulk User Info:**
    - screennames.php: "Get profile details for user IDs 44196397, 1367531, 875856268056969216." (Use known IDs)
    
    **Multi-Step / Complex:**
    - "Find recent followers of @github and tell me their bios." (Combines followers.php → screennames.php)
    - "Search for tweets about 'rust programming language', then show details of the first tweet found." (search.php → tweet.php)
    - "Get the timeline for @MetaAI, find a tweet that quotes another tweet, and show the text of the quoted tweet." (timeline.php → requires logic to find quoted object)
    - "Who follows @elonmusk? From that list, find someone who is blue verified and show their bio." (followers.php → filter → screennames.php - may require multiple follower pages)
    """)

# --- Initialization ---
# Load static data (ontology, endpoints)
try:
    state_manager.load_initial_data()
    if not state_manager.endpoints_data or not state_manager.ontology_data_str:
         st.error("Failed to load endpoint or ontology data. Check file paths and content.")
         st.stop()
except Exception as e:
    st.error(f"Error during initial data load: {e}")
    st.stop()

# Load API keys from secrets
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    RAPIDAPI_KEY = st.secrets["RAPIDAPI_KEY"]
except KeyError as e:
    st.error(f"Missing API Key in Streamlit Secrets (secrets.toml): {e}")
    st.info("Please create a `.streamlit/secrets.toml` file with your GEMINI_API_KEY and RAPIDAPI_KEY.")
    st.stop()

# Initialize LLM Handler
try:
    llm_handler.set_llm_model(GEMINI_API_KEY)
except Exception as e:
    st.error(f"Failed to initialize the LLM handler: {e}")
    st.stop()

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # For displaying chat UI
if "llm_history" not in st.session_state:
    st.session_state.llm_history = [] # For LLM context
if 'graph' not in st.session_state:
    st.session_state['graph'] = nx.MultiDiGraph() # Initialize NetworkX graph


# --- UI Components ---

# Sidebar for Controls
with st.sidebar:
    st.subheader("Graph Controls")
    if st.button("Clear Conversation History & Graph"):
        st.session_state.messages = []
        st.session_state.llm_history = []
        st.session_state.graph = nx.MultiDiGraph()
        st.success("History and Graph Cleared!")
        time.sleep(1) # Brief pause
        st.rerun() # Rerun to reflect cleared state

    st.subheader("Graph Info")
    graph_info_placeholder = st.empty()


# Main Chat Interface Area
chat_container = st.container() # Use container for chat messages

with chat_container:
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Separate container for the graph below chat
graph_container = st.container()

# --- Handle User Input & Processing ---
if prompt := st.chat_input("Ask about Twitter..."):
    # Add user message to display state immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message
    with chat_container:
         with st.chat_message("user"):
            st.markdown(prompt)

    # --- Call Backend Logic ---
    final_summary = ""
    llm_structured_response = {}
    execution_results = [] # Store results here

    try:
        # Display thinking indicator within chat container
        with chat_container:
            with st.chat_message("assistant"):
                status_placeholder = st.empty() # Placeholder for status updates
                status_placeholder.markdown("Thinking... 🤔")

                # 1. Get Plan/Clarification from LLM
                formatted_hist = state_manager.get_history_for_prompt(st.session_state.llm_history)
                llm_response = llm_handler.get_llm_plan(prompt, formatted_hist)
                llm_structured_response = llm_response

                response_type = llm_response.get('response_type')
                message_to_user = llm_response.get('message_to_user')
                api_plan = llm_response.get('api_plan')

                # Display initial message from LLM (status or clarification)
                if message_to_user:
                     status_placeholder.info(message_to_user)

                if response_type == "CLARIFICATION" or response_type == "ERROR":
                    final_summary = message_to_user

                elif response_type == "PLAN":
                    if not api_plan:
                        final_summary = message_to_user or "I generated a plan but it was empty. Please try again."
                    else:
                        # 2. Execute API Plan
                        status_placeholder.markdown("Executing API plan... ⚙️")
                        execution_error_occurred = False
                        with st.expander("Execution Details", expanded=False): # Use expander for logs
                            start_time = time.time()
                            sorted_plan = sorted(api_plan, key=lambda x: x.get('step', 0))
                            for step_num, step in enumerate(sorted_plan):
                                st.write(f"Step {step_num + 1}: Calling {step.get('endpoint')}...")
                                try:
                                     step_result = api_client.execute_api_step(
                                         step,
                                         execution_results,
                                         RAPIDAPI_KEY
                                     )
                                except Exception as exec_e:
                                     # Catch errors during the API call/processing itself
                                     st.error(f"Critical error executing step {step_num + 1}: {exec_e}")
                                     final_summary = f"A critical error occurred during API execution: {exec_e}"
                                     execution_error_occurred = True
                                     break

                                step_result['step_executed'] = step.get('step', step_num + 1) # Add step num to result
                                execution_results.append(step_result)

                                if 'error' in step_result:
                                    error_msg = f"Error in Step {step_num + 1} ({step.get('endpoint')}): {step_result['error']}"
                                    st.error(error_msg)
                                    final_summary = f"I encountered an error during execution and couldn't complete your request:\n```\n{error_msg}\n```"
                                    execution_error_occurred = True
                                    break
                                else:
                                     st.write(f"Step {step_num + 1} completed.")

                            if not execution_error_occurred:
                                exec_time = time.time() - start_time
                                st.write(f"API Execution Complete ({exec_time:.2f}s)")

                        # --- 2.5 UPDATE GRAPH ---
                        if not execution_error_occurred:
                            status_placeholder.markdown("Updating graph... 🕸️")
                            try:
                                current_graph = st.session_state['graph']
                                for result_item in execution_results:
                                     # Call the central parser in graph_manager
                                     graph_manager.parse_and_process_api_result(current_graph, result_item)
                                st.session_state['graph'] = current_graph # Save updated graph back
                                status_placeholder.markdown("Graph updated.")
                            except Exception as graph_e:
                                 st.error(f"Error updating graph data: {graph_e}")
                                 # Continue without graph update if it fails? Or halt?

                        # 3. Summarize Results (if execution successful)
                        if not execution_error_occurred:
                            if not execution_results or not any(res.get('data') for res in execution_results if res and 'error' not in res):
                                final_summary = "I executed the plan, but no data was retrieved to summarize."
                            else:
                                status_placeholder.markdown("Generating summary... ✍️")
                                # --- Check for filtering necessity ---
                                final_data_for_summary = execution_results
                                # Check if the request was *specifically* for replies *made by* someone
                                if ("replies" in prompt.lower() and
                                    ("made by" in prompt.lower() or "from @" in prompt.lower())): # Added "from @"
                                     st.write("Filtering results for replies...")
                                     # ... (Filtering Logic - same as previous response) ...
                                     # (Ensure this logic correctly creates filtered_step_result with needed keys)
                                     filtered_results = []
                                     if execution_results and 'data' in execution_results[0] and isinstance(execution_results[0]['data'], dict) and 'timeline' in execution_results[0]['data']:
                                          timeline_data = execution_results[0]['data']['timeline']
                                          if isinstance(timeline_data, list):
                                               actual_replies = [
                                                   item for item in timeline_data
                                                   if item and item.get('in_reply_to_status_id_str')
                                               ]
                                               if actual_replies:
                                                    filtered_step_result = execution_results[0].copy()
                                                    filtered_step_result['data'] = { 'timeline': actual_replies }
                                                    filtered_results.append(filtered_step_result)
                                                    st.write(f"Found {len(actual_replies)} replies after filtering.")
                                               else:
                                                    st.write("No actual replies found in timeline data after filtering.")
                                                    filtered_results.append({'endpoint': execution_results[0].get('endpoint'), 'data': {'timeline': []}})

                                          if len(execution_results) > 1:
                                              filtered_results.extend(execution_results[1:])

                                          if filtered_results:
                                              final_data_for_summary = filtered_results
                                          else:
                                               final_data_for_summary = [{'endpoint': 'filter', 'data': {'timeline': []}}]
                                     else:
                                          st.warning("Could not find 'timeline' list in first step results for filtering replies.")
                                # --- End Filtering ---

                                final_summary = llm_handler.get_llm_summary(prompt, final_data_for_summary)
                                status_placeholder.empty() # Clear status message on success

                else:
                     final_summary = "Sorry, I received an unexpected response type from the planning module."
                     status_placeholder.error(final_summary)

    except Exception as e:
        # Catch unexpected errors during the whole process
        st.error(f"An unexpected error occurred: {e}")
        final_summary = f"Sorry, an unexpected error stopped me from completing your request: {e}"
        llm_structured_response = {"response_type": "SYSTEM_ERROR", "message_to_user": str(e)}
        # Clear placeholder if error happened before it was cleared
        if 'status_placeholder' in locals() and hasattr(status_placeholder, 'empty'): status_placeholder.empty()


    # --- Display Final AI Response and Update History ---
    if not isinstance(final_summary, str):
        final_summary = "Sorry, I could not generate a final response."

    with chat_container:
        with st.chat_message("assistant"):
            st.markdown(final_summary)

    st.session_state.messages.append({"role": "assistant", "content": final_summary})
    st.session_state.llm_history.append({
        "user_query": prompt,
        "llm_response": llm_structured_response, # Plan/Clarification/Error JSON
        "summary": final_summary # Final text shown
        })

# --- Display Graph ---
with graph_container:
    st.divider()
    st.subheader("Session Interaction Graph")
    graph = st.session_state.get('graph', nx.MultiDiGraph()) # Get the graph

    if not graph or graph.number_of_nodes() == 0:
        st.caption("Graph is empty. Ask some questions to populate it!")
    else:
        # --- Pyvis Integration ---
        try:
            net = Network(height='600px', width='100%', directed=True, notebook=True, cdn_resources='in_line')
            
            # Add physics configuration buttons BEFORE setting options
            # This ensures that options.configure is set up properly
            net.show_buttons(filter_=['physics'])
            
            # Configure physics for better stability
            physics_options = {
                "enabled": True,
                "solver": "barnesHut",
                "barnesHut": {
                    "gravitationalConstant": -10000,  # Strong repulsion to separate nodes
                    "centralGravity": 0.3,            # Increased pull towards center for stability
                    "springLength": 150,              # Longer edges for clearer visualization
                    "springConstant": 0.04,           # Softer springs for slower motion
                    "damping": 0.09,                  # Dampening for quicker settling
                    "avoidOverlap": 0.5               # Increased overlap avoidance
                },
                "stabilization": {
                    "enabled": True,
                    "iterations": 1000,               # More iterations for initial stabilization
                    "updateInterval": 50,             # Update view less frequently during stabilization
                    "fit": True                       # Scale to fit all nodes when done
                },
                "minVelocity": 0.75,                  # Stop simulation when nodes slow down
                "maxVelocity": 30                     # Cap maximum velocity to prevent "shooting" nodes
            }
            
            # Set the physics configuration - with all options combined
            options = {
                "physics": physics_options,
                "interaction": {
                    "navigationButtons": True,        # Add navigation controls
                    "hover": True,                    # Enable hover effects
                },
                "edges": {
                    "smooth": {
                        "type": "continuous",         # Smoother edge curves
                        "forceDirection": "none",
                    },
                    "arrows": {
                        "to": {"enabled": True, "scaleFactor": 0.5}  # Smaller arrows
                    }
                }
            }
            
            # Apply all options at once AFTER show_buttons has been called
            net.set_options(json.dumps(options))
            
            # Add nodes and edges from NetworkX graph to Pyvis network
            # Map NetworkX attributes to Pyvis attributes
            for node_id, attrs in graph.nodes(data=True):
                node_type = attrs.get('node_type', 'Unknown')
                pyvis_title = f"ID: {node_id}<br>Type: {node_type}" # HTML for tooltips
                pyvis_label = str(node_id)
                pyvis_color = '#CCCCCC'
                pyvis_size = 15

                # Apply styling based on ontology (similar logic as before)
                if node_type == "User":
                    pyvis_color = '#97C2FC' # Blue
                    followers = attrs.get('followers_count', 0)
                    pyvis_size = 15 + int(min(max(followers, 0)**0.3, 25))
                    pyvis_label = attrs.get('screen_name', node_id)
                    pyvis_title = f"<b>User:</b> @{pyvis_label}<br><b>Name:</b> {attrs.get('name', 'N/A')}<br><b>Bio:</b> {attrs.get('description', 'N/A')}<br><b>Followers:</b> {followers}"
                elif node_type == "Tweet":
                    pyvis_color = '#A_FB_A' # Green
                    engagement = attrs.get('retweets_count', 0) + attrs.get('likes_count', 0)
                    pyvis_size = 10 + int(min(max(engagement, 0)**0.25, 20))
                    pyvis_label = "" # Often hide tweet labels for clarity
                    pyvis_title = f"<b>Tweet:</b> {attrs.get('tweet_id', node_id)}<br><b>Author:</b> @{attrs.get('author_screen_name', 'N/A')}<br><b>Created:</b> {attrs.get('created_at', 'N/A')}<br><b>Text:</b> {attrs.get('text', '')[:150]}...<br><b>Likes:</b> {attrs.get('likes_count',0)}, RTs: {attrs.get('retweets_count',0)}"
                elif node_type == "List":
                     pyvis_color = '#FFB347' # Orange
                     pyvis_size = 20
                     pyvis_label = attrs.get('name', node_id)
                     pyvis_title = f"<b>List:</b> {pyvis_label}<br><b>ID:</b> {attrs.get('list_id', node_id)}<br><b>Desc:</b> {attrs.get('description', 'N/A')}"
                # Add elif for Space, Community...

                net.add_node(str(node_id), label=pyvis_label, title=pyvis_title, color=pyvis_color, size=pyvis_size, node_type=node_type) # Store node_type if needed

            edge_color_map = { # Same map as before
                'FOLLOWS': '#DDDDDD', 'POSTED': '#BBBBBB', 'IS_REPLY_TO': '#77DD77',
                'IS_QUOTE_OF': '#FFC080', 'IS_RETWEET_OF': '#ADD8E6', 'MENTIONS': '#FFB347',
                'MEMBER_OF': '#FFD700', 'FOLLOWS_LIST': '#FFD700', 'OWNS_LIST': '#FFD700',
                'CONTAINS_TWEET': '#DDA0DD', 'CREATED_SPACE': '#FFA0BC', 'ADMIN_OF_SPACE': '#FFA0BC',
                'SPEAKER_IN_SPACE': '#FFA0BC'
            }
            for u, v, attrs in graph.edges(data=True):
                edge_type = attrs.get('type', 'UNKNOWN')
                edge_color = edge_color_map.get(edge_type, '#888888')
                edge_title = edge_type # Tooltip for edge type

                net.add_edge(str(u), str(v), title=edge_title, color=edge_color, type=edge_type) # physics=False? Arrow settings?

            # --- Generate and Display HTML ---
            # Option 1: Save to file then display (might be more reliable for complex graphs)
            # html_file = 'twitter_network.html'
            # net.save_graph(html_file)
            # with open(html_file, 'r', encoding='utf-8') as f:
            #     html_content = f.read()
            # components.html(html_content, height=610, scrolling=False)

            # Option 2: Generate HTML string directly (simpler for moderate graphs)
            try:
                # Instead of using save_graph which relies on the system's default encoding
                # Write the HTML directly with UTF-8 encoding
                with open('pyvis_graph.html', 'w', encoding='utf-8') as f:
                    f.write(net.generate_html())
                
                with open('pyvis_graph.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()
                components.html(html_content, height=610, scrolling=False)
            except UnicodeEncodeError as e:
                # If we still have encoding issues, try a fallback approach
                st.warning("Encountered encoding issues with graph data. Attempting fallback visualization...")
                
                # Clean node titles/labels to remove problematic characters
                for node in net.nodes:
                    if 'title' in node:
                        # Replace any problematic characters with safe equivalents
                        node['title'] = (str(node['title'])
                                       .encode('ascii', 'replace')
                                       .decode('ascii'))
                    if 'label' in node:
                        node['label'] = (str(node['label'])
                                       .encode('ascii', 'replace')
                                       .decode('ascii'))
                
                # Try again with cleaned data
                with open('pyvis_graph_clean.html', 'w', encoding='utf-8') as f:
                    f.write(net.generate_html())
                
                with open('pyvis_graph_clean.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()
                components.html(html_content, height=610, scrolling=False)


        except Exception as e:
            st.error(f"Failed to generate graph visualization: {e}")
            import traceback
            st.code(traceback.format_exc()) # Show detailed error for debugging

# Update graph info in sidebar
graph = st.session_state.get('graph', nx.MultiDiGraph())
with graph_info_placeholder.container():
    st.metric("Nodes", graph.number_of_nodes())
    st.metric("Edges", graph.number_of_edges())
    # Count node types
    node_counts = {}
    for _, attrs in graph.nodes(data=True):
        ntype = attrs.get('node_type', 'Unknown')
        node_counts[ntype] = node_counts.get(ntype, 0) + 1
    st.write("**Node Types:**")
    if node_counts:
        st.dataframe(node_counts)
    else:
        st.caption("No nodes yet.")