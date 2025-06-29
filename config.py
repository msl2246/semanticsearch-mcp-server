"""
Configuration management for Semantic Scholar MCP Server.
All settings are loaded from environment variables or .env file.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Semantic Scholar API settings
    semantic_scholar_api_key: str = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
    semantic_scholar_base_url: str = os.getenv(
        "SEMANTIC_SCHOLAR_BASE_URL", "https://api.semanticscholar.org"
    )

    # MCP Server settings
    mcp_server_name: str = os.getenv("MCP_SERVER_NAME", "SemanticSearch")
    mcp_server_host: str = os.getenv("MCP_SERVER_HOST", "localhost")
    mcp_server_port: int = int(os.getenv("MCP_SERVER_PORT", "5002"))
    mcp_log_level: str = os.getenv("MCP_LOG_LEVEL", "INFO")

    # Rate limiting and HTTP settings
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    retry_delay: float = float(os.getenv("RETRY_DELAY", "1.0"))

    # Transport mode settings
    mcp_transport: str = os.getenv("MCP_TRANSPORT", "streamable-http")  # "stdio" or "streamable-http"

    model_config = ConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()


def get_semantic_scholar_headers() -> dict[str, str]:
    """Get headers for Semantic Scholar API requests."""
    headers = {
        "User-Agent": f"{settings.mcp_server_name}/1.0",
        "Accept": "application/json",
    }

    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key

    return headers


def get_rate_limit_delay() -> float:
    """Get appropriate delay between requests based on API key availability."""
    if settings.semantic_scholar_api_key:
        # With API key: 1 request per second
        return 1.0
    else:
        # Without API key: 100 requests per 5 minutes = 3 second intervals
        return 3.0


def is_stdio_mode() -> bool:
    """Check if server should run in stdio mode."""
    return settings.mcp_transport.lower() == "stdio"


def is_http_mode() -> bool:
    """Check if server should run in HTTP mode."""
    return settings.mcp_transport.lower() in ["streamable-http", "http"]


def get_transport_mode() -> str:
    """Get the appropriate transport mode string."""
    if is_stdio_mode():
        return "stdio"
    else:
        return "streamable-http"
