#!/usr/bin/env python3
import json
import subprocess
import os

def test_mcp_initialize():
    """Test MCP initialize protocol"""
    env = os.environ.copy()
    env["SEMANTIC_SCHOLAR_API_KEY"] = "SGEs5LaI8C5vd1mWLvi42aWCK35gZR5ak7bkbNC0"
    
    # Initialize message
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
    
    process = subprocess.Popen(
        ["uv", "run", "python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    input_data = json.dumps(init_msg) + "\n"
    print(f"Sending initialize: {input_data.strip()}")
    
    try:
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        print(f"STDOUT: {stdout}")
        if stderr:
            print(f"STDERR: {stderr}")
    except subprocess.TimeoutExpired:
        process.kill()
        print("Timeout expired")

def test_mcp_tools_list():
    """Test MCP tools/list"""
    env = os.environ.copy()
    env["SEMANTIC_SCHOLAR_API_KEY"] = "SGEs5LaI8C5vd1mWLvi42aWCK35gZR5ak7bkbNC0"
    
    tools_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    process = subprocess.Popen(
        ["uv", "run", "python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    input_data = json.dumps(tools_msg) + "\n"
    print(f"Sending tools/list: {input_data.strip()}")
    
    try:
        stdout, stderr = process.communicate(input=input_data, timeout=10)
        print(f"STDOUT: {stdout}")
        if stderr:
            print(f"STDERR: {stderr}")
    except subprocess.TimeoutExpired:
        process.kill()
        print("Timeout expired")

if __name__ == "__main__":
    print("=== Testing MCP Initialize ===")
    test_mcp_initialize()
    print("\n=== Testing MCP Tools List ===")
    test_mcp_tools_list()