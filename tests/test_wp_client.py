"""Tests for WordPress API client."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from visey_recommender.clients.wp_client import WPClient
from visey_recommender.config import settings


@pytest.fixture
def wp_client():
    """Create a WordPress client for testing."""
    return WPClient(
        base_url="https://example.com",
        auth_type="none",
        rate_limit=100,
        timeout=10
    )


@pytest.fixture
def mock_response_data():
    """Mock WordPress API response data."""
    return {
        "user_profile": {
            "id": 123,
            "name": "Test User",
            "email": "test@example.com",
            "meta": {
                "industry": "tech",
                "stage": "growth",
                "team_size": "10-50",
                "funding": "series-a",
                "location": "San Francisco"
            }
        },
        "posts": [
            {
                "id": 1,
                "title": {"rendered": "Test Post"},
                "link": "https://example.com/test-post",
                "excerpt": {"rendered": "Test excerpt"},
                "content": {"rendered": "Test content"},
                "categories": [1, 2],
                "tags": [3, 4],
                "meta": {"custom_field": "value"},
                "date": "2023-01-01T00:00:00",
                "modified": "2023-01-02T00:00:00",
                "author": 123,
                "featured_media": 456,
                "_embedded": {
                    "wp:term": [[
                        {"id": 1, "name": "Technology", "taxonomy": "category"},
                        {"id": 3, "name": "AI", "taxonomy": "post_tag"}
                    ]],
                    "author": [{"name": "Test Author"}]
                }
            }
        ],
        "categories": [
            {"id": 1, "name": "Technology", "slug": "tech", "count": 10}
        ],
        "site_info": {
            "name": "Test Site",
            "description": "A test WordPress site",
            "url": "https://example.com",
            "namespaces": ["wp/v2"]
        }
    }


class TestWPClient:
    """Test WordPress API client functionality."""

    def test_init_with_defaults(self):
        """Test client initialization with default settings."""
        client = WPClient()
        assert client.base_url == settings.WP_BASE_URL.rstrip("/")
        assert client.auth_type == settings.WP_AUTH_TYPE.lower()
        assert client.timeout == 30

    def test_init_with_custom_params(self):
        """Test client initialization with custom parameters."""
        client = WPClient(
            base_url="https://custom.com/",
            auth_type="JWT",
            rate_limit=120,
            timeout=45
        )
        assert client.base_url == "https://custom.com"
        assert client.auth_type == "jwt"
        assert client.timeout == 45

    def test_init_without_base_url_raises_error(self):
        """Test that missing base URL raises ValueError."""
        with patch.object(settings, 'WP_BASE_URL', ''):
            with pytest.raises(ValueError, match="WordPress base URL is required"):
                WPClient()

    def test_auth_headers_none(self, wp_client):
        """Test auth headers with no authentication."""
        headers = wp_client._auth_headers()
        expected = {
            "Accept": "application/json",
            "User-Agent": "Visey-Recommender/1.0"
        }
        assert headers == expected

    def test_auth_headers_jwt(self):
        """Test auth headers with JWT authentication."""
        with patch.object(settings, 'WP_JWT_TOKEN', 'test-jwt-token'):
            client = WPClient(auth_type="jwt")
            headers = client._auth_headers()
            assert headers["Authorization"] == "Bearer test-jwt-token"

    def test_auth_headers_app_password(self):
        """Test auth headers with application password."""
        with patch.object(settings, 'WP_APP_PASSWORD', 'test-app-password'):
            client = WPClient(auth_type="application_password")
            headers = client._auth_headers()
            assert headers["Authorization"] == "Bearer test-app-password"

    def test_auth_basic(self):
        """Test basic authentication setup."""
        with patch.object(settings, 'WP_USERNAME', 'testuser'), \
             patch.object(settings, 'WP_PASSWORD', 'testpass'):
            client = WPClient(auth_type="basic")
            auth = client._auth()
            assert isinstance(auth, httpx.BasicAuth)

    def test_auth_none(self, wp_client):
        """Test no authentication setup."""
        auth = wp_client._auth()
        assert auth is None

    @pytest.mark.asyncio
    async def test_make_request_success(self, wp_client, mock_response_data):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_response_data["site_info"]
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                return_value=mock_response
            )
            
            result = await wp_client._make_request("GET", "https://example.com/test")
            assert result == mock_response_data["site_info"]

    @pytest.mark.asyncio
    async def test_make_request_http_error(self, wp_client):
        """Test API request with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.request = AsyncMock(
                side_effect=httpx.HTTPStatusError("Not Found", request=None, response=mock_response)
            )
            
            with pytest.raises(httpx.HTTPStatusError):
                await wp_client._make_request("GET", "https://example.com/test")

    @pytest.mark.asyncio
    async def test_fetch_user_profile_success(self, wp_client, mock_response_data):
        """Test successful user profile fetch."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["user_profile"]):
            profile = await wp_client.fetch_user_profile(123)
            
            assert profile["id"] == 123
            assert profile["name"] == "Test User"
            assert profile["industry"] == "tech"
            assert profile["stage"] == "growth"

    @pytest.mark.asyncio
    async def test_fetch_user_profile_invalid_id(self, wp_client):
        """Test user profile fetch with invalid ID."""
        with pytest.raises(ValueError, match="Invalid user_id"):
            await wp_client.fetch_user_profile(-1)

        with pytest.raises(ValueError, match="Invalid user_id"):
            await wp_client.fetch_user_profile("invalid")

    @pytest.mark.asyncio
    async def test_fetch_resources_success(self, wp_client, mock_response_data):
        """Test successful resources fetch."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["posts"]):
            resources = await wp_client.fetch_resources(per_page=10, page=1)
            
            assert len(resources) == 1
            resource = resources[0]
            assert resource["id"] == 1
            assert resource["title"] == "Test Post"
            assert resource["category_names"] == ["Technology"]
            assert resource["tag_names"] == ["AI"]

    @pytest.mark.asyncio
    async def test_fetch_resources_with_modified_after(self, wp_client, mock_response_data):
        """Test resources fetch with modified_after filter."""
        modified_after = datetime(2023, 1, 1, tzinfo=timezone.utc)
        
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["posts"]) as mock_request:
            await wp_client.fetch_resources(modified_after=modified_after)
            
            # Check that modified_after was passed in params
            call_args = mock_request.call_args
            assert "modified_after" in call_args[1]["params"]

    @pytest.mark.asyncio
    async def test_fetch_resources_per_page_limit(self, wp_client, mock_response_data):
        """Test that per_page is capped at 100."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["posts"]) as mock_request:
            await wp_client.fetch_resources(per_page=150)
            
            call_args = mock_request.call_args
            assert call_args[1]["params"]["per_page"] == 100

    @pytest.mark.asyncio
    async def test_fetch_all_resources(self, wp_client, mock_response_data):
        """Test fetching all resources with pagination."""
        # Mock multiple pages
        page1_data = mock_response_data["posts"]
        page2_data = []  # Empty page to stop pagination
        
        with patch.object(wp_client, 'fetch_resources', side_effect=[page1_data, page2_data]):
            all_resources = await wp_client.fetch_all_resources()
            
            assert len(all_resources) == 1
            assert all_resources[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_fetch_categories(self, wp_client, mock_response_data):
        """Test fetching categories."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["categories"]):
            categories = await wp_client.fetch_categories()
            
            assert len(categories) == 1
            assert categories[0]["name"] == "Technology"

    @pytest.mark.asyncio
    async def test_search_posts(self, wp_client, mock_response_data):
        """Test post search functionality."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["posts"]):
            results = await wp_client.search_posts("test query")
            
            assert len(results) == 1
            assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, wp_client, mock_response_data):
        """Test health check with healthy API."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["site_info"]):
            health = await wp_client.health_check()
            
            assert health["status"] == "healthy"
            assert health["base_url"] == wp_client.base_url
            assert "timestamp" in health

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, wp_client):
        """Test health check with unhealthy API."""
        with patch.object(wp_client, '_make_request', side_effect=Exception("Connection failed")):
            health = await wp_client.health_check()
            
            assert health["status"] == "unhealthy"
            assert "Connection failed" in health["error"]

    @pytest.mark.asyncio
    async def test_get_site_info(self, wp_client, mock_response_data):
        """Test getting site information."""
        with patch.object(wp_client, '_make_request', return_value=mock_response_data["site_info"]):
            info = await wp_client.get_site_info()
            
            assert info["name"] == "Test Site"
            assert info["description"] == "A test WordPress site"

    def test_extract_rendered_content_dict(self, wp_client):
        """Test extracting rendered content from dict."""
        content = {"rendered": "Test content"}
        result = wp_client._extract_rendered_content(content)
        assert result == "Test content"

    def test_extract_rendered_content_string(self, wp_client):
        """Test extracting rendered content from string."""
        content = "Test content"
        result = wp_client._extract_rendered_content(content)
        assert result == "Test content"

    def test_extract_rendered_content_none(self, wp_client):
        """Test extracting rendered content from None."""
        result = wp_client._extract_rendered_content(None)
        assert result == ""


@pytest.mark.integration
class TestWPClientIntegration:
    """Integration tests for WordPress API client (requires real WordPress site)."""

    @pytest.mark.skip(reason="Requires live WordPress site")
    @pytest.mark.asyncio
    async def test_real_wordpress_connection(self):
        """Test connection to real WordPress site."""
        # This test would require a real WordPress site
        # Skip by default to avoid external dependencies
        client = WPClient(base_url="https://demo.wp-api.org")
        health = await client.health_check()
        assert health["status"] == "healthy"