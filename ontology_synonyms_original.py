# ontology_synonyms.py

# We maintain two dictionaries for clarity.
USER_SYNONYMS = {
    "user_id": ["id", "user_id", "id_str", "rest_id"],
    "rest_id": ["rest_id"],  # sometimes repeated, but let's keep it distinct
    "screen_name": ["screen_name", "profile"],
    "name": ["name"],
    "description": ["description", "desc"],
    "location": ["location"],
    "legacy_verified": [],
    "blue_verified": ["blue_verified", "is_blue_verified"],
    "business_account": ["business_account"],
    "protected": ["protected"],
    "avatar": ["avatar", "profile_image", "image"],
    "header_image": ["header_image"],
    "created_at": ["created_at"],
    "followers_count": ["followers_count"],
    "following_count": ["friends", "friends_count"],
    "statuses_count": ["statuses_count"],
    "media_count": ["media_count"],
    "sub_count": ["sub_count"],
    "website": ["website"],
    "lang": ["lang"]
}

TWEET_SYNONYMS = {
    "tweet_id": ["id", "tweet_id", "id_str"],
    "text": ["text"],
    "display_text": ["display_text"],
    "created_at": ["created_at"],
    "conversation_id": ["conversation_id"],
    "lang": ["lang"],
    "view_count": ["views"],
    "reply_count": ["replies", "reply_count"],
    "retweet_count": ["retweets"],
    "quote_count": ["quotes"],
    "favorite_count": ["likes", "favorites"],
    "bookmark_count": ["bookmarks"],
    "in_reply_to_status_id": ["in_reply_to_status_id_str"],
    "in_reply_to_user_id": ["in_reply_to_user_id_str"],
    "in_reply_to_screen_name": ["in_reply_to_screen_name"],
    "possibly_sensitive": ["sensitive"],
    "media": ["media"],
    "hashtags": ["hashtags"],
    "urls": ["urls"]
}

# If you also want synonyms for List, Space, etc., you can create 
# LIST_SYNONYMS, SPACE_SYNONYMS, etc., similarly, 
# or keep them separate if you prefer.
