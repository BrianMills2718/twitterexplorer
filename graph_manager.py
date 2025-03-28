# graph_manager.py
import networkx as nx
import logging # Optional: for more detailed logging

logger = logging.getLogger(__name__)

# --- Node Update Helper ---
def update_node(graph, node_id, node_type, properties):
    """Adds or updates a node in the graph."""
    if not node_id:
        logger.warning(f"Attempted to add node with empty ID. Properties: {properties}")
        return False

    if graph.has_node(node_id):
        # Update existing node properties (only update provided ones)
        graph.nodes[node_id].update({k: v for k, v in properties.items() if v is not None})
        # Ensure node_type is always set correctly
        graph.nodes[node_id]['node_type'] = node_type
    else:
        # Add new node with all properties
        properties['node_type'] = node_type
        graph.add_node(node_id, **properties)
    return True

# --- Edge Update Helper ---
def add_edge(graph, source_id, target_id, edge_type, **properties):
    """Adds a directed edge if it doesn't already exist between these nodes with this type."""
    if not source_id or not target_id:
        logger.warning(f"Attempted to add edge with missing source/target ID. Type: {edge_type}")
        return

    # Check if an edge of this type already exists (MultiDiGraph allows parallel edges)
    # For simplicity, let's just add it; MultiDiGraph handles it.
    # If using DiGraph, you'd check: if not graph.has_edge(source_id, target_id, key=edge_type):
    graph.add_edge(source_id, target_id, key=edge_type, type=edge_type, **properties)


# --- Parsers for Different API Data Types ---

def parse_and_add_user(graph, user_data):
    """Parses user data (from screenname.php, followers, etc.) and adds/updates node."""
    if not isinstance(user_data, dict): return

    screen_name = user_data.get('screen_name') or user_data.get('profile') # Use screen_name as ID
    rest_id = user_data.get('rest_id') or user_data.get('user_id') or user_data.get('id')

    if not screen_name:
        logger.warning(f"Skipping user add/update due to missing screen_name. Data: {user_data}")
        return

    # Map API keys to ontology properties
    properties = {
        'rest_id': str(rest_id) if rest_id else None,
        'screen_name': screen_name,
        'name': user_data.get('name'),
        'description': user_data.get('description') or user_data.get('desc'),
        'avatar_url': user_data.get('avatar') or user_data.get('profile_image'),
        'followers_count': int(user_data.get('followers_count') or user_data.get('sub_count') or 0),
        'following_count': int(user_data.get('following_count') or user_data.get('friends_count') or user_data.get('friends') or 0),
        'statuses_count': int(user_data.get('statuses_count') or 0),
        'location': user_data.get('location'),
        'created_at': user_data.get('created_at'),
        'blue_verified': user_data.get('blue_verified') or False,
        'is_protected': user_data.get('protected') or False,
        'data_source_endpoint': user_data.get('data_source_endpoint') # Optional: add later if needed
    }
    update_node(graph, screen_name, "User", properties)

def parse_and_add_tweet(graph, tweet_data):
    """Parses tweet data (from timeline, tweet.php, etc.) and adds/updates node and edges."""
    if not isinstance(tweet_data, dict): return

    tweet_id = tweet_data.get('tweet_id') or tweet_data.get('id')
    if not tweet_id:
        logger.warning(f"Skipping tweet add/update due to missing tweet_id. Data: {tweet_data}")
        return

    # --- Extract Tweet Properties ---
    author_info = tweet_data.get('author') or tweet_data.get('user_info') # Author of this tweet obj
    author_screen_name = None
    if isinstance(author_info, dict):
        author_screen_name = author_info.get('screen_name')
        # Optionally add/update the author User node here too
        parse_and_add_user(graph, author_info)

    # Determine tweet type flags
    retweeted_tweet_obj = tweet_data.get('retweeted_tweet') or tweet_data.get('retweeted') # Check both common keys
    quoted_tweet_obj = tweet_data.get('quoted')
    in_reply_to_status_id = tweet_data.get('in_reply_to_status_id_str') or tweet_data.get('in_reply_to_status_id')
    in_reply_to_screen_name = tweet_data.get('in_reply_to_screen_name')

    is_retweet = bool(retweeted_tweet_obj)
    is_quote = bool(quoted_tweet_obj)
    is_reply = bool(in_reply_to_status_id)

    # Simplified media type
    media_type = "None"
    if isinstance(tweet_data.get('media'), dict):
        if tweet_data['media'].get('video'): media_type = "Video"
        elif tweet_data['media'].get('photo'): media_type = "Photo"
        # Add checks for GIF if API provides that info

    # Helper function to safely convert counts/views to int
    def safe_int(value, default=0):
        if value is None: return default
        try: return int(value)
        except (ValueError, TypeError): return default

    properties = {
        'tweet_id': str(tweet_id),
        'author_screen_name': author_screen_name,
        'text': tweet_data.get('text') or tweet_data.get('display_text'),
        'created_at': tweet_data.get('created_at'),
        'conversation_id': tweet_data.get('conversation_id'),
        'lang': tweet_data.get('lang'),
        'views_count': safe_int(tweet_data.get('views')),
        'likes_count': safe_int(tweet_data.get('favorites') or tweet_data.get('likes')),
        'retweets_count': safe_int(tweet_data.get('retweets')),
        'quotes_count': safe_int(tweet_data.get('quotes')), # Might be count or object key, check usage
        'replies_count': safe_int(tweet_data.get('replies')),
        'bookmarks_count': safe_int(tweet_data.get('bookmarks')),
        'in_reply_to_status_id': str(in_reply_to_status_id) if in_reply_to_status_id else None,
        'in_reply_to_screen_name': in_reply_to_screen_name,
        'is_retweet': is_retweet,
        'is_quote': is_quote,
        'is_reply': is_reply,
        'media_type': media_type,
        'data_source_endpoint': tweet_data.get('data_source_endpoint')
    }

    # Add/Update the Tweet Node
    if not update_node(graph, str(tweet_id), "Tweet", properties):
        return # Stop if node couldn't be added

    # --- Add Edges ---
    # POSTED Edge
    if author_screen_name:
        add_edge(graph, author_screen_name, str(tweet_id), "POSTED")

    # IS_REPLY_TO Edge
    if is_reply and in_reply_to_status_id:
        add_edge(graph, str(tweet_id), str(in_reply_to_status_id), "IS_REPLY_TO")
        # We might not have the target tweet node yet, but edge can be added

    # IS_QUOTE_OF Edge
    if is_quote and isinstance(quoted_tweet_obj, dict):
        quoted_id = quoted_tweet_obj.get('tweet_id') or quoted_tweet_obj.get('id')
        if quoted_id:
            add_edge(graph, str(tweet_id), str(quoted_id), "IS_QUOTE_OF")
            # Optionally parse and add the quoted tweet/author node too
            parse_and_add_tweet(graph, quoted_tweet_obj) # Recursive add

    # IS_RETWEET_OF Edge
    if is_retweet and isinstance(retweeted_tweet_obj, dict):
         original_id = retweeted_tweet_obj.get('tweet_id') or retweeted_tweet_obj.get('id')
         if original_id:
             add_edge(graph, str(tweet_id), str(original_id), "IS_RETWEET_OF")
             # Optionally parse and add the original tweet/author node too
             parse_and_add_tweet(graph, retweeted_tweet_obj) # Recursive add

    # MENTIONS Edges
    mentions = tweet_data.get("entities", {}).get("user_mentions", [])
    if isinstance(mentions, list):
        for mention in mentions:
            mentioned_sn = mention.get("screen_name")
            if mentioned_sn:
                # Add mentioned user node (minimal info for now if not fetched separately)
                update_node(graph, mentioned_sn, "User", {'screen_name': mentioned_sn})
                add_edge(graph, str(tweet_id), mentioned_sn, "MENTIONS")

def parse_and_process_api_result(graph, result_item):
    """Determines the type of data in the result and calls the appropriate parser."""
    if not isinstance(result_item, dict):
        logger.warning(f"Skipping result item as it's not a dictionary: {type(result_item)}")
        return

    endpoint = result_item.get('endpoint')
    data = result_item.get('data')

    if not data or not endpoint:
        logger.warning(f"Skipping result item due to missing data or endpoint info.")
        return

    logger.info(f"Processing data from endpoint: {endpoint}")

    # Determine data type based on endpoint and data structure
    if endpoint in ["screenname.php", "tweet.php", "spaces.php"]: # Endpoints returning single object
        if 'tweet_id' in data or 'id' in data and endpoint == "tweet.php": # Check for tweet keys
             parse_and_add_tweet(graph, data)
        elif 'rest_id' in data and endpoint == "screenname.php": # Check for user keys
             parse_and_add_user(graph, data)
        # Add elif for spaces.php data structure check
        elif 'media_key' in data and 'playlist' in data: # Heuristic for Space data
             # parse_and_add_space(graph, data) # Implement this function
             logger.info("Space parsing not fully implemented yet.")
        else:
             logger.warning(f"Unrecognized single object structure from endpoint {endpoint}")

    elif endpoint in ["timeline.php", "usermedia.php", "search.php", "latest_replies.php", "listtimeline.php", "community_timeline.php"]: # Endpoints returning list of tweets
         timeline = data.get('timeline') # Common key
         if isinstance(timeline, list):
             logger.info(f"Parsing {len(timeline)} tweets from {endpoint}")
             for tweet in timeline:
                  parse_and_add_tweet(graph, tweet)
         else:
              logger.warning(f"Expected 'timeline' list not found or not a list in response from {endpoint}")
         # Add user node from top-level 'user' key if present (e.g., in timeline.php)
         user_info = data.get('user')
         if isinstance(user_info, dict):
             parse_and_add_user(graph, user_info)

    elif endpoint in ["followers.php", "following.php", "retweets.php", "list_followers.php", "list_members.php"]: # Endpoints potentially returning list of users
         user_list = None
         source_screenname = None # Variable to hold the source user of the query

         # Extract source screenname from the executed parameters included in the result item
         executed_params = result_item.get('executed_params', {})
         if 'screenname' in executed_params:
              source_screenname = executed_params['screenname']
         # Add other potential source keys if needed (e.g., 'list_id' for list endpoints)
         # list_id = executed_params.get('list_id')

         list_keys = ['followers', 'following', 'retweets', 'members'] # Keys containing user lists
         for key in list_keys:
             # Check if the key exists directly in the data payload
             if key in data and isinstance(data.get(key), list):
                  user_list = data[key]
                  logger.info(f"Parsing {len(user_list)} users from key '{key}' in {endpoint}")
                  break

         # Now add edges if we have the list and the source context
         if user_list is not None: # Check if we found a user list
             if source_screenname:
                 # Ensure source node exists in the graph
                 update_node(graph, source_screenname, "User", {'screen_name': source_screenname})

                 for user in user_list:
                      # Add/Update the target user node first
                      parse_and_add_user(graph, user)

                      # Get the screen name of the target user from the list item
                      target_sn = user.get('screen_name')

                      if target_sn:
                          # Add the FOLLOWS edge with correct direction
                          if endpoint == "following.php":
                              # Source user follows target user
                              add_edge(graph, source_screenname, target_sn, "FOLLOWS")
                              print(f"  Added edge: {source_screenname} -> FOLLOWS -> {target_sn}") # Debug print
                          elif endpoint == "followers.php":
                              # Target user follows source user
                              add_edge(graph, target_sn, source_screenname, "FOLLOWS")
                              print(f"  Added edge: {target_sn} -> FOLLOWS -> {source_screenname}") # Debug print
                          # Add logic here for list membership/following edges if list_id context is available
                          # elif endpoint == "list_followers.php" and list_id:
                          #     add_edge(graph, target_sn, str(list_id), "FOLLOWS_LIST")
                          # elif endpoint == "list_members.php" and list_id:
                          #     add_edge(graph, target_sn, str(list_id), "MEMBER_OF")

             elif endpoint not in ["retweets.php"]: # Don't warn if source isn't needed (like for retweeters list)
                  logger.warning(f"Could not determine source screenname from params for {endpoint} to add relationship edges.")
         else:
              logger.warning(f"Expected user list not found in response from {endpoint} using keys {list_keys}")

    # --- ADD LOGIC FOR LIST MEMBERS ---
    elif endpoint == "list_members.php":
        user_list = data.get('members')
        # Get context: which list were these members fetched for?
        list_id = result_item.get('executed_params', {}).get('list_id')
        if isinstance(user_list, list) and list_id:
            # Ensure the List node itself exists (might have minimal data initially)
            list_node_id = f"list_{list_id}" # Create a unique node ID prefix for lists
            update_node(graph, list_node_id, "List", {'list_id': str(list_id)}) # Add/update list node
            logger.info(f"Parsing {len(user_list)} list members for list {list_id}")
            for user in user_list:
                parse_and_add_user(graph, user) # Add/update user node
                target_sn = user.get('screen_name')
                if target_sn:
                    # User is MEMBER_OF List
                    add_edge(graph, target_sn, list_node_id, "MEMBER_OF")
                    print(f"  Added edge: {target_sn} -> MEMBER_OF -> {list_node_id}")
        else:
             logger.warning(f"Expected 'members' list or 'list_id' param not found for {endpoint}")

    # --- ADD LOGIC FOR LIST FOLLOWERS ---
    elif endpoint == "list_followers.php":
        user_list = data.get('followers')
        list_id = result_item.get('executed_params', {}).get('list_id')
        if isinstance(user_list, list) and list_id:
            list_node_id = f"list_{list_id}"
            update_node(graph, list_node_id, "List", {'list_id': str(list_id)})
            logger.info(f"Parsing {len(user_list)} list followers for list {list_id}")
            for user in user_list:
                parse_and_add_user(graph, user)
                target_sn = user.get('screen_name')
                if target_sn:
                    # User FOLLOWS_LIST List
                    add_edge(graph, target_sn, list_node_id, "FOLLOWS_LIST")
                    print(f"  Added edge: {target_sn} -> FOLLOWS_LIST -> {list_node_id}")
        else:
             logger.warning(f"Expected 'followers' list or 'list_id' param not found for {endpoint}")

    # --- ADD LOGIC FOR LIST TIMELINE / COMMUNITY TIMELINE ---
    elif endpoint in ["listtimeline.php", "community_timeline.php"]:
        timeline = data.get('timeline')
        # Get context: which list/community were these tweets fetched for?
        list_id = result_item.get('executed_params', {}).get('list_id')
        community_id = result_item.get('executed_params', {}).get('community_id')
        source_node_id = None
        source_node_type = None
        if list_id:
            source_node_id = f"list_{list_id}"
            source_node_type = "List"
            update_node(graph, source_node_id, source_node_type, {'list_id': str(list_id)})
        elif community_id:
             source_node_id = f"community_{community_id}"
             source_node_type = "Community"
             update_node(graph, source_node_id, source_node_type, {'community_id': str(community_id)})

        if isinstance(timeline, list) and source_node_id:
            logger.info(f"Parsing {len(timeline)} tweets for {source_node_type} {source_node_id}")
            for tweet in timeline:
                # Add tweet node and its internal edges (posted, mentions, etc.)
                parse_and_add_tweet(graph, tweet)
                tweet_id = tweet.get('tweet_id') or tweet.get('id')
                if tweet_id:
                    # Add edge: List/Community CONTAINS_TWEET Tweet
                    add_edge(graph, source_node_id, str(tweet_id), "CONTAINS_TWEET")
                    print(f"  Added edge: {source_node_id} -> CONTAINS_TWEET -> {tweet_id}")
        else:
             logger.warning(f"Expected 'timeline' list or list/community id not found for {endpoint}")

    # --- ADD LOGIC FOR SPACES ---
    elif endpoint == "spaces.php":
         space_id = data.get('id')
         if space_id:
             space_node_id = f"space_{space_id}"
             # parse_and_add_space(graph, data) # Create this function if needed
             # For now, just add the node and creator edge
             creator_info = data.get('creator', {})
             creator_sn = creator_info.get('screenname')
             update_node(graph, space_node_id, "Space", {
                 'space_id': space_id,
                 'state': data.get('state'),
                 'started_at': data.get('started'),
                 'creator_screen_name': creator_sn
             })
             print(f"Adding/Updating Space node: {space_node_id}")

             if creator_sn:
                 update_node(graph, creator_sn, "User", {'screen_name': creator_sn}) # Ensure creator node exists
                 add_edge(graph, creator_sn, space_node_id, "CREATED_SPACE")
                 print(f"  Added edge: {creator_sn} -> CREATED_SPACE -> {space_node_id}")

             # Add edges for Admins
             admins = data.get('participants', {}).get('admins', [])
             for admin in admins:
                 admin_sn = admin.get('screenname')
                 if admin_sn:
                      update_node(graph, admin_sn, "User", {'screen_name': admin_sn})
                      add_edge(graph, admin_sn, space_node_id, "ADMIN_OF_SPACE")
                      print(f"  Added edge: {admin_sn} -> ADMIN_OF_SPACE -> {space_node_id}")

             # Add edges for Speakers
             speakers = data.get('participants', {}).get('speakers', [])
             for speaker in speakers:
                 speaker_sn = speaker.get('screenname')
                 if speaker_sn:
                      update_node(graph, speaker_sn, "User", {'screen_name': speaker_sn})
                      add_edge(graph, speaker_sn, space_node_id, "SPEAKER_IN_SPACE")
                      print(f"  Added edge: {speaker_sn} -> SPEAKER_IN_SPACE -> {space_node_id}")
         else:
             logger.warning(f"Could not find space ID in data for {endpoint}")

    elif endpoint == "screennames.php": # Endpoint returning specific user list structure
         user_list = data.get('users')
         if isinstance(user_list, list):
              logger.info(f"Parsing {len(user_list)} users from {endpoint}")
              for user in user_list:
                   parse_and_add_user(graph, user)
         else:
               logger.warning(f"Expected 'users' list not found in response from {endpoint}")

    # Add elif blocks for other specific endpoint structures (affiliates, trends etc.) if needed
    # ...

    else:
         logger.warning(f"No specific parsing logic implemented for endpoint: {endpoint}")