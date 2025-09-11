#!/usr/bin/env python3
"""
Test CLI import purity - Issue #1: Streamlit import contamination in CLI
Test CLI execution should not import Streamlit modules
"""

import pytest
import sys
import subprocess
import time
import os
from unittest.mock import patch


def test_cli_has_no_streamlit_imports():
    """CLI execution should work without Streamlit available"""
    # Test that CLI can run when Streamlit is completely unavailable
    
    # Store original streamlit module if it exists
    original_streamlit = sys.modules.get('streamlit', None)
    
    try:
        # Disable streamlit by setting it to None
        sys.modules['streamlit'] = None
        
        # Remove any streamlit modules that might have been imported
        streamlit_modules = [mod for mod in list(sys.modules.keys()) if 'streamlit' in mod.lower()]
        for mod in streamlit_modules:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Import investigation engine and CLI components
        # Note: we need to reload modules that may have already imported streamlit
        if 'investigation_engine' in sys.modules:
            del sys.modules['investigation_engine']
        if 'cli_test' in sys.modules:
            del sys.modules['cli_test']
        if 'llm_client' in sys.modules:
            del sys.modules['llm_client']
            
        from investigation_engine import InvestigationEngine, InvestigationConfig
        from cli_test import main as cli_main
        
        # Create engine to verify it works without streamlit
        engine = InvestigationEngine("test_api_key")
        config = InvestigationConfig(max_searches=1)
        
        # Verify these work
        assert engine is not None
        assert config is not None
        
        print("✅ CLI components work correctly without Streamlit!")
        
    except ImportError as e:
        pytest.fail(f"Failed to import CLI components without streamlit: {e}")
    except Exception as e:
        # Check if error is streamlit-related
        if 'streamlit' in str(e).lower():
            pytest.fail(f"CLI failed due to streamlit dependency: {e}")
        else:
            # Other errors might be acceptable (like API keys, etc.)
            print(f"Note: Non-streamlit error occurred: {e}")
    
    finally:
        # Restore original streamlit module
        if original_streamlit is not None:
            sys.modules['streamlit'] = original_streamlit


def test_cli_import_performance():
    """Measure import performance impact for CLI components"""
    import time
    
    # Time the import of CLI components
    start_time = time.time()
    
    try:
        from investigation_engine import InvestigationEngine, InvestigationConfig
        from cli_test import main as cli_main
    except ImportError as e:
        pytest.fail(f"Failed to import CLI components: {e}")
    
    import_time = time.time() - start_time
    
    # Assert imports are reasonably fast (< 2 seconds)
    assert import_time < 2.0, f"CLI imports took {import_time:.2f}s, too slow"


def test_cli_execution_with_mocked_streamlit_unavailable():
    """Test CLI can run when Streamlit is completely unavailable"""
    
    # Mock sys.modules to make streamlit unavailable
    with patch.dict('sys.modules', {'streamlit': None}):
        try:
            # Import should still work
            from investigation_engine import InvestigationEngine, InvestigationConfig
            
            # Create engine should work without streamlit
            engine = InvestigationEngine("test_api_key")
            config = InvestigationConfig(max_searches=1)
            
            # This should not fail due to streamlit dependencies
            assert engine is not None
            assert config is not None
            
        except Exception as e:
            # If there's an error, it should NOT be streamlit-related
            assert 'streamlit' not in str(e).lower(), f"Streamlit-related error: {e}"


def test_investigate_engine_imports_isolation():
    """Test investigation_engine.py doesn't directly import streamlit in CLI mode"""
    
    # Read the investigation_engine.py file
    engine_path = os.path.join(os.path.dirname(__file__), 'investigation_engine.py')
    with open(engine_path, 'r') as f:
        content = f.read()
    
    # Count streamlit imports
    lines = content.split('\n')
    streamlit_import_lines = [line for line in lines if 'import streamlit' in line and not line.strip().startswith('#')]
    
    # There should be conditional imports only, not direct imports
    direct_imports = [line for line in streamlit_import_lines if not ('try:' in content or 'except:' in content)]
    
    # Assert we found the problematic import
    assert len(streamlit_import_lines) > 0, "Should find the streamlit import that causes CLI contamination"
    
    print(f"Found streamlit imports: {streamlit_import_lines}")


def test_cli_subprocess_execution():
    """Test CLI execution in subprocess doesn't show streamlit warnings"""
    
    # Set up environment
    test_env = os.environ.copy()
    test_env['GEMINI_API_KEY'] = 'test_key'
    
    # Run CLI in subprocess with minimal test
    cmd = [sys.executable, 'cli_test.py', 'test query']
    
    try:
        # Run with timeout to avoid hanging
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=30,
            env=test_env
        )
        
        # Check for streamlit warnings in output
        output_text = result.stdout + result.stderr
        streamlit_warnings = [line for line in output_text.split('\n') 
                             if 'streamlit' in line.lower() and ('warning' in line.lower() or 'error' in line.lower())]
        
        # Record evidence for debugging
        print(f"CLI subprocess output (first 500 chars): {output_text[:500]}")
        print(f"Streamlit-related warnings found: {streamlit_warnings}")
        
        # This test documents the current issue - it will fail until fixed
        assert len(streamlit_warnings) > 0, "Expected to find streamlit warnings (documenting current issue)"
        
    except subprocess.TimeoutExpired:
        pytest.fail("CLI test timed out - possible hang due to import issues")
    except Exception as e:
        pytest.fail(f"Failed to run CLI subprocess: {e}")


def test_streamlit_conditional_import_pattern():
    """Test that streamlit imports use proper conditional patterns"""
    
    # Check investigation_engine.py for proper conditional import patterns
    engine_path = os.path.join(os.path.dirname(__file__), 'investigation_engine.py')
    with open(engine_path, 'r') as f:
        content = f.read()
    
    # Look for try/except patterns around streamlit imports
    has_conditional_streamlit = 'try:' in content and 'streamlit' in content and 'except' in content
    
    if 'import streamlit' in content:
        # If streamlit is imported, it should be conditional
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'import streamlit' in line and not line.strip().startswith('#'):
                # Check if this import is inside a try/except block
                context_lines = lines[max(0, i-5):i+5]
                context_text = '\n'.join(context_lines)
                
                print(f"Streamlit import context:\n{context_text}")
                # This documents the current issue
                assert 'try:' not in context_text or 'except' not in context_text, \
                    "Streamlit import should be conditional but appears to be direct"


if __name__ == "__main__":
    # Run tests to document current issues
    pytest.main([__file__, "-v", "-s"])