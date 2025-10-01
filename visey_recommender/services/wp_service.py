"""WordPress integration service for the recommender system."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

from ..clients.wp_client import WPClient
from ..config import settings
from ..utils.metrics import track_operation
from ..storage.cache import CacheManager


@dataclass
class WPSyncResult:
    """Result of WordPress data synchronization."""
    users_synced: int
    posts_synced: int
    categories_synced: int
    tags_synced: int
    errors: List[str]
    sync_duration: float
    last_sync: datetime


class WordPressService:
    """Service for managing WordPress data integration and synchronization."""

    def __init__(self, wp_client: Optional[WPClient] = None, 
                 cache_manager: Optional[CacheManager] = None):
        self.wp_client = wp_client or WPClient(
            rate_limit=settings.WP_RATE_LIMIT,
            timeout=settings.WP_TIMEOUT
        )
        self.cache_manager = cache_manager or CacheManager()
        self.logger = logging.getLogger(__name__)

    @track_operation("wp_sync_all_data")
    async def sync_all_data(self, incremental: bool = True) -> WPSyncResult:
        """Synchronize all WordPress data (users, posts, categories, tags).
        
        Args:
            incremental: If True, only sync data modified since last sync
            
        Returns:
            WPSyncResult with synchronization statistics
        """
        start_time = datetime.now()
        errors = []
        
        # Determine last sync time for incremental updates
        last_sync = None
        if incremental:
            last_sync = await self._get_last_sync_time()
        
        self.logger.info(f"Starting WordPress data sync (incremental: {incremental})")
        
        # Sync data in parallel where possible
        sync_tasks = [
            self._sync_users(),
            self._sync_posts(modified_after=last_sync),
            self._sync_categories(),
            self._sync_tags()
        ]
        
        try:
            results = await asyncio.gather(*sync_tasks, return_exceptions=True)
            
            users_count = results[0] if not isinstance(results[0], Exception) else 0
            posts_count = results[1] if not isinstance(results[1], Exception) else 0
            categories_count = results[2] if not isinstance(results[2], Exception) else 0
            tags_count = results[3] if not isinstance(results[3], Exception) else 0
            
            # Collect any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    task_names = ["users", "posts", "categories", "tags"]
                    errors.append(f"Failed to sync {task_names[i]}: {str(result)}")
            
        except Exception as e:
            self.logger.error(f"WordPress sync failed: {str(e)}")
            errors.append(f"Sync failed: {str(e)}")
            users_count = posts_count = categories_count = tags_count = 0
        
        # Update last sync time
        await self._update_last_sync_time()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        result = WPSyncResult(
            users_synced=users_count,
            posts_synced=posts_count,
            categories_synced=categories_count,
            tags_synced=tags_count,
            errors=errors,
            sync_duration=duration,
            last_sync=datetime.now(timezone.utc)
        )
        
        self.logger.info(f"WordPress sync completed in {duration:.2f}s: "
                        f"{posts_count} posts, {users_count} users, "
                        f"{categories_count} categories, {tags_count} tags")
        
        return result

    async def _sync_users(self) -> int:
        """Sync WordPress users."""
        try:
            users = await self.wp_client.fetch_users(per_page=100)
            
            # Process and cache user data
            processed_users = []
            for user in users:
                processed_user = await self._process_user_data(user)
                processed_users.append(processed_user)
            
            # Cache users data
            await self.cache_manager.set("wp_users", processed_users, ttl=3600)
            
            self.logger.debug(f"Synced {len(users)} users")
            return len(users)
            
        except Exception as e:
            self.logger.error(f"Failed to sync users: {str(e)}")
            raise

    async def _sync_posts(self, modified_after: Optional[datetime] = None) -> int:
        """Sync WordPress posts."""
        try:
            posts = await self.wp_client.fetch_all_resources(
                post_type="posts",
                modified_after=modified_after,
                batch_size=settings.WP_BATCH_SIZE
            )
            
            # Process and cache posts data
            processed_posts = []
            for post in posts:
                processed_post = await self._process_post_data(post)
                processed_posts.append(processed_post)
            
            # Cache posts data
            await self.cache_manager.set("wp_posts", processed_posts, ttl=1800)
            
            self.logger.debug(f"Synced {len(posts)} posts")
            return len(posts)
            
        except Exception as e:
            self.logger.error(f"Failed to sync posts: {str(e)}")
            raise

    async def _sync_categories(self) -> int:
        """Sync WordPress categories."""
        try:
            categories = await self.wp_client.fetch_categories()
            
            # Cache categories
            await self.cache_manager.set("wp_categories", categories, ttl=7200)
            
            self.logger.debug(f"Synced {len(categories)} categories")
            return len(categories)
            
        except Exception as e:
            self.logger.error(f"Failed to sync categories: {str(e)}")
            raise

    async def _sync_tags(self) -> int:
        """Sync WordPress tags."""
        try:
            tags = await self.wp_client.fetch_tags()
            
            # Cache tags
            await self.cache_manager.set("wp_tags", tags, ttl=7200)
            
            self.logger.debug(f"Synced {len(tags)} tags")
            return len(tags)
            
        except Exception as e:
            self.logger.error(f"Failed to sync tags: {str(e)}")
            raise

    async def _process_user_data(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize user data for the recommender system."""
        # Fetch detailed profile if needed
        try:
            if user.get("id"):
                detailed_profile = await self.wp_client.fetch_user_profile(user["id"])
                user.update(detailed_profile)
        except Exception as e:
            self.logger.warning(f"Failed to fetch detailed profile for user {user.get('id')}: {str(e)}")
        
        return {
            "id": user.get("id"),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "industry": user.get("industry", ""),
            "stage": user.get("stage", ""),
            "team_size": user.get("team_size", ""),
            "funding": user.get("funding", ""),
            "location": user.get("location", ""),
            "bio": user.get("bio", ""),
            "registered_date": user.get("registered_date", ""),
            "roles": user.get("roles", []),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _process_post_data(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize post data for the recommender system."""
        return {
            "id": post.get("id"),
            "title": post.get("title", ""),
            "content": post.get("content", ""),
            "excerpt": post.get("excerpt", ""),
            "link": post.get("link", ""),
            "categories": post.get("categories", []),
            "tags": post.get("tags", []),
            "category_names": post.get("category_names", []),
            "tag_names": post.get("tag_names", []),
            "author_id": post.get("author_id", 0),
            "author_name": post.get("author_name", ""),
            "date": post.get("date", ""),
            "modified": post.get("modified", ""),
            "featured_media": post.get("featured_media", 0),
            "meta": post.get("meta", {}),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def get_user_profile(self, user_id: int, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get user profile with caching support."""
        cache_key = f"wp_user_{user_id}"
        
        if use_cache:
            cached_profile = await self.cache_manager.get(cache_key)
            if cached_profile:
                return cached_profile
        
        try:
            profile = await self.wp_client.fetch_user_profile(user_id)
            processed_profile = await self._process_user_data(profile)
            
            # Cache for 1 hour
            await self.cache_manager.set(cache_key, processed_profile, ttl=3600)
            
            return processed_profile
            
        except Exception as e:
            self.logger.error(f"Failed to get user profile {user_id}: {str(e)}")
            return None

    async def search_content(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search WordPress content."""
        try:
            results = await self.wp_client.search_posts(query, per_page=limit)
            return [await self._process_post_data(post) for post in results]
        except Exception as e:
            self.logger.error(f"Content search failed: {str(e)}")
            return []

    async def get_cached_data(self, data_type: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached WordPress data by type."""
        cache_keys = {
            "users": "wp_users",
            "posts": "wp_posts", 
            "categories": "wp_categories",
            "tags": "wp_tags"
        }
        
        cache_key = cache_keys.get(data_type)
        if not cache_key:
            return None
            
        return await self.cache_manager.get(cache_key)

    async def get_content_by_category(self, category_ids: List[int], 
                                    limit: int = 50) -> List[Dict[str, Any]]:
        """Get content filtered by category IDs."""
        try:
            # Get all posts from cache first
            cached_posts = await self.get_cached_data("posts")
            if cached_posts:
                # Filter by categories
                filtered_posts = [
                    post for post in cached_posts 
                    if any(cat_id in post.get("categories", []) for cat_id in category_ids)
                ]
                return filtered_posts[:limit]
            
            # Fallback to API call (less efficient)
            all_posts = []
            for category_id in category_ids:
                posts = await self.wp_client.fetch_resources(
                    per_page=min(limit, 100),
                    post_type="posts"
                )
                # Filter posts by category (WordPress API doesn't have direct category filter)
                category_posts = [
                    post for post in posts 
                    if category_id in post.get("categories", [])
                ]
                all_posts.extend(category_posts)
            
            return all_posts[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get content by category: {str(e)}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        wp_health = await self.wp_client.health_check()
        
        # Check cache connectivity
        cache_healthy = True
        try:
            await self.cache_manager.set("health_check", "ok", ttl=60)
            cache_result = await self.cache_manager.get("health_check")
            cache_healthy = cache_result == "ok"
        except Exception:
            cache_healthy = False
        
        # Check last sync status
        last_sync = await self._get_last_sync_time()
        sync_status = "never"
        if last_sync:
            hours_since_sync = (datetime.now(timezone.utc) - last_sync).total_seconds() / 3600
            if hours_since_sync < 1:
                sync_status = "recent"
            elif hours_since_sync < 24:
                sync_status = "stale"
            else:
                sync_status = "very_stale"
        
        return {
            "wordpress_api": wp_health,
            "cache_healthy": cache_healthy,
            "last_sync": last_sync.isoformat() if last_sync else None,
            "sync_status": sync_status,
            "service_status": "healthy" if wp_health.get("status") == "healthy" and cache_healthy else "degraded"
        }

    async def _get_last_sync_time(self) -> Optional[datetime]:
        """Get the last synchronization timestamp."""
        try:
            timestamp = await self.cache_manager.get("wp_last_sync")
            if timestamp:
                return datetime.fromisoformat(timestamp)
        except Exception:
            pass
        return None

    async def _update_last_sync_time(self) -> None:
        """Update the last synchronization timestamp."""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            await self.cache_manager.set("wp_last_sync", timestamp, ttl=86400 * 7)  # Keep for a week
        except Exception as e:
            self.logger.warning(f"Failed to update last sync time: {str(e)}")

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get detailed synchronization status."""
        last_sync = await self._get_last_sync_time()
        
        # Get cached data counts
        data_counts = {}
        for data_type in ["users", "posts", "categories", "tags"]:
            cached_data = await self.get_cached_data(data_type)
            data_counts[data_type] = len(cached_data) if cached_data else 0
        
        return {
            "last_sync": last_sync.isoformat() if last_sync else None,
            "data_counts": data_counts,
            "cache_status": "active" if any(data_counts.values()) else "empty"
        }