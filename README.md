# Semantic Scholar MCP Server

A comprehensive Model Context Protocol (MCP) server that provides access to the Semantic Scholar Academic Graph API with streaming HTTP support.

## 🚀 Installation & Quick Start

### Recommended: One-time Installation with uv tool

```bash
# Install once from GitHub
uv tool install git+https://github.com/msl2246/semanticsearch-mcp-server

# Run with your API key
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here semanticsearch-mcp-server
```

### Alternative: Direct Execution with uvx

```bash
# Run directly without installation (downloads each time)
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here uvx --from git+https://github.com/msl2246/semanticsearch-mcp-server semanticsearch-mcp-server
```

## 🚀 Advanced Usage Examples

### Basic Network Mode with API Key
```bash
# After installation via uv tool install
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here semanticsearch-mcp-server
```

### External Access Mode
```bash
# Run for external access (accessible from other machines)
MCP_SERVER_HOST=0.0.0.0 \
MCP_SERVER_PORT=5002 \
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here \
semanticsearch-mcp-server
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
semanticsearch-mcp-server
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

First, install the tool:
```bash
uv tool install git+https://github.com/msl2246/semanticsearch-mcp-server
```

Then run in stdio mode:
```bash
export MCP_TRANSPORT=stdio
semanticsearch-mcp-server
```

#### Claude Desktop Configuration

To integrate with Claude Desktop, add this to your `claude_desktop_config.json`:

**Option 1: Using installed tool (Recommended)**
```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "semanticsearch-mcp-server",
      "env": {
        "MCP_TRANSPORT": "stdio",
        "SEMANTIC_SCHOLAR_API_KEY": "your_api_key_here",
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Option 2: Using uvx (Alternative)**
```json
{
  "mcpServers": {
    "semantic-scholar": {
      "command": "uvx",
      "args": [
        "--from", 
        "git+https://github.com/msl2246/semanticsearch-mcp-server", 
        "semanticsearch-mcp-server"
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

### 2. HTTP Mode (For Network Access)

First, install the tool:
```bash
uv tool install git+https://github.com/msl2246/semanticsearch-mcp-server
```

Then run in HTTP mode:
```bash
export MCP_TRANSPORT=streamable-http  # Default mode
semanticsearch-mcp-server
# Server runs on http://localhost:5002
```

### Development Mode with MCP Inspector

For development, you can use the source code directly:
```bash
# Clone the repository for development
git clone https://github.com/msl2246/semanticsearch-mcp-server
cd semanticsearch-mcp-server

# Install dependencies
uv sync

# Run with MCP Inspector
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
semanticsearch-mcp-server

# Server will be available at:
# http://your-ip-address:5002/mcp
# http://your-ip-address:5002/sse
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

## 🔧 Tool Management

### Update to Latest Version
```bash
# Update the installed tool
uv tool upgrade semanticsearch-mcp-server
```

### Uninstall
```bash
# Remove the installed tool
uv tool uninstall semanticsearch-mcp-server
```

### List Installed Tools
```bash
# Check installed uv tools
uv tool list
```

### Reinstall (if needed)
```bash
# Uninstall and reinstall
uv tool uninstall semanticsearch-mcp-server
uv tool install git+https://github.com/msl2246/semanticsearch-mcp-server
```