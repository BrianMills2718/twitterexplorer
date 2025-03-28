# ontology_synonyms.py

# User entity properties and synonyms
USER_SYNONYMS = {
    "user_id": ["id", "user_id", "id_str", "rest_id"],
    "rest_id": ["rest_id"],  # sometimes repeated, but let's keep it distinct
    "screen_name": ["screen_name", "profile"],
    "name": ["name", "display_name"],
    "description": ["description", "desc"],
    "location": ["location"],
    "legacy_verified": ["verified", "is_verified"],
    "blue_verified": ["blue_verified", "is_blue_verified"],
    "business_account": ["business_account"],
    "protected": ["protected"],
    "avatar": ["avatar", "profile_image", "image"],
    "header_image": ["header_image"],
    "created_at": ["created_at"],
    "followers_count": ["followers_count", "sub_count"],
    "following_count": ["friends", "friends_count"],
    "statuses_count": ["statuses_count"],
    "media_count": ["media_count"],
    "favourites_count": ["favourites_count"],
    "website": ["website"],
    "lang": ["lang"]
}

# Tweet entity properties and synonyms
TWEET_SYNONYMS = {
    "tweet_id": ["id", "tweet_id", "id_str"],
    "text": ["text", "display_text"],
    "created_at": ["created_at"],
    "conversation_id": ["conversation_id"],
    "lang": ["lang"],
    "view_count": ["views"],
    "reply_count": ["replies", "reply_count"],
    "retweet_count": ["retweets"],
    "quote_count": ["quotes"],
    "favorite_count": ["likes", "favorites", "favourites"],
    "bookmark_count": ["bookmarks"],
    "in_reply_to_status_id": ["in_reply_to_status_id_str"],
    "in_reply_to_user_id": ["in_reply_to_user_id_str"],
    "in_reply_to_screen_name": ["in_reply_to_screen_name"],
    "possibly_sensitive": ["sensitive"],
    "media": ["media"],
    "hashtags": ["hashtags"],
    "urls": ["urls"],
    "entities": ["entities"]
}

# List entity properties and synonyms
LIST_SYNONYMS = {
    "list_id": ["list_id"],
    "name": ["name"],
    "description": ["description"],
    "member_count": ["member_count"],
    "follower_count": ["follower_count"],
    "created_at": ["created_at"],
    "owner_id": ["owner_id"],
    "owner_screen_name": ["owner_screen_name"]
}

# Space entity properties and synonyms
SPACE_SYNONYMS = {
    "space_id": ["id", "space_id"],
    "title": ["title"],
    "state": ["state"],
    "created_at": ["created_at", "started"],
    "ended_at": ["ended", "ended_at"],
    "participant_count": ["total_live_listeners"],
    "replay_count": ["total_replay_watched"],
    "replay_available": ["replay_available", "is_space_available_for_replay"],
    "creator_id": ["creator_id"],
    "admin_ids": ["admin_ids"],
    "speaker_ids": ["speaker_ids"]
}

# Relationship types (edges) between entities
RELATIONSHIP_TYPES = {
    # User to User relationships
    "follows": {
        "description": "User follows another user",
        "endpoints": ["following.php", "followers.php", "checkfollow.php"],
        "source": "USER",
        "target": "USER"
    },
    # User to Tweet relationships
    "authored": {
        "description": "User authored a tweet",
        "endpoints": ["timeline.php", "usermedia.php", "tweet.php"],
        "source": "USER",
        "target": "TWEET"
    },
    "liked": {
        "description": "User liked a tweet",
        "endpoints": [],  # Not directly available in endpoints
        "source": "USER",
        "target": "TWEET"
    },
    "retweeted": {
        "description": "User retweeted a tweet",
        "endpoints": ["checkretweet.php", "retweets.php"],
        "source": "USER",
        "target": "TWEET"
    },
    "replied": {
        "description": "User replied to a tweet",
        "endpoints": ["latest_replies.php", "replies.php"],
        "source": "USER",
        "target": "TWEET"
    },
    "quoted": {
        "description": "User quoted a tweet",
        "endpoints": [],  # Not directly available in endpoints
        "source": "USER",
        "target": "TWEET"
    },
    "mentioned": {
        "description": "User was mentioned in a tweet",
        "endpoints": ["tweet.php"],  # Check entities.user_mentions
        "source": "TWEET",
        "target": "USER"
    },
    # User to List relationships
    "created_list": {
        "description": "User created a list",
        "endpoints": [],  # Not directly available in endpoints
        "source": "USER",
        "target": "LIST"
    },
    "follows_list": {
        "description": "User follows a list",
        "endpoints": ["list_followers.php"],
        "source": "USER",
        "target": "LIST"
    },
    "member_of_list": {
        "description": "User is a member of a list",
        "endpoints": ["list_members.php"],
        "source": "USER",
        "target": "LIST"
    },
    # User to Space relationships
    "created_space": {
        "description": "User created a space",
        "endpoints": ["spaces.php"],
        "source": "USER",
        "target": "SPACE"
    },
    "admin_of_space": {
        "description": "User is an admin of a space",
        "endpoints": ["spaces.php"],
        "source": "USER",
        "target": "SPACE"
    },
    "speaker_in_space": {
        "description": "User is a speaker in a space",
        "endpoints": ["spaces.php"],
        "source": "USER",
        "target": "SPACE"
    },
    "listener_in_space": {
        "description": "User is a listener in a space",
        "endpoints": ["spaces.php"],
        "source": "USER",
        "target": "SPACE"
    },
    # Tweet to Tweet relationships
    "reply_to": {
        "description": "Tweet is a reply to another tweet",
        "endpoints": ["tweet.php", "latest_replies.php"],
        "source": "TWEET",
        "target": "TWEET"
    },
    "quote_of": {
        "description": "Tweet quotes another tweet",
        "endpoints": ["tweet.php"],
        "source": "TWEET",
        "target": "TWEET"
    },
    "thread_with": {
        "description": "Tweet is part of a thread with another tweet",
        "endpoints": ["tweet_thread.php"],
        "source": "TWEET",
        "target": "TWEET"
    }
}

# Mapping of high-level user queries to endpoint patterns
QUERY_PATTERNS = {
    "user_info": {
        "description": "Get basic information about a user",
        "primary_endpoint": "screenname.php",
        "parameters": ["screenname"],
        "entity_type": "USER"
    },
    "user_timeline": {
        "description": "Get a user's recent tweets",
        "primary_endpoint": "timeline.php",
        "parameters": ["screenname"],
        "entity_type": "TWEET"
    },
    "user_following": {
        "description": "Get users that a user follows",
        "primary_endpoint": "following.php",
        "parameters": ["screenname"],
        "entity_type": "USER"
    },
    "user_followers": {
        "description": "Get users that follow a user",
        "primary_endpoint": "followers.php",
        "parameters": ["screenname"],
        "entity_type": "USER"
    },
    "tweet_info": {
        "description": "Get information about a specific tweet",
        "primary_endpoint": "tweet.php",
        "parameters": ["id"],
        "entity_type": "TWEET"
    },
    "tweet_replies": {
        "description": "Get replies to a tweet",
        "primary_endpoint": "latest_replies.php",
        "parameters": ["id"],
        "entity_type": "TWEET"
    },
    "tweet_retweets": {
        "description": "Get users who retweeted a tweet",
        "primary_endpoint": "retweets.php",
        "parameters": ["id"],
        "entity_type": "USER"
    },
    "tweet_thread": {
        "description": "Get all tweets in a thread",
        "primary_endpoint": "tweet_thread.php",
        "parameters": ["id"],
        "entity_type": "TWEET"
    },
    "list_timeline": {
        "description": "Get tweets from a list",
        "primary_endpoint": "listtimeline.php",
        "parameters": ["list_id"],
        "entity_type": "TWEET"
    },
    "list_members": {
        "description": "Get members of a list",
        "primary_endpoint": "list_members.php",
        "parameters": ["list_id"],
        "entity_type": "USER"
    },
    "list_followers": {
        "description": "Get followers of a list",
        "primary_endpoint": "list_followers.php",
        "parameters": ["list_id"],
        "entity_type": "USER"
    },
    "space_info": {
        "description": "Get information about a space",
        "primary_endpoint": "spaces.php",
        "parameters": ["id"],
        "entity_type": "SPACE"
    }
}