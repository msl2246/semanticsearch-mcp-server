#!/usr/bin/env python3
import json
import subprocess
import os

def test_individual_tools():
    """Test each MCP tool individually"""
    env = os.environ.copy()
    env["SEMANTIC_SCHOLAR_API_KEY"] = "SGEs5LaI8C5vd1mWLvi42aWCK35gZR5ak7bkbNC0"
    
    # Test cases for different tools
    test_cases = [
        {
            "name": "search_papers",
            "description": "Search for machine learning papers",
            "arguments": {
                "query": "neural networks",
                "limit": 3,
                "fields": "title,year,citationCount"
            }
        },
        {
            "name": "get_paper_details", 
            "description": "Get details for a specific paper",
            "arguments": {
                "paper_id": "649def34f8be52c8b66281af98ae884c09aef38b",
                "fields": "title,abstract,year,authors"
            }
        },
        {
            "name": "search_authors",
            "description": "Search for authors",
            "arguments": {
                "query": "Geoffrey Hinton",
                "limit": 2,
                "fields": "name,affiliations,hIndex"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*50}")
        print(f"Test {i}: {test_case['description']}")
        print(f"Tool: {test_case['name']}")
        print(f"{'='*50}")
        
        process = subprocess.Popen(
            ["uv", "run", "python", "server_stdio.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        messages = [
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
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {}
            },
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": test_case["name"],
                    "arguments": test_case["arguments"]
                }
            }
        ]
        
        input_data = "\n".join([json.dumps(msg) for msg in messages]) + "\n"
        
        try:
            stdout, stderr = process.communicate(input=input_data, timeout=20)
            
            print(f"Arguments: {test_case['arguments']}")
            
            # Parse and display results
            lines = stdout.strip().split('\n')
            for line in lines:
                if line.strip():
                    try:
                        response = json.loads(line)
                        if response.get('id') == 2:  # Tool call response
                            result = response.get('result', {})
                            if 'result' in result:
                                # Parse the JSON result from tool
                                tool_result = json.loads(result['result'])
                                print(f"Success: {json.dumps(tool_result, indent=2)[:500]}...")
                            elif 'error' in response:
                                print(f"Error: {response['error']}")
                    except json.JSONDecodeError:
                        continue
            
            if stderr and "INFO:" not in stderr:
                print(f"Warnings/Errors: {stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            process.kill()
            print("Timeout expired")

if __name__ == "__main__":
    test_individual_tools()