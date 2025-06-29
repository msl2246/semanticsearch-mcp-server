#!/usr/bin/env python3
import json
import subprocess
import os

def test_mcp_tools_complete():
    """Test complete MCP protocol with stdio server"""
    env = os.environ.copy()
    env["SEMANTIC_SCHOLAR_API_KEY"] = "SGEs5LaI8C5vd1mWLvi42aWCK35gZR5ak7bkbNC0"
    
    # Test sequence: initialize -> tools/list -> call tool
    process = subprocess.Popen(
        ["uv", "run", "python", "server_stdio.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    # Initialize
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    
    # Tools list
    tools_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    # Test search_papers tool
    search_msg = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "search_papers",
            "arguments": {
                "query": "machine learning",
                "limit": 2
            }
        }
    }
    
    messages = [init_msg, tools_msg, search_msg]
    input_data = "\n".join([json.dumps(msg) for msg in messages]) + "\n"
    
    print(f"Sending {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        print(f"{i}. {msg['method']}")
    
    try:
        stdout, stderr = process.communicate(input=input_data, timeout=20)
        print(f"\n=== STDOUT ===\n{stdout}")
        if stderr:
            print(f"\n=== STDERR ===\n{stderr}")
    except subprocess.TimeoutExpired:
        process.kill()
        print("Timeout expired")

if __name__ == "__main__":
    test_mcp_tools_complete()