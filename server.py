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
from config import settings, get_semantic_scholar_headers, get_rate_limit_delay, is_http_mode, get_transport_mode

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


def filter_open_access_pdf_disclaimer(data: Any) -> Any:
    """
    Recursively remove 'disclaimer' field from openAccessPdf objects in API responses.
    This removes unnecessary legal disclaimer information that's not useful for AI applications.
    
    Args:
        data: API response data (dict, list, or other)
        
    Returns:
        Filtered data with disclaimer fields removed from openAccessPdf objects
    """
    if isinstance(data, dict):
        filtered_data = {}
        for key, value in data.items():
            if key == "openAccessPdf" and isinstance(value, dict):
                # Filter out disclaimer from openAccessPdf object
                filtered_pdf = {k: v for k, v in value.items() if k != "disclaimer"}
                filtered_data[key] = filtered_pdf
            else:
                # Recursively filter nested structures
                filtered_data[key] = filter_open_access_pdf_disclaimer(value)
        return filtered_data
    elif isinstance(data, list):
        # Filter each item in the list
        return [filter_open_access_pdf_disclaimer(item) for item in data]
    else:
        # Return primitive values as-is
        return data


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
        httpx.HTTPError: If request fails with detailed error information
    """
    client = await init_http_client()
    url = f"{settings.semantic_scholar_base_url}{endpoint}"

    # Add rate limiting delay
    await asyncio.sleep(get_rate_limit_delay())

    logger.info(f"🌐 Making {method} request to: {url}")
    if params:
        logger.info(f"📋 Request parameters: {params}")

    try:
        if method == "GET":
            response = await client.get(url, params=params)
        elif method == "POST":
            response = await client.post(url, json=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        logger.info(f"📡 Response status: {response.status_code}")
        response.raise_for_status()
        
        result = response.json()
        logger.info("✅ API request successful")
        
        # Filter out disclaimer from openAccessPdf fields
        filtered_result = filter_open_access_pdf_disclaimer(result)
        return filtered_result

    except httpx.HTTPStatusError as e:
        error_details = {
            "status_code": e.response.status_code,
            "url": str(e.request.url),
            "method": e.request.method,
            "response_text": e.response.text,
            "headers": dict(e.response.headers)
        }
        
        logger.error(f"❌ HTTP {e.response.status_code} error: {e.response.text}")
        logger.error(f"🔍 Request details: {error_details}")
        
        if e.response.status_code == 400:
            # Try to parse error response for more details
            try:
                error_json = e.response.json()
                detailed_msg = f"Bad Request (400): {error_json.get('message', e.response.text)}"
                if 'error' in error_json:
                    detailed_msg += f" - {error_json['error']}"
                if 'details' in error_json:
                    detailed_msg += f" - Details: {error_json['details']}"
                raise httpx.HTTPError(detailed_msg)
            except json.JSONDecodeError:
                raise httpx.HTTPError(f"Bad Request (400): Invalid API parameters. Response: {e.response.text}")
        elif e.response.status_code == 401:
            raise httpx.HTTPError("Authentication failed (401): Invalid or missing API key")
        elif e.response.status_code == 403:
            raise httpx.HTTPError("Access forbidden (403): API key lacks required permissions")
        elif e.response.status_code == 404:
            raise httpx.HTTPError(f"Resource not found (404): {endpoint}")
        elif e.response.status_code == 429:
            rate_limit_info = e.response.headers.get('X-RateLimit-Remaining', 'unknown')
            retry_after = e.response.headers.get('Retry-After', 'unknown')
            raise httpx.HTTPError(f"Rate limit exceeded (429): Remaining: {rate_limit_info}, Retry after: {retry_after}s")
        elif e.response.status_code >= 500:
            raise httpx.HTTPError(f"Server error ({e.response.status_code}): Semantic Scholar API is experiencing issues")
        else:
            raise httpx.HTTPError(f"HTTP {e.response.status_code}: {e.response.text}")
            
    except httpx.RequestError as e:
        logger.error(f"❌ Network error: {e}")
        if "timeout" in str(e).lower():
            raise httpx.HTTPError(f"Request timeout: API took too long to respond (>{settings.request_timeout}s)")
        elif "connection" in str(e).lower():
            raise httpx.HTTPError("Connection error: Unable to reach Semantic Scholar API")
        else:
            raise httpx.HTTPError(f"Network error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON decode error: {e}")
        raise httpx.HTTPError(f"Invalid JSON response from API: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Unexpected error in API request: {e}")
        raise httpx.HTTPError(f"Unexpected error: {str(e)}")


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
        query: Search query string (required)
        limit: Number of results to return (1-100, default: 10)
        offset: Offset for pagination (default: 0)
        fields: Comma-separated list of fields to return. Available fields:
                paperId, title, abstract, venue, year, referenceCount, citationCount,
                influentialCitationCount, isOpenAccess, fieldsOfStudy, s2FieldsOfStudy,
                publicationTypes, publicationDate, journal, authors, citations, references
        publication_types: Filter by publication type (e.g., JournalArticle, Conference)
        publication_date_or_year: Filter by publication date/year. Format examples:
                                 - Single year: "2024"
                                 - Year range: "2023:2024"
                                 - Month range: "2024-01:2024-06"
                                 - Date range: "2024-01-01:2024-12-31"
        min_citation_count: Minimum citation count filter (integer)

    Returns:
        JSON string containing search results with metadata
    """
    if ctx:
        ctx.info(f"🔍 Searching papers for query: '{query}'")

    # Validate parameters
    if not query or not query.strip():
        error_msg = "Query parameter is required and cannot be empty"
        if ctx:
            ctx.info(f"❌ Parameter validation failed: {error_msg}")
        return json.dumps({"error": error_msg, "parameter": "query"})

    if limit < 1 or limit > 100:
        error_msg = "Limit must be between 1 and 100"
        if ctx:
            ctx.info(f"❌ Parameter validation failed: {error_msg}")
        return json.dumps({"error": error_msg, "parameter": "limit", "value": limit})

    if offset < 0:
        error_msg = "Offset must be non-negative"
        if ctx:
            ctx.info(f"❌ Parameter validation failed: {error_msg}")
        return json.dumps({"error": error_msg, "parameter": "offset", "value": offset})

    # Valid field names for Semantic Scholar API
    valid_fields = {
        "paperId", "title", "abstract", "venue", "year", "referenceCount", 
        "citationCount", "influentialCitationCount", "isOpenAccess", 
        "fieldsOfStudy", "s2FieldsOfStudy", "publicationTypes", 
        "publicationDate", "journal", "authors", "citations", "references",
        "url", "publicationVenue", "externalIds", "openAccessPdf"
    }

    # Build API parameters using correct parameter names
    params = {
        "query": query.strip(),
        "limit": min(limit, 100),
        "offset": offset,
    }

    if fields:
        # Validate field names
        requested_fields = [f.strip() for f in fields.split(",")]
        invalid_fields = [f for f in requested_fields if f not in valid_fields]
        if invalid_fields:
            error_msg = f"Invalid field names: {invalid_fields}. Valid fields: {sorted(valid_fields)}"
            if ctx:
                ctx.info(f"❌ Field validation failed: {error_msg}")
            return json.dumps({"error": error_msg, "parameter": "fields", "invalid_fields": invalid_fields})
        params["fields"] = fields

    if publication_types:
        params["publicationTypes"] = publication_types

    # Fix parameter name: use camelCase as expected by API
    if publication_date_or_year:
        # Validate date format
        date_str = publication_date_or_year.strip()
        if not date_str:
            error_msg = "Publication date/year cannot be empty"
            if ctx:
                ctx.info(f"❌ Date validation failed: {error_msg}")
            return json.dumps({"error": error_msg, "parameter": "publication_date_or_year"})
        
        # Convert format like "2024-2025" to "2024:2025"
        if "-" in date_str and ":" not in date_str:
            # Check if it looks like a range (e.g., "2024-2025")
            parts = date_str.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit() and len(parts[0]) == 4 and len(parts[1]) == 4:
                date_str = f"{parts[0]}:{parts[1]}"
                if ctx:
                    ctx.info(f"📅 Converted date range format: '{publication_date_or_year}' → '{date_str}'")
        
        params["publicationDateOrYear"] = date_str

    if min_citation_count is not None:
        if min_citation_count < 0:
            error_msg = "Minimum citation count must be non-negative"
            if ctx:
                ctx.info(f"❌ Parameter validation failed: {error_msg}")
            return json.dumps({"error": error_msg, "parameter": "min_citation_count", "value": min_citation_count})
        params["minCitationCount"] = min_citation_count

    if ctx:
        ctx.info(f"📋 API request parameters: {params}")

    try:
        result = await make_api_request("/graph/v1/paper/search", params)

        if ctx:
            total = result.get("total", 0)
            returned = len(result.get("data", []))
            ctx.info(f"✅ Found {total} papers, returning {returned}")

        # Add metadata to response
        result["_metadata"] = {
            "query": query,
            "parameters_used": params,
            "api_endpoint": "/graph/v1/paper/search"
        }

        return json.dumps(result, indent=2)

    except httpx.HTTPError as e:
        error_msg = f"API request failed: {str(e)}"
        if ctx:
            ctx.info(f"❌ HTTP error: {error_msg}")
        logger.error(f"HTTP error in search_papers: {error_msg}")
        return json.dumps({
            "error": error_msg,
            "query": query,
            "parameters": params,
            "suggestion": "Check API parameters format and try again"
        })
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        if ctx:
            ctx.info(f"❌ Unexpected error: {error_msg}")
        logger.error(f"Unexpected error in search_papers: {error_msg}")
        return json.dumps({
            "error": error_msg,
            "query": query,
            "suggestion": "Please report this error to the server administrator"
        })


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
            "url",
            "publicationVenue",
            "externalIds",
            "openAccessPdf"
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


@mcp.resource("semantic-scholar://ai-agent-guidelines")
async def get_ai_agent_guidelines() -> str:
    """
    Comprehensive guidelines for AI agents using this Semantic Scholar MCP server.
    This resource provides clear instructions on parameter formats, best practices, and common pitfalls.
    """
    guidelines = {
        "overview": {
            "description": "Semantic Scholar MCP Server provides access to academic paper search and retrieval",
            "api_version": "Graph API v1",
            "rate_limits": "1 RPS without API key, higher with authentication",
            "base_url": settings.semantic_scholar_base_url
        },
        "tools": {
            "search_papers": {
                "description": "Search for academic papers with advanced filtering",
                "required_parameters": ["query"],
                "parameter_guidelines": {
                    "query": {
                        "type": "string",
                        "required": True,
                        "description": "Search terms (title, abstract, keywords)",
                        "examples": ["machine learning", "neural networks", "climate change"],
                        "tips": "Use specific terms for better results"
                    },
                    "fields": {
                        "type": "string",
                        "required": False,
                        "description": "Comma-separated list of fields to return",
                        "valid_fields": ["paperId", "title", "abstract", "venue", "year", "citationCount", "authors", "url"],
                        "examples": ["paperId,title,authors", "title,abstract,year,citationCount"],
                        "default_recommendation": "paperId,title,authors,year,citationCount,url"
                    },
                    "publication_date_or_year": {
                        "type": "string",
                        "required": False,
                        "description": "Filter by publication date or year",
                        "correct_formats": {
                            "single_year": "2024",
                            "year_range": "2023:2024",
                            "month_range": "2024-01:2024-06",
                            "date_range": "2024-01-01:2024-12-31"
                        },
                        "common_mistakes": {
                            "wrong": "2024-2025",
                            "correct": "2024:2025",
                            "note": "Use colon (:) for ranges, not hyphen (-)"
                        }
                    },
                    "limit": {
                        "type": "integer",
                        "required": False,
                        "range": "1-100",
                        "default": 10,
                        "recommendation": "Use 10-20 for quick searches, 50-100 for comprehensive results"
                    }
                },
                "best_practices": [
                    "Always include essential fields like paperId, title, authors",
                    "Use specific queries for better precision",
                    "Combine with date filters for recent research",
                    "Start with small limits, then increase if needed",
                    "Check total count before requesting large datasets"
                ],
                "common_errors": {
                    "400_bad_request": {
                        "causes": [
                            "Invalid field names in 'fields' parameter",
                            "Wrong date format in 'publication_date_or_year'",
                            "Empty query string",
                            "Invalid parameter values"
                        ],
                        "solutions": [
                            "Validate field names against available_fields resource",
                            "Use correct date format (YYYY:YYYY for ranges)",
                            "Ensure query is not empty",
                            "Check parameter types and ranges"
                        ]
                    }
                }
            },
            "get_paper_details": {
                "description": "Get detailed information about a specific paper",
                "required_parameters": ["paper_id"],
                "parameter_guidelines": {
                    "paper_id": {
                        "type": "string",
                        "required": True,
                        "description": "Semantic Scholar paper ID or external ID (DOI, ArXiv, etc.)",
                        "examples": ["649def34f8be52c8b66281af98ae884c09aef38b", "10.1038/nature14539", "1506.02142"]
                    }
                }
            }
        },
        "resources": {
            "api-info": "Get server configuration and API status",
            "available-fields": "List all valid field names for API requests",
            "ai-agent-guidelines": "This comprehensive guide for AI agents"
        },
        "prompts": {
            "paper_search_prompt": "Generate research strategy for paper search",
            "paper_analysis_prompt": "Analyze specific papers in detail",
            "author_research_prompt": "Research authors and their work"
        },
        "workflow_examples": {
            "basic_search": {
                "step_1": "search_papers with query='machine learning' and basic fields",
                "step_2": "Review results and select interesting papers",
                "step_3": "get_paper_details for specific papers",
                "step_4": "get_paper_citations or get_paper_references for related work"
            },
            "comprehensive_research": {
                "step_1": "search_papers with specific query and date filter",
                "step_2": "Analyze top papers by citation count",
                "step_3": "get_author_details for key researchers",
                "step_4": "get_author_papers for their other work",
                "step_5": "Synthesize findings into research overview"
            }
        },
        "error_handling": {
            "always_check": [
                "Response contains 'error' field",
                "HTTP status in error messages",
                "Parameter validation errors"
            ],
            "retry_strategies": {
                "rate_limit_429": "Wait and retry with exponential backoff",
                "bad_request_400": "Fix parameters and retry",
                "not_found_404": "Try different paper ID or search terms",
                "server_error_5xx": "Wait and retry, may be temporary"
            }
        },
        "performance_tips": [
            "Request only needed fields to reduce response size",
            "Use pagination (offset) for large result sets",
            "Cache paper details to avoid repeated requests",
            "Batch related operations when possible",
            "Monitor rate limits and plan requests accordingly"
        ],
        "data_interpretation": {
            "citation_count": "Number of papers citing this work",
            "influential_citation_count": "High-quality citations (Semantic Scholar's metric)",
            "fields_of_study": "Research areas assigned by the system",
            "publication_types": "Article type (Journal, Conference, etc.)",
            "venue": "Journal or conference name",
            "open_access": "PDF freely available"
        }
    }
    
    return json.dumps(guidelines, indent=2)


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
    import argparse
    
    # Add command line arguments for MCP SDK compatibility
    parser = argparse.ArgumentParser(description="Semantic Scholar MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], 
                       default=get_transport_mode(), help="Transport protocol")
    parser.add_argument("--host", default=settings.mcp_server_host, 
                       help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.mcp_server_port, 
                       help="Port to bind to")
    parser.add_argument("--log-level", default=settings.mcp_log_level, 
                       help="Logging level")
    parser.add_argument("--json-response", action="store_true", 
                       help="Enable JSON responses instead of SSE")
    
    args = parser.parse_args()
    
    # Override settings with command line arguments
    transport_mode = args.transport
    host = args.host
    port = args.port
    
    if transport_mode == "stdio":
        logger.info(f"Starting {settings.mcp_server_name} server in stdio mode")
        # Run FastMCP server with stdio transport
        mcp.run(transport=transport_mode)
    else:
        logger.info(
            f"Starting {settings.mcp_server_name} server on {host}:{port} (HTTP mode)"
        )
        # For HTTP mode, we need to use uvicorn directly to control port
        import uvicorn
        
        if transport_mode == "streamable-http":
            app = mcp.streamable_http_app()
        else:  # sse
            app = mcp.sse_app()
            
        uvicorn.run(app, host=host, port=port, log_level=args.log_level.lower())


if __name__ == "__main__":
    main()