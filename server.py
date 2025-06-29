"""
Semantic Scholar MCP Server with Streaming HTTP Support.

This server provides access to the Semantic Scholar Academic Graph API
through MCP (Model Context Protocol) with streaming HTTP transport.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any
import httpx
from mcp.server.fastmcp import FastMCP, Context
from config import settings, get_semantic_scholar_headers, get_rate_limit_delay, is_stdio_mode, is_http_mode, get_transport_mode

# Configure logging
logging.basicConfig(level=getattr(logging, settings.mcp_log_level))
logger = logging.getLogger(__name__)

# Create FastMCP server with transport mode-specific configuration
if is_http_mode():
    # HTTP mode with stateless support for multi-node environments
    mcp = FastMCP(
        name=settings.mcp_server_name,
        stateless_http=True,  # Enable stateless HTTP for multi-node environments
        json_response=True    # Enable JSON responses for better client compatibility
    )
else:
    # stdio mode with minimal configuration
    mcp = FastMCP(
        name=settings.mcp_server_name
    )

# HTTP client for API requests
http_client: Optional[httpx.AsyncClient] = None


async def init_http_client():
    """Initialize the HTTP client with proper configuration."""
    global http_client
    if http_client is None:
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout),
            headers=get_semantic_scholar_headers(),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return http_client


async def close_http_client():
    """Close the HTTP client."""
    global http_client
    if http_client:
        await http_client.aclose()
        http_client = None


async def make_api_request(
    endpoint: str, params: Optional[Dict[str, Any]] = None, method: str = "GET"
) -> Dict[str, Any]:
    """
    Make a request to the Semantic Scholar API with rate limiting and error handling.

    Args:
        endpoint: API endpoint path
        params: Query parameters
        method: HTTP method

    Returns:
        JSON response data

    Raises:
        httpx.HTTPError: If request fails
    """
    client = await init_http_client()
    url = f"{settings.semantic_scholar_base_url}{endpoint}"

    # Add rate limiting delay
    await asyncio.sleep(get_rate_limit_delay())

    try:
        if method == "GET":
            response = await client.get(url, params=params)
        elif method == "POST":
            response = await client.post(url, json=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        if e.response.status_code == 429:
            raise httpx.HTTPError("Rate limit exceeded. Please try again later.")
        elif e.response.status_code == 404:
            raise httpx.HTTPError("Resource not found.")
        else:
            raise httpx.HTTPError(f"API request failed: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise httpx.HTTPError(f"Network error: {str(e)}")


# MCP Tools Implementation

@mcp.tool()
async def search_papers(
    query: str,
    limit: int = 10,
    offset: int = 0,
    fields: Optional[str] = None,
    publication_types: Optional[str] = None,
    publication_date_or_year: Optional[str] = None,
    min_citation_count: Optional[int] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Search for academic papers using the Semantic Scholar API.

    Args:
        query: Search query string
        limit: Number of results to return (max 100)
        offset: Offset for pagination
        fields: Comma-separated list of fields to return
        publication_types: Filter by publication type
        publication_date_or_year: Filter by publication date or year
        min_citation_count: Minimum citation count filter

    Returns:
        JSON string containing search results
    """
    if ctx:
        ctx.info(f"Searching papers for query: {query}")

    params = {
        "query": query,
        "limit": min(limit, 100),  # API limit is 100
        "offset": offset,
    }

    if fields:
        params["fields"] = fields
    if publication_types:
        params["publicationTypes"] = publication_types
    if publication_date_or_year:
        params["publicationDateOrYear"] = publication_date_or_year
    if min_citation_count:
        params["minCitationCount"] = min_citation_count

    try:
        result = await make_api_request("/graph/v1/paper/search", params)

        if ctx:
            total = result.get("total", 0)
            returned = len(result.get("data", []))
            ctx.info(f"Found {total} papers, returning {returned}")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error searching papers: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def get_paper_details(
    paper_id: str, fields: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    Get detailed information about a specific paper.

    Args:
        paper_id: Semantic Scholar paper ID or external ID (DOI, ArXiv, etc.)
        fields: Comma-separated list of fields to return

    Returns:
        JSON string containing paper details
    """
    if ctx:
        ctx.info(f"Fetching paper details for ID: {paper_id}")

    params = {}
    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request(f"/graph/v1/paper/{paper_id}", params)

        if ctx:
            title = result.get("title", "Unknown")
            ctx.info(f"Retrieved paper: {title}")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error fetching paper details: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def get_paper_authors(
    paper_id: str,
    fields: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get authors of a specific paper.

    Args:
        paper_id: Semantic Scholar paper ID
        fields: Comma-separated list of fields to return
        limit: Number of authors to return
        offset: Offset for pagination

    Returns:
        JSON string containing author information
    """
    if ctx:
        ctx.info(f"Fetching authors for paper ID: {paper_id}")

    params = {"limit": limit, "offset": offset}
    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request(f"/graph/v1/paper/{paper_id}/authors", params)

        if ctx:
            count = len(result.get("data", []))
            ctx.info(f"Retrieved {count} authors")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error fetching paper authors: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def get_paper_citations(
    paper_id: str,
    fields: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get citations of a specific paper.

    Args:
        paper_id: Semantic Scholar paper ID
        fields: Comma-separated list of fields to return
        limit: Number of citations to return
        offset: Offset for pagination

    Returns:
        JSON string containing citation information
    """
    if ctx:
        ctx.info(f"Fetching citations for paper ID: {paper_id}")

    params = {"limit": limit, "offset": offset}
    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request(f"/graph/v1/paper/{paper_id}/citations", params)

        if ctx:
            count = len(result.get("data", []))
            ctx.info(f"Retrieved {count} citations")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error fetching paper citations: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def get_paper_references(
    paper_id: str,
    fields: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get references of a specific paper.

    Args:
        paper_id: Semantic Scholar paper ID
        fields: Comma-separated list of fields to return
        limit: Number of references to return
        offset: Offset for pagination

    Returns:
        JSON string containing reference information
    """
    if ctx:
        ctx.info(f"Fetching references for paper ID: {paper_id}")

    params = {"limit": limit, "offset": offset}
    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request(
            f"/graph/v1/paper/{paper_id}/references", params
        )

        if ctx:
            count = len(result.get("data", []))
            ctx.info(f"Retrieved {count} references")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error fetching paper references: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def search_authors(
    query: str,
    limit: int = 10,
    offset: int = 0,
    fields: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> str:
    """
    Search for authors using the Semantic Scholar API.

    Args:
        query: Author search query
        limit: Number of results to return (max 100)
        offset: Offset for pagination
        fields: Comma-separated list of fields to return

    Returns:
        JSON string containing search results
    """
    if ctx:
        ctx.info(f"Searching authors for query: {query}")

    params = {"query": query, "limit": min(limit, 100), "offset": offset}

    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request("/graph/v1/author/search", params)

        if ctx:
            total = result.get("total", 0)
            returned = len(result.get("data", []))
            ctx.info(f"Found {total} authors, returning {returned}")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error searching authors: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def get_author_details(
    author_id: str, fields: Optional[str] = None, ctx: Optional[Context] = None
) -> str:
    """
    Get detailed information about a specific author.

    Args:
        author_id: Semantic Scholar author ID
        fields: Comma-separated list of fields to return

    Returns:
        JSON string containing author details
    """
    if ctx:
        ctx.info(f"Fetching author details for ID: {author_id}")

    params = {}
    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request(f"/graph/v1/author/{author_id}", params)

        if ctx:
            name = result.get("name", "Unknown")
            ctx.info(f"Retrieved author: {name}")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error fetching author details: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


@mcp.tool()
async def get_author_papers(
    author_id: str,
    fields: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get papers by a specific author.

    Args:
        author_id: Semantic Scholar author ID
        fields: Comma-separated list of fields to return
        limit: Number of papers to return
        offset: Offset for pagination

    Returns:
        JSON string containing author's papers
    """
    if ctx:
        ctx.info(f"Fetching papers for author ID: {author_id}")

    params = {"limit": limit, "offset": offset}
    if fields:
        params["fields"] = fields

    try:
        result = await make_api_request(f"/graph/v1/author/{author_id}/papers", params)

        if ctx:
            count = len(result.get("data", []))
            ctx.info(f"Retrieved {count} papers")

        return json.dumps(result, indent=2)

    except Exception as e:
        error_msg = f"Error fetching author papers: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


# MCP Resources Implementation

@mcp.resource("semantic-scholar://api-info")
async def get_api_info() -> str:
    """Get information about the Semantic Scholar API configuration."""
    info = {
        "api_base_url": settings.semantic_scholar_base_url,
        "has_api_key": bool(settings.semantic_scholar_api_key),
        "rate_limit_delay": get_rate_limit_delay(),
        "request_timeout": settings.request_timeout,
        "max_retries": settings.max_retries,
        "server_name": settings.mcp_server_name,
    }
    return json.dumps(info, indent=2)


@mcp.resource("semantic-scholar://available-fields")
async def get_available_fields() -> str:
    """Get information about available fields for API requests."""
    fields_info = {
        "paper_fields": [
            "paperId",
            "title",
            "abstract",
            "venue",
            "year",
            "referenceCount",
            "citationCount",
            "influentialCitationCount",
            "isOpenAccess",
            "fieldsOfStudy",
            "s2FieldsOfStudy",
            "publicationTypes",
            "publicationDate",
            "journal",
            "authors",
            "citations",
            "references",
        ],
        "author_fields": [
            "authorId",
            "name",
            "affiliations",
            "homepage",
            "paperCount",
            "citationCount",
            "hIndex",
            "papers",
        ],
        "citation_fields": [
            "paperId",
            "title",
            "abstract",
            "venue",
            "year",
            "authors",
            "isInfluential",
            "contexts",
            "intents",
        ],
    }
    return json.dumps(fields_info, indent=2)


# MCP Prompts Implementation

@mcp.prompt()
def paper_search_prompt(topic: str, requirements: str = "") -> str:
    """Generate a prompt for searching academic papers on a specific topic."""
    base_prompt = f"""I need to search for academic papers on the topic: {topic}

Please help me:
1. Identify relevant search terms and keywords
2. Suggest appropriate filters (publication year, citation count, etc.)
3. Recommend the most useful fields to retrieve
4. Plan a comprehensive search strategy

Additional requirements: {requirements}

Use the search_papers tool to find relevant papers, then analyze the results to provide insights and recommendations."""

    return base_prompt


@mcp.prompt()
def paper_analysis_prompt(paper_id: str, analysis_type: str = "summary") -> list:
    """Generate a prompt for analyzing a specific paper."""
    from mcp.server.fastmcp.prompts import base
    
    return [
        base.UserMessage(f"I need to analyze paper ID: {paper_id}"),
        base.UserMessage(f"Analysis type: {analysis_type}"),
        base.AssistantMessage(
            "I'll help you analyze this paper. Let me retrieve the paper details first, then provide a comprehensive analysis."
        ),
        base.UserMessage(
            "Please use the get_paper_details tool to fetch the paper information, then provide insights based on the analysis type requested."
        ),
    ]


@mcp.prompt()
def author_research_prompt(author_name: str, research_focus: str = "") -> str:
    """Generate a prompt for researching an author and their work."""
    return f"""I need to research the author: {author_name}

Research focus: {research_focus}

Please help me:
1. Find the author using search_authors
2. Get detailed information about their work
3. Analyze their most cited papers
4. Identify their research areas and contributions
5. Provide a comprehensive overview of their academic profile

Use the appropriate tools to gather this information and provide a detailed analysis."""


def main():
    """Main entry point for the Semantic Scholar MCP Server."""
    transport_mode = get_transport_mode()
    
    if is_stdio_mode():
        logger.info(f"Starting {settings.mcp_server_name} server in stdio mode")
    else:
        logger.info(
            f"Starting {settings.mcp_server_name} server on {settings.mcp_server_host}:{settings.mcp_server_port} (HTTP mode)"
        )

    # Run FastMCP server with the appropriate transport
    mcp.run(transport=transport_mode)


if __name__ == "__main__":
    main()