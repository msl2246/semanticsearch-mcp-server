#!/usr/bin/env python3
import json
import subprocess
import os

def test_mcp_complete_flow():
    """Test complete MCP protocol flow with proper initialization"""
    env = os.environ.copy()
    env["SEMANTIC_SCHOLAR_API_KEY"] = "SGEs5LaI8C5vd1mWLvi42aWCK35gZR5ak7bkbNC0"
    
    process = subprocess.Popen(
        ["uv", "run", "python", "server_stdio.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    # Proper MCP initialization sequence
    messages = [
        # 1. Initialize
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        },
        # 2. Initialized notification (no response expected)
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        },
        # 3. List tools
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        # 4. List resources
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
            "params": {}
        },
        # 5. Test search_papers tool
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "search_papers",
                "arguments": {
                    "query": "artificial intelligence",
                    "limit": 2
                }
            }
        }
    ]
    
    input_data = "\n".join([json.dumps(msg) for msg in messages]) + "\n"
    
    print(f"Sending {len(messages)} messages:")
    for i, msg in enumerate(messages, 1):
        method = msg.get('method', 'unknown')
        print(f"{i}. {method}")
    
    try:
        stdout, stderr = process.communicate(input=input_data, timeout=30)
        print(f"\n=== STDOUT ===")
        # Parse and pretty print each response
        for line in stdout.strip().split('\n'):
            if line.strip():
                try:
                    response = json.loads(line)
                    print(json.dumps(response, indent=2))
                    print("---")
                except json.JSONDecodeError:
                    print(f"Raw: {line}")
        
        if stderr:
            print(f"\n=== STDERR ===\n{stderr}")
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("Timeout expired")

if __name__ == "__main__":
    test_mcp_complete_flow()