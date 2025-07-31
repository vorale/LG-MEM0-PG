#!/usr/bin/env python3
"""
Robust telemetry disabling for Mem0 and PostHog

This module completely disables telemetry before any imports,
preventing initialization issues.
"""

import os
import sys
import warnings

# Set all telemetry environment variables before any imports
os.environ["MEM0_TELEMETRY"] = "false"
os.environ["POSTHOG_DISABLED"] = "true"
os.environ["POSTHOG_PERSONAL_API_KEY"] = ""
os.environ["MEM0_USER_ID"] = "disabled"

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

def disable_all_telemetry():
    """Completely disable all telemetry systems"""
    
    # Method 1: Mock the posthog module entirely
    class MockPostHog:
        def __init__(self, *args, **kwargs):
            pass
        
        def capture(self, *args, **kwargs):
            pass
        
        def identify(self, *args, **kwargs):
            pass
        
        def alias(self, *args, **kwargs):
            pass
        
        def group(self, *args, **kwargs):
            pass
        
        def page(self, *args, **kwargs):
            pass
        
        def screen(self, *args, **kwargs):
            pass
        
        def track(self, *args, **kwargs):
            pass
        
        def flush(self, *args, **kwargs):
            pass
        
        def shutdown(self, *args, **kwargs):
            pass
    
    class MockPostHogClient:
        def __init__(self, *args, **kwargs):
            pass
        
        def capture(self, *args, **kwargs):
            pass
    
    # Mock the entire posthog module
    class MockPostHogModule:
        Client = MockPostHogClient
        
        def __init__(self):
            pass
        
        def capture(self, *args, **kwargs):
            pass
        
        def identify(self, *args, **kwargs):
            pass
    
    # Replace posthog in sys.modules before it gets imported
    sys.modules['posthog'] = MockPostHogModule()
    sys.modules['posthog.client'] = MockPostHogModule()
    
    # Method 2: Mock mem0 telemetry functions
    def mock_capture_event(*args, **kwargs):
        pass
    
    def mock_telemetry_init(*args, **kwargs):
        pass
    
    # Try to replace mem0 telemetry if it's already imported
    try:
        import mem0.memory.telemetry
        mem0.memory.telemetry.capture_event = mock_capture_event
        print("✅ Mem0 telemetry disabled")
    except ImportError:
        pass
    
    print("✅ All telemetry systems disabled")

# Call the disable function immediately when this module is imported
disable_all_telemetry()

# Also make it available for explicit calling
__all__ = ['disable_all_telemetry']
