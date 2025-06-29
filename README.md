# Semantic Scholar MCP Server

A comprehensive Model Context Protocol (MCP) server that provides access to the Semantic Scholar Academic Graph API with streaming HTTP support.

## 🚀 Quick Start

```bash
# Install and run directly
uvx --from git+https://github.com/msl2246/semanticsearch-mcp-server semantic-scholar-mcp
```

## 🚀 Network Mode Quick Start

Run the server directly from GitHub with your API key and custom settings:

### Basic Network Mode with API Key
```bash
# Run with your API key in network mode (default)
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here uvx --from git+https://github.com/msl2246/semanticsearch-mcp-server semantic-scholar-mcp
```

### External Access Mode
```bash
# Run for external access (accessible from other machines)
MCP_SERVER_HOST=0.0.0.0 \
MCP_SERVER_PORT=5002 \
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here \
uvx --from git+https://github.com/msl2246/semanticsearch-mcp-server semantic-scholar-mcp
```

### Custom Configuration
```bash
# Run with custom settings and debug logging
MCP_TRANSPORT=streamable-http \
MCP_SERVER_HOST=0.0.0.0 \
MCP_SERVER_PORT=8080 \
MCP_LOG_LEVEL=DEBUG \
REQUEST_TIMEOUT=60 \
MAX_RETRIES=5 \
RETRY_DELAY=2 \
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here \
uvx --from git+https://github.com/msl2246/semanticsearch-mcp-server semantic-scholar-mcp
```

### Quick Test Commands
```bash
# After starting the server, test these endpoints:

curl http://localhost:5002/mcp

# For external access:
curl http://your-ip-address:5002/mcp
```

> 💡 **Tip**: Get your API key from [Semantic Scholar API](https://www.semanticscholar.org/product/api) to increase rate limits.

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

#### Claude Desktop Configuration or another MCP Client
To integrate with Claude Desktop, add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "uvx",
      "args": [
        "--from", 
        "git+https://github.com/msl2246/semanticsearch-mcp-server", 
        "semantic-scholar-mcp"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "SEMANTIC_SCHOLAR_API_KEY": "your_api_key_here",
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

> 📍 **Location of claude_desktop_config.json**:
> - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
> - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
> - **Linux**: `~/.config/claude/claude_desktop_config.json`

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