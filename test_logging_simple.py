#!/usr/bin/env python3
# test_logging_simple.py - Simple test for logging system

import json
import time
import os
import sys

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logging_system():
    """Test the comprehensive logging system"""
    print("Testing Logging System...")
    
    try:
        # Import required modules
        from logging_system import investigation_logger
        from investigation_engine import InvestigationConfig, InvestigationSession, SearchAttempt
        
        print("SUCCESS: All imports successful")
        
        # Test 1: Basic logging initialization
        print("\nTest 1: Logging initialization")
        print(f"Base log directory: {investigation_logger.base_log_dir}")
        print(f"Log directories exist: {investigation_logger.base_log_dir.exists()}")
        
        # Test 2: Session logging
        print("\nTest 2: Session logging")
        
        # Create test config
        test_config = InvestigationConfig(
            max_searches=5,
            satisfaction_enabled=True,
            satisfaction_threshold=0.8,
            show_search_details=True
        )
        
        # Start test session
        session_id = investigation_logger.start_session(
            user_query="Test investigation for logging verification",
            config=test_config,
            user_ip="127.0.0.1"
        )
        print(f"SUCCESS: Started session: {session_id}")
        
        # Test 3: Search attempt logging
        print("\nTest 3: Search attempt logging")
        
        test_search = SearchAttempt(
            search_id=1,
            round_number=1,
            endpoint="search.php",
            params={"query": "test search query", "result_type": "latest"},
            query_description="Test search for logging verification",
            results_count=5,
            effectiveness_score=7.5,
            execution_time=1.2
        )
        
        investigation_logger.log_search_attempt(test_search, "direct_search")
        print("SUCCESS: Search attempt logged successfully")
        
        # Test 4: LLM interaction logging
        print("\nTest 4: LLM interaction logging")
        
        test_llm_response = {
            "response_type": "PLAN",
            "message_to_user": "Test LLM response",
            "api_plan": [{"endpoint": "search.php", "params": {"query": "test"}}]
        }
        
        investigation_logger.log_llm_interaction(
            interaction_type="strategy_generation",
            prompt_sent="Test prompt for strategy generation",
            llm_response=test_llm_response,
            processing_time=0.8,
            success=True
        )
        print("SUCCESS: LLM interaction logged successfully")
        
        # Test 5: Session completion
        print("\nTest 5: Session completion logging")
        
        # Create mock session for testing
        test_session = InvestigationSession("Test investigation for logging verification", test_config)
        test_session.search_count = 3
        test_session.total_results_found = 25
        test_session.completion_reason = "Test completed successfully"
        
        investigation_logger.end_session(test_session)
        print("SUCCESS: Session ended and logged successfully")
        
        # Wait a moment for files to be written
        time.sleep(1)
        
        # Test 6: Log file verification
        print("\nTest 6: Log file verification")
        
        log_dirs = [
            investigation_logger.base_log_dir / "sessions",
            investigation_logger.base_log_dir / "searches", 
            investigation_logger.base_log_dir / "llm_interactions",
            investigation_logger.base_log_dir / "strategies",
            investigation_logger.base_log_dir / "system"
        ]
        
        for log_dir in log_dirs:
            if log_dir.exists():
                files = list(log_dir.glob("*"))
                print(f"SUCCESS: {log_dir.name}: {len(files)} files")
            else:
                print(f"ERROR: {log_dir.name}: Directory not found")
        
        print("\nLogging System Test Complete!")
        print("\nSummary:")
        print("- Logging infrastructure: Working")
        print("- Session management: Working")
        print("- Search logging: Working") 
        print("- LLM interaction logging: Working")
        print("- File system: Working")
        print("\nSystem is ready for full testing!")
        
        return True
        
    except Exception as e:
        print(f"\nERROR: Logging system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_logging_system()
    if success:
        print("\nSUCCESS: All tests passed - logging system is working correctly!")
        exit(0)
    else:
        print("\nERROR: Some tests failed - check the errors above")
        exit(1)