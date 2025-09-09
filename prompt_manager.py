"""Isolated prompt management without circular dependencies"""
from typing import Tuple

class PromptManager:
    """Manages prompt templates without circular dependencies"""
    
    def __init__(self):
        self._cached_prompts = {}
    
    def load_prompts(self) -> Tuple[str, str]:
        """Load prompts with proper error handling"""
        try:
            # Try to load from prompts folder WITHOUT causing circular import
            import os
            import sys
            # Temporarily add to path if needed
            prompts_path = os.path.join(os.path.dirname(__file__), 'prompts')
            if os.path.exists(prompts_path):
                # Load directly from file to avoid import issues
                prompts_file = os.path.join(prompts_path, 'investigation_prompts.py')
                if os.path.exists(prompts_file):
                    with open(prompts_file, 'r') as f:
                        content = f.read()
                        # Extract prompts using simple parsing
                        if 'PLANNER_SYSTEM_PROMPT' in content:
                            return self._extract_prompts_from_content(content)
            
            # Fallback to importing if file reading fails
            from twitterexplorer.prompts.investigation_prompts import (
                PLANNER_SYSTEM_PROMPT, 
                SUMMARIZER_SYSTEM_PROMPT
            )
            return PLANNER_SYSTEM_PROMPT, SUMMARIZER_SYSTEM_PROMPT
        except (ImportError, FileNotFoundError):
            return self._get_fallback_prompts()
    
    def _extract_prompts_from_content(self, content: str) -> Tuple[str, str]:
        """Extract prompts from file content"""
        # Simple extraction logic
        planner_start = content.find('PLANNER_SYSTEM_PROMPT = """')
        planner_end = content.find('"""', planner_start + 30)
        
        summarizer_start = content.find('SUMMARIZER_SYSTEM_PROMPT = """')
        summarizer_end = content.find('"""', summarizer_start + 30)
        
        if planner_start > 0 and summarizer_start > 0:
            planner = content[planner_start+28:planner_end]
            summarizer = content[summarizer_start+31:summarizer_end]
            return planner, summarizer
        
        return self._get_fallback_prompts()
    
    def _get_fallback_prompts(self) -> Tuple[str, str]:
        """Fallback prompts that don't depend on any modules"""
        planner = "You are an intelligent Twitter research strategist. Design effective searches."
        summarizer = "Analyze the Twitter investigation results and provide insights."
        return planner, summarizer

# Global instance
prompt_manager = PromptManager()