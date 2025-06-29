"""
Test suite for Semantic Scholar MCP Server.

This module contains comprehensive tests for all server functionality including
tools, resources, prompts, and error handling.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

# Import server components
from server import (
    make_api_request,
    init_http_client,
    close_http_client,
    search_papers,
    get_paper_details,
    search_authors,
    get_author_details,
)
from config import settings


class TestConfiguration:
    """Test configuration and settings."""

    def test_settings_loaded(self):
        """Test that settings are properly loaded."""
        assert settings.mcp_server_name
        assert settings.semantic_scholar_base_url
        assert settings.mcp_server_port > 0

    def test_api_key_configured(self):
        """Test that API key is configured (for development)."""
        # In production, you might want to skip this test
        assert settings.semantic_scholar_api_key


class TestHTTPClient:
    """Test HTTP client functionality."""

    @pytest.mark.asyncio
    async def test_init_http_client(self):
        """Test HTTP client initialization."""
        client = await init_http_client()
        assert client is not None
        assert isinstance(client, httpx.AsyncClient)
        await close_http_client()

    @pytest.mark.asyncio
    async def test_close_http_client(self):
        """Test HTTP client cleanup."""
        await init_http_client()
        await close_http_client()
        # Should be able to close multiple times without error
        await close_http_client()


class TestAPIRequests:
    """Test API request functionality."""

    @pytest.mark.asyncio
    async def test_make_api_request_success(self):
        """Test successful API request."""
        mock_response = {
            "data": [{"paperId": "123", "title": "Test Paper"}],
            "total": 1,
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_client.get.return_value = mock_response_obj

            result = await make_api_request("/test/endpoint")
            assert result == mock_response
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_api_request_rate_limit_error(self):
        """Test handling of rate limit errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response_obj = AsyncMock()
            mock_response_obj.status_code = 429
            mock_response_obj.text = "Rate limit exceeded"

            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Too Many Requests", request=MagicMock(), response=mock_response_obj
            )

            with pytest.raises(httpx.HTTPError, match="Rate limit exceeded"):
                await make_api_request("/test/endpoint")

    @pytest.mark.asyncio
    async def test_make_api_request_not_found_error(self):
        """Test handling of 404 errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_response_obj = AsyncMock()
            mock_response_obj.status_code = 404
            mock_response_obj.text = "Not found"

            mock_client.get.side_effect = httpx.HTTPStatusError(
                "Not Found", request=MagicMock(), response=mock_response_obj
            )

            with pytest.raises(httpx.HTTPError, match="Resource not found"):
                await make_api_request("/test/endpoint")


class TestTools:
    """Test MCP tools functionality."""

    @pytest.mark.asyncio
    async def test_search_papers_success(self):
        """Test successful paper search."""
        mock_result = {
            "data": [
                {"paperId": "123", "title": "Test Paper 1"},
                {"paperId": "456", "title": "Test Paper 2"},
            ],
            "total": 2,
        }

        with patch("server.make_api_request", return_value=mock_result):
            result = await search_papers("machine learning", limit=2)

            # Result should be JSON string
            parsed_result = json.loads(result)
            assert parsed_result == mock_result
            assert len(parsed_result["data"]) == 2

    @pytest.mark.asyncio
    async def test_search_papers_with_filters(self):
        """Test paper search with filters."""
        mock_result = {"data": [], "total": 0}

        with patch("server.make_api_request", return_value=mock_result) as mock_request:
            await search_papers(
                "deep learning",
                limit=50,
                offset=10,
                fields="paperId,title,year",
                publication_types="JournalArticle",
                publication_date_or_year="2023",
                min_citation_count=10,
            )

            # Verify the API was called with correct parameters
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[0][0] == "/graph/v1/paper/search"
            params = call_args[0][1]
            assert params["query"] == "deep learning"
            assert params["limit"] == 50
            assert params["offset"] == 10
            assert params["fields"] == "paperId,title,year"
            assert params["publicationTypes"] == "JournalArticle"
            assert params["publicationDateOrYear"] == "2023"
            assert params["minCitationCount"] == 10

    @pytest.mark.asyncio
    async def test_search_papers_error_handling(self):
        """Test paper search error handling."""
        with patch("server.make_api_request", side_effect=Exception("API Error")):
            result = await search_papers("test query")

            # Should return error in JSON format
            parsed_result = json.loads(result)
            assert "error" in parsed_result
            assert "API Error" in parsed_result["error"]

    @pytest.mark.asyncio
    async def test_get_paper_details_success(self):
        """Test successful paper details retrieval."""
        mock_result = {
            "paperId": "123",
            "title": "Test Paper",
            "abstract": "This is a test paper",
            "year": 2023,
        }

        with patch("server.make_api_request", return_value=mock_result):
            result = await get_paper_details("123")

            parsed_result = json.loads(result)
            assert parsed_result == mock_result
            assert parsed_result["paperId"] == "123"

    @pytest.mark.asyncio
    async def test_search_authors_success(self):
        """Test successful author search."""
        mock_result = {
            "data": [
                {"authorId": "123", "name": "Test Author"},
                {"authorId": "456", "name": "Another Author"},
            ],
            "total": 2,
        }

        with patch("server.make_api_request", return_value=mock_result):
            result = await search_authors("John Smith")

            parsed_result = json.loads(result)
            assert parsed_result == mock_result
            assert len(parsed_result["data"]) == 2

    @pytest.mark.asyncio
    async def test_get_author_details_success(self):
        """Test successful author details retrieval."""
        mock_result = {
            "authorId": "123",
            "name": "Test Author",
            "paperCount": 50,
            "citationCount": 1000,
        }

        with patch("server.make_api_request", return_value=mock_result):
            result = await get_author_details("123")

            parsed_result = json.loads(result)
            assert parsed_result == mock_result
            assert parsed_result["authorId"] == "123"


class TestResources:
    """Test MCP resources functionality."""

    @pytest.mark.asyncio
    async def test_get_api_info_resource(self):
        """Test API info resource."""
        # We need to call the resource function directly since it's decorated
        from server import get_api_info

        result = await get_api_info()
        parsed_result = json.loads(result)

        assert "api_base_url" in parsed_result
        assert "has_api_key" in parsed_result
        assert "rate_limit_delay" in parsed_result
        assert "server_name" in parsed_result
        assert parsed_result["api_base_url"] == settings.semantic_scholar_base_url

    @pytest.mark.asyncio
    async def test_get_available_fields_resource(self):
        """Test available fields resource."""
        from server import get_available_fields

        result = await get_available_fields()
        parsed_result = json.loads(result)

        assert "paper_fields" in parsed_result
        assert "author_fields" in parsed_result
        assert "citation_fields" in parsed_result
        assert isinstance(parsed_result["paper_fields"], list)
        assert "paperId" in parsed_result["paper_fields"]
        assert "title" in parsed_result["paper_fields"]


class TestPrompts:
    """Test MCP prompts functionality."""

    def test_paper_search_prompt(self):
        """Test paper search prompt generation."""
        from server import paper_search_prompt

        prompt = paper_search_prompt("machine learning", "focus on recent papers")

        assert isinstance(prompt, str)
        assert "machine learning" in prompt
        assert "recent papers" in prompt
        assert "search_papers" in prompt

    def test_paper_analysis_prompt(self):
        """Test paper analysis prompt generation."""
        from server import paper_analysis_prompt

        messages = paper_analysis_prompt("123", "summary")

        assert isinstance(messages, list)
        assert len(messages) >= 3
        assert any("123" in str(msg) for msg in messages)
        assert any("summary" in str(msg) for msg in messages)

    def test_author_research_prompt(self):
        """Test author research prompt generation."""
        from server import author_research_prompt

        prompt = author_research_prompt("John Smith", "AI research")

        assert isinstance(prompt, str)
        assert "John Smith" in prompt
        assert "AI research" in prompt
        assert "search_authors" in prompt


class TestIntegration:
    """Integration tests for the complete system."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Test server lifecycle management."""
        # Test that we can initialize and close the HTTP client
        await init_http_client()
        await close_http_client()

    @pytest.mark.asyncio
    async def test_end_to_end_paper_search(self):
        """Test end-to-end paper search with mocked API."""
        mock_result = {
            "data": [{"paperId": "test123", "title": "Test Paper"}],
            "total": 1,
        }

        with patch("server.make_api_request", return_value=mock_result):
            # Test search
            search_result = await search_papers("test query")
            search_data = json.loads(search_result)

            assert search_data["total"] == 1
            paper_id = search_data["data"][0]["paperId"]

            # Test getting details for the found paper
            mock_detail = {
                "paperId": paper_id,
                "title": "Test Paper",
                "abstract": "Test abstract",
            }

            with patch("server.make_api_request", return_value=mock_detail):
                detail_result = await get_paper_details(paper_id)
                detail_data = json.loads(detail_result)

                assert detail_data["paperId"] == paper_id
                assert detail_data["title"] == "Test Paper"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
