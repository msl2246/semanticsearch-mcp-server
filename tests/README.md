# Test Suite

This directory contains test scripts for the Semantic Scholar MCP Server.

## Test Files

- `test_stdio_direct.py` - Direct stdio communication tests
- `test_stdio_tools.py` - Tool functionality tests via stdio
- `test_stdio_complete.py` - Complete MCP protocol flow tests
- `test_all_tools.py` - Individual tool testing
- `test_simple.py` - Simple functionality verification

## Running Tests

### stdio Mode Tests
```bash
# Set environment variable
export MCP_TRANSPORT=stdio

# Run individual tests
python3 tests/test_simple.py
python3 tests/test_stdio_complete.py
python3 tests/test_all_tools.py
```

### HTTP Mode Tests
```bash
# Set environment variable  
export MCP_TRANSPORT=streamable-http

# Run HTTP mode tests
python3 tests/test_simple.py
```

## Environment Variables Required

- `SEMANTIC_SCHOLAR_API_KEY` - Your Semantic Scholar API key
- `MCP_TRANSPORT` - Transport mode: "stdio" or "streamable-http"