# Semantic Scholar MCP Server

A comprehensive Model Context Protocol (MCP) server that provides access to the Semantic Scholar Academic Graph API with streaming HTTP support.

## 🚀 Quick Start

```bash
# Install and run directly
uvx --from git+https://github.com/msl2246/semanticsearch-mcp-server semantic-scholar-mcp
```

## 🔧 Configuration

### Environment Variables
```bash
# Required: Get your API key from https://www.semanticscholar.org/product/api
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# Server Configuration
MCP_SERVER_HOST=localhost          # Use 0.0.0.0 for external access
MCP_SERVER_PORT=5002              # Server port
MCP_LOG_LEVEL=INFO                # Logging level

# API Settings
SEMANTIC_SCHOLAR_BASE_URL=https://api.semanticscholar.org
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=1
```

## 🎯 Usage Modes

The server supports two transport modes via the `MCP_TRANSPORT` environment variable:

### 1. stdio Mode (For Claude Desktop Integration)
```bash
export MCP_TRANSPORT=stdio
uv run python server.py
```

### 2. HTTP Mode (For Network Access)
```bash
export MCP_TRANSPORT=streamable-http  # Default mode
uv run python server.py
# Server runs on http://localhost:5002
```

### Development Mode with MCP Inspector
```bash
uv run mcp dev server.py
# Server runs at http://localhost:6274 with MCP Inspector
```

## 🌐 Server Endpoints

### HTTP Streaming Endpoints
- **Base URL**: `http://{HOST}:{PORT}`
- **Streaming HTTP**: `http://localhost:5002/mcp` (default)
- **SSE Endpoint**: `http://localhost:5002/sse`
- **Health Check**: `http://localhost:5002/health`

### External Access Configuration (HTTP Mode Only)
```bash
# For external access (e.g., from other machines)
export MCP_TRANSPORT=streamable-http
export MCP_SERVER_HOST=0.0.0.0
export MCP_SERVER_PORT=5002
uv run python server.py

# Server will be available at:
# http://your-ip-address:5002/mcp
# http://your-ip-address:5002/sse
```

### Development with MCP Inspector
```bash
uv run mcp dev server.py
# Access at: http://localhost:6274
# Inspector token will be displayed in console
```

## 🛠️ Features

> **Note**: This server uses FastMCP with native streaming HTTP support. The underlying HTTP server is managed automatically by the MCP framework - no additional server setup required.

### 8 MCP Tools Available
1. **search_papers** - Search academic papers with advanced filtering
2. **get_paper_details** - Get detailed information about a specific paper
3. **get_paper_authors** - Get authors of a specific paper
4. **get_paper_citations** - Get citations of a specific paper
5. **get_paper_references** - Get references of a specific paper
6. **search_authors** - Search for authors
7. **get_author_details** - Get detailed author information
8. **get_author_papers** - Get papers by a specific author

### 2 Resources Available
- **semantic-scholar://api-info** - Current API configuration and status
- **semantic-scholar://available-fields** - Available fields for API requests

### 3 Prompts Available
- **paper_search_prompt** - Generate comprehensive paper search strategies
- **paper_analysis_prompt** - Generate paper analysis workflows
- **author_research_prompt** - Generate author research workflows

## 📊 API Rate Limits

The server automatically handles rate limits:
- **With API Key**: 1 request per second on all endpoints
- **Without API KEY** : depends on semanticsearch api response (You may adjust RETRY_DELAY env value)


**Verify server is running:**
```bash
curl http://localhost:5002/health
curl http://localhost:5002/mcp
```

## 🔒 Security Considerations

- **API Key Protection**: Never commit API keys to version control
- **Host Binding**: Use `localhost` for local-only access, `0.0.0.0` for external access
- **Firewall**: Configure firewall rules for external access
- **HTTPS**: Use reverse proxy (nginx) for HTTPS in production

## 📚 Configuration Reference

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `SEMANTIC_SCHOLAR_API_KEY` | API key for Semantic Scholar | "apikey" | Your API key |
| `SEMANTIC_SCHOLAR_BASE_URL` | API base URL | "https://api.semanticscholar.org" | API endpoint |
| `MCP_SERVER_NAME` | Server name | "SemanticSearch" | Any string |
| `MCP_TRANSPORT` | Transport mode | "streamable-http" | "stdio", "streamable-http" |
| `MCP_SERVER_HOST` | Bind address (HTTP mode only) | "localhost" | "localhost", "0.0.0.0" |
| `MCP_SERVER_PORT` | Server port (HTTP mode only) | 5002 | 1024-65535 |
| `MCP_LOG_LEVEL` | Logging level | "INFO" | "DEBUG", "INFO", "WARNING", "ERROR" |
| `REQUEST_TIMEOUT` | HTTP timeout | 30 | Seconds |
| `MAX_RETRIES` | Retry attempts | 3 | Number |
| `RETRY_DELAY` | Retry delay | 1.0 | Seconds |


## 🧪 Testing

The test suite is located in the `tests/` directory and supports both transport modes.

### stdio Mode Tests
```bash
export MCP_TRANSPORT=stdio
export SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# Run individual tests
python3 tests/test_simple.py
python3 tests/test_stdio_complete.py
python3 tests/test_all_tools.py
```

### HTTP Mode Tests
```bash
export MCP_TRANSPORT=streamable-http
export SEMANTIC_SCHOLAR_API_KEY=your_api_key_here

# Run HTTP mode tests
python3 tests/test_simple.py
```
