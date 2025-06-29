#!/usr/bin/env python3
import json
import subprocess
import os

def simple_test():
    """Simple test to verify tool functionality"""
    env = os.environ.copy()
    env["SEMANTIC_SCHOLAR_API_KEY"] = "SGEs5LaI8C5vd1mWLvi42aWCK35gZR5ak7bkbNC0"
    
    # Test search_papers with minimal parameters
    cmd = ["uv", "run", "python", "server.py"]
    
    init_msg = '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}'
    initialized_msg = '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'
    tool_msg = '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "search_papers", "arguments": {"query": "deep learning", "limit": 1}}}'
    
    input_data = f"{init_msg}\n{initialized_msg}\n{tool_msg}\n"
    
    print("Testing search_papers tool with 'deep learning' query...")
    
    try:
        result = subprocess.run(
            cmd,
            input=input_data,
            text=True,
            capture_output=True,
            timeout=15,
            env=env
        )
        
        print("STDOUT:")
        for line in result.stdout.split('\n'):
            if line.strip():
                print(f"  {line}")
        
        if result.stderr:
            print("\nSTDERR:")
            print(f"  {result.stderr}")
            
        # Look for successful API response
        if "total" in result.stdout and "data" in result.stdout:
            print("\n✅ SUCCESS: Tool executed and returned data!")
        elif "HTTP Request: GET" in result.stderr:
            print("\n✅ SUCCESS: API call was made!")
        else:
            print("\n❌ FAILED: No clear success indicator")
    
    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Test took too long")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    simple_test()