"""Tests for WordPress service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from visey_recommender.services.wp_service import WordPressService, WPSyncResult
from visey_recommender.clients.wp_client import WPClient


@pytest.fixture
def mock_wp_client():
    """Mock WordPress client."""
    client = MagicMock(spec=WPClient)
    client.fetch_users = AsyncMock(return_value=[
        {"id": 1, "name": "User 1", "email": "user1@example.com"}
    ])
    client.fetch_all_resources = AsyncMock(return_value=[
        {"id": 1, "title": "Post 1", "content": "Content 1"}
    ])
    client.fetch_categories = AsyncMock(return_value=[
        {"id": 1, "name": "Category 1"}
    ])
    client.fetch_tags = AsyncMock(return_value=[
        {"id": 1, "name": "Tag 1"}
    ])
    client.fetch_user_profile = AsyncMock(return_value={
        "id": 1, "name": "User 1", "industry": "tech"
    })
    client.search_posts = AsyncMock(return_value=[
        {"id": 1, "title": "Search Result"}
    ])
    client.health_check = AsyncMock(return_value={
        "status": "healthy", "base_url": "https://example.com"
    })
    return client


@pytest.fixture
def mock_cache_manager():
    """Mock cache manager."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def wp_service(mock_wp_client, mock_cache_manager):
    """WordPress service with mocked dependencies."""
    return WordPressService(
        wp_client=mock_wp_client,
        cache_manager=mock_cache_manager
    )


class TestWordPressService:
    """Test WordPress service functionality."""

    @pytest.mark.asyncio
    async def test_sync_all_data_success(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test successful data synchronization."""
        result = await wp_service.sync_all_data(incremental=True)
        
        assert isinstance(result, WPSyncResult)
        assert result.users_synced == 1
        assert result.posts_synced == 1
        assert result.categories_synced == 1
        assert result.tags_synced == 1
        assert len(result.errors) == 0
        assert result.sync_duration > 0
        
        # Verify cache calls
        assert mock_cache_manager.set.call_count >= 4  # users, posts, categories, tags

    @pytest.mark.asyncio
    async def test_sync_all_data_with_errors(self, wp_service, mock_wp_client):
        """Test data sync with partial failures."""
        # Make users sync fail
        mock_wp_client.fetch_users.side_effect = Exception("Users sync failed")
        
        result = await wp_service.sync_all_data(incremental=True)
        
        assert result.users_synced == 0
        assert result.posts_synced == 1  # Other syncs should still work
        assert len(result.errors) == 1
        assert "Users sync failed" in result.errors[0]

    @pytest.mark.asyncio
    async def test_sync_users(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test user synchronization."""
        count = await wp_service._sync_users()
        
        assert count == 1
        mock_wp_client.fetch_users.assert_called_once_with(per_page=100)
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_posts(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test post synchronization."""
        count = await wp_service._sync_posts()
        
        assert count == 1
        mock_wp_client.fetch_all_resources.assert_called_once()
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_posts_with_modified_after(self, wp_service, mock_wp_client):
        """Test post sync with modified_after filter."""
        modified_after = datetime(2023, 1, 1, tzinfo=timezone.utc)
        
        await wp_service._sync_posts(modified_after=modified_after)
        
        mock_wp_client.fetch_all_resources.assert_called_once_with(
            post_type="posts",
            modified_after=modified_after,
            batch_size=100  # Default batch size
        )

    @pytest.mark.asyncio
    async def test_get_user_profile_cached(self, wp_service, mock_cache_manager):
        """Test getting user profile from cache."""
        cached_profile = {"id": 1, "name": "Cached User"}
        mock_cache_manager.get.return_value = cached_profile
        
        profile = await wp_service.get_user_profile(1, use_cache=True)
        
        assert profile == cached_profile
        mock_cache_manager.get.assert_called_once_with("wp_user_1")

    @pytest.mark.asyncio
    async def test_get_user_profile_not_cached(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test getting user profile when not cached."""
        mock_cache_manager.get.return_value = None
        
        profile = await wp_service.get_user_profile(1, use_cache=True)
        
        assert profile is not None
        mock_wp_client.fetch_user_profile.assert_called_once_with(1)
        mock_cache_manager.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_profile_error(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test user profile fetch with error."""
        mock_cache_manager.get.return_value = None
        mock_wp_client.fetch_user_profile.side_effect = Exception("API error")
        
        profile = await wp_service.get_user_profile(1)
        
        assert profile is None

    @pytest.mark.asyncio
    async def test_search_content(self, wp_service, mock_wp_client):
        """Test content search."""
        results = await wp_service.search_content("test query", limit=10)
        
        assert len(results) == 1
        assert results[0]["title"] == "Search Result"
        mock_wp_client.search_posts.assert_called_once_with("test query", per_page=10)

    @pytest.mark.asyncio
    async def test_search_content_error(self, wp_service, mock_wp_client):
        """Test content search with error."""
        mock_wp_client.search_posts.side_effect = Exception("Search failed")
        
        results = await wp_service.search_content("test query")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_get_cached_data(self, wp_service, mock_cache_manager):
        """Test getting cached data."""
        cached_data = [{"id": 1, "name": "Test"}]
        mock_cache_manager.get.return_value = cached_data
        
        data = await wp_service.get_cached_data("users")
        
        assert data == cached_data
        mock_cache_manager.get.assert_called_once_with("wp_users")

    @pytest.mark.asyncio
    async def test_get_cached_data_invalid_type(self, wp_service):
        """Test getting cached data with invalid type."""
        data = await wp_service.get_cached_data("invalid_type")
        
        assert data is None

    @pytest.mark.asyncio
    async def test_get_content_by_category_cached(self, wp_service, mock_cache_manager):
        """Test getting content by category from cache."""
        cached_posts = [
            {"id": 1, "categories": [1, 2]},
            {"id": 2, "categories": [2, 3]},
            {"id": 3, "categories": [4, 5]}
        ]
        mock_cache_manager.get.return_value = cached_posts
        
        results = await wp_service.get_content_by_category([1, 3], limit=10)
        
        assert len(results) == 2  # Posts 1 and 2 match categories 1 or 3
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_get_content_by_category_api_fallback(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test getting content by category with API fallback."""
        mock_cache_manager.get.return_value = None  # No cached data
        mock_wp_client.fetch_resources.return_value = [
            {"id": 1, "categories": [1]},
            {"id": 2, "categories": [2]}
        ]
        
        results = await wp_service.get_content_by_category([1], limit=10)
        
        assert len(results) == 1
        assert results[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_health_check(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test health check."""
        mock_cache_manager.get.return_value = "ok"
        
        health = await wp_service.health_check()
        
        assert health["wordpress_api"]["status"] == "healthy"
        assert health["cache_healthy"] is True
        assert health["service_status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_cache_unhealthy(self, wp_service, mock_wp_client, mock_cache_manager):
        """Test health check with unhealthy cache."""
        mock_cache_manager.set.side_effect = Exception("Cache error")
        
        health = await wp_service.health_check()
        
        assert health["cache_healthy"] is False
        assert health["service_status"] == "degraded"

    @pytest.mark.asyncio
    async def test_process_user_data(self, wp_service, mock_wp_client):
        """Test user data processing."""
        user_data = {
            "id": 1,
            "name": "Test User",
            "email": "test@example.com",
            "industry": "tech"
        }
        
        processed = await wp_service._process_user_data(user_data)
        
        assert processed["id"] == 1
        assert processed["name"] == "Test User"
        assert processed["industry"] == "tech"
        assert "last_updated" in processed

    @pytest.mark.asyncio
    async def test_process_user_data_with_profile_fetch(self, wp_service, mock_wp_client):
        """Test user data processing with detailed profile fetch."""
        user_data = {"id": 1, "name": "Test User"}
        detailed_profile = {"id": 1, "industry": "tech", "stage": "growth"}
        mock_wp_client.fetch_user_profile.return_value = detailed_profile
        
        processed = await wp_service._process_user_data(user_data)
        
        assert processed["industry"] == "tech"
        assert processed["stage"] == "growth"
        mock_wp_client.fetch_user_profile.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_process_post_data(self, wp_service):
        """Test post data processing."""
        post_data = {
            "id": 1,
            "title": "Test Post",
            "content": "Test content",
            "categories": [1, 2],
            "tags": [3, 4]
        }
        
        processed = await wp_service._process_post_data(post_data)
        
        assert processed["id"] == 1
        assert processed["title"] == "Test Post"
        assert processed["categories"] == [1, 2]
        assert "last_updated" in processed

    @pytest.mark.asyncio
    async def test_get_sync_status(self, wp_service, mock_cache_manager):
        """Test getting sync status."""
        # Mock last sync time
        last_sync = datetime.now(timezone.utc).isoformat()
        mock_cache_manager.get.side_effect = lambda key: {
            "wp_last_sync": last_sync,
            "wp_users": [{"id": 1}],
            "wp_posts": [{"id": 1}, {"id": 2}],
            "wp_categories": [],
            "wp_tags": None
        }.get(key)
        
        status = await wp_service.get_sync_status()
        
        assert status["last_sync"] == last_sync
        assert status["data_counts"]["users"] == 1
        assert status["data_counts"]["posts"] == 2
        assert status["data_counts"]["categories"] == 0
        assert status["data_counts"]["tags"] == 0
        assert status["cache_status"] == "active"

    @pytest.mark.asyncio
    async def test_get_sync_status_empty_cache(self, wp_service, mock_cache_manager):
        """Test sync status with empty cache."""
        mock_cache_manager.get.return_value = None
        
        status = await wp_service.get_sync_status()
        
        assert status["last_sync"] is None
        assert all(count == 0 for count in status["data_counts"].values())
        assert status["cache_status"] == "empty"

    @pytest.mark.asyncio
    async def test_last_sync_time_management(self, wp_service, mock_cache_manager):
        """Test last sync time get/set operations."""
        # Test getting non-existent sync time
        mock_cache_manager.get.return_value = None
        last_sync = await wp_service._get_last_sync_time()
        assert last_sync is None
        
        # Test updating sync time
        await wp_service._update_last_sync_time()
        mock_cache_manager.set.assert_called_once()
        
        # Verify the call was made with correct parameters
        call_args = mock_cache_manager.set.call_args
        assert call_args[0][0] == "wp_last_sync"  # key
        assert call_args[1]["ttl"] == 86400 * 7  # 7 days TTL