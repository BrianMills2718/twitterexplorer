#!/usr/bin/env python3
"""
Debug script to test bridge integration
"""

import os
os.environ['DISABLE_STREAMLIT'] = '1'

from investigation_engine import InvestigationEngine, InvestigationConfig

def test_bridge_integration():
    """Test that the bridge integration is working"""
    print("Testing bridge integration...")
    
    # Set up API keys
    rapidapi_key = '7501a19221mshf1eb289b88dc8acp1d30e6jsn04f6eab32db3'
    os.environ['GEMINI_API_KEY'] = 'AIzaSyAhwSgnnZrVbTECNCXDp1nODEVh3rtoTq8'
    os.environ['OPENAI_API_KEY'] = 'REMOVED_OPENAI_API_KEY'

    # Create engine
    print("Creating investigation engine...")
    engine = InvestigationEngine.from_config(api_key=rapidapi_key, provider='openai')
    
    print(f"Engine created. Graph mode: {engine.graph_mode}")
    
    # Bridge is only created during investigation, not at engine init
    config = InvestigationConfig(
        max_searches=1,  # Just start the investigation to create bridge
        satisfaction_threshold=0.1
    )
    
    query = 'test bridge creation'
    print(f"Starting investigation to create bridge: {query}")
    
    try:
        # This should create the bridge
        result = engine.conduct_investigation(query, config)
        
        print(f"\nAfter investigation start:")
        print(f"Bridge available: {hasattr(engine, 'integration_bridge')}")
        
        if hasattr(engine, 'integration_bridge'):
            print(f"Bridge instance: {engine.integration_bridge}")
            print(f"Bridge type: {type(engine.integration_bridge)}")
            
            if hasattr(engine, 'insight_synthesizer'):
                print(f"Insight synthesizer exists: {engine.insight_synthesizer is not None}")
                if engine.insight_synthesizer:
                    print(f"Insight synthesizer bridge: {engine.insight_synthesizer.bridge}")
                    print(f"Bridge properly wired: {engine.insight_synthesizer.bridge is engine.integration_bridge}")
            else:
                print("No insight synthesizer found!")
        else:
            print("No bridge found!")
            
        # Check bridge components
        if hasattr(engine, 'integration_bridge') and engine.integration_bridge:
            bridge = engine.integration_bridge
            print(f"Bridge coordinator: {bridge.coordinator}")
            print(f"Bridge graph: {bridge.graph}")
            print(f"Bridge coordinator has detect_emergent_questions: {hasattr(bridge.coordinator, 'detect_emergent_questions')}")
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        import traceback
        traceback.print_exc()
    
if __name__ == "__main__":
    test_bridge_integration()