# prompts/strategy_prompts.py

ADAPTIVE_STRATEGY_PROMPT = """
You are designing the next round of searches in an ongoing Twitter investigation.

**ORIGINAL QUERY:** {original_query}

**INVESTIGATION CONTEXT:**
{investigation_context}

**Your Task:**
Based on what has been tried and what was found (or not found), design the next strategic searches.

**Strategic Guidelines:**

**For Early Rounds (Few Searches Done):**
- Start with the most obvious, direct searches
- Try basic variations of key terms
- Establish whether the topic exists in the Twitter discourse

**For Failed Searches (No Results Found):**
- Try alternative spellings or name variations
- Broaden the search scope to find related discussions
- Consider if the topic might be known by different terms

**For Successful Searches (Results Found):**
- Build on what worked by trying variations
- Drill deeper into promising directions
- Follow the language and terminology you found

**For Mixed Results:**
- Continue the most effective approaches
- Try to bridge gaps between successful searches
- Explore different angles or perspectives

**Search Design Principles:**
- Use natural language that real Twitter users would employ
- Consider the actual communities and voices involved
- Think about how people really discuss these topics
- Balance breadth and depth appropriately

Design 2-4 searches that intelligently build on previous learning and move the investigation forward.
"""

FALLBACK_STRATEGY_PROMPT = """
Create a basic search strategy for: {query}

Start with fundamental searches:
1. Basic name/topic search
2. Common variations or alternative spellings
3. Related context searches
4. Community-specific searches if applicable

Keep searches simple and direct for this fallback approach.
"""