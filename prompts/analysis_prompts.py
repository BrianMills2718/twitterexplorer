# prompts/analysis_prompts.py

SATISFACTION_ANALYSIS_PROMPT = """
Analyze the quality and completeness of this Twitter investigation.

**Investigation Goal:** {original_query}
**Searches Conducted:** {search_count}
**Results Found:** {total_results}

**Search History:**
{search_summary}

**Assessment Criteria:**
1. **Coverage**: How thoroughly was the topic explored?
2. **Source Quality**: How credible and diverse were the sources found?
3. **Relevance**: How well do the findings address the original question?
4. **Completeness**: What important aspects might be missing?

Provide a satisfaction score (0-100%) and explain your reasoning.
"""

KNOWLEDGE_SYNTHESIS_PROMPT = """
Synthesize the accumulated knowledge from this investigation.

**Topic Investigated:** {topic}
**Key Findings:** {findings}
**Sources Found:** {sources}
**Contradictions Identified:** {contradictions}

**Synthesis Tasks:**
1. What is the overall picture that emerges?
2. What are the key insights and patterns?
3. How credible and reliable is the information found?
4. What are the main arguments or perspectives?
5. What questions remain unanswered?

Provide a comprehensive knowledge summary.
"""

RECOMMENDATION_PROMPT = """
Based on this investigation, what should be done next?

**Investigation Summary:** {summary}
**Gaps Identified:** {gaps}
**Effectiveness Patterns:** {patterns}

**Recommendation Categories:**
1. **Search Improvements**: Better terms, strategies, or approaches
2. **Platform Expansion**: Other sources that might have information
3. **Research Directions**: Specific aspects that need more investigation
4. **Verification Steps**: How to validate or cross-check findings

Provide actionable recommendations for continuing or concluding this research.
"""