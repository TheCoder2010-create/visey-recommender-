from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
import httpx
import asyncio
import logging
from datetime import datetime, timezone

from ..config import settings
from ..utils.retry import retry_with_backoff
from ..utils.rate_limiter import SlidingWindowRateLimiter
from ..utils.validation import validate_wp_response

class WPClient:
    """Enhanced WordPress REST API client with retry logic, rate limiting, and comprehensive error handling.

    Features:
    - Automatic retries with exponential backoff
    - Rate limiting to respect WordPress API limits
    - Comprehensive error handling and logging
    - Support for multiple authentication methods
    - Batch operations for better performance
    - Data validation and sanitization
    """

    def __init__(self, base_url: Optional[str] = None, auth_type: Optional[str] = None, 
                 rate_limit: int = 60, timeout: int = 30):
        self.base_url = (base_url or settings.WP_BASE_URL).rstrip("/")
        self.auth_type = (auth_type or settings.WP_AUTH_TYPE).lower()
        self.rate_limiter = SlidingWindowRateLimiter(max_requests=rate_limit, window_seconds=60)
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        if not self.base_url:
            raise ValueError("WordPress base URL is required")

    def _auth_headers(self) -> Dict[str, str]:
        """Get authentication headers based on configured auth type."""
        headers: Dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "Visey-Recommender/1.0"
        }
        
        if self.auth_type == "jwt" and settings.WP_JWT_TOKEN:
            headers["Authorization"] = f"Bearer {settings.WP_JWT_TOKEN}"
        elif self.auth_type == "application_password" and settings.WP_APP_PASSWORD:
            headers["Authorization"] = f"Bearer {settings.WP_APP_PASSWORD}"
            
        return headers

    def _auth(self) -> Optional[httpx.Auth]:
        """Get authentication object for httpx client."""
        if self.auth_type == "basic" and settings.WP_USERNAME and settings.WP_PASSWORD:
            return httpx.BasicAuth(settings.WP_USERNAME, settings.WP_PASSWORD)
        return None

    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request with rate limiting and retry logic."""
        # Rate limiting check
        if not self.rate_limiter.is_allowed("wp_client"):
            await asyncio.sleep(1)  # Wait a bit if rate limited
        
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        async def _request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._auth_headers(),
                    auth=self._auth(),
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
        
        try:
            return await _request()
        except httpx.HTTPStatusError as e:
            self.logger.error(f"WordPress API error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"WordPress API request failed: {str(e)}")
            raise

    async def fetch_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Fetch entrepreneur profile from WordPress user endpoint.

        Args:
            user_id: WordPress user ID

        Returns:
            Dict with profile data: industry, stage, team_size, funding, location
            
        Raises:
            ValueError: If user_id is invalid
            httpx.HTTPStatusError: If API request fails
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError(f"Invalid user_id: {user_id}")
            
        url = f"{self.base_url}/wp-json/wp/v2/users/{user_id}"
        params = {"context": "edit"} if self.auth_type in ("basic", "jwt", "application_password") else {}
        
        self.logger.info(f"Fetching user profile for user_id: {user_id}")
        data = await self._make_request("GET", url, params=params)
        
        # Validate response structure
        validate_wp_response(data, required_fields=["id"])
        
        # Map typical meta structures with fallbacks
        meta = data.get("meta", {}) or data.get("acf", {}) or {}
        profile = {
            "id": data.get("id"),
            "name": data.get("name", ""),
            "email": data.get("email", ""),
            "industry": meta.get("industry") or data.get("industry") or "",
            "stage": meta.get("stage") or data.get("stage") or "",
            "team_size": meta.get("team_size") or data.get("team_size") or "",
            "funding": meta.get("funding") or data.get("funding") or "",
            "location": meta.get("location") or data.get("location") or "",
            "bio": data.get("description", ""),
            "registered_date": data.get("registered_date", ""),
        }
        
        self.logger.debug(f"Successfully fetched profile for user {user_id}")
        return profile

    async def fetch_resources(self, per_page: int = 100, page: int = 1, 
                            post_type: str = "posts", status: str = "publish",
                            modified_after: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch WordPress posts with categories, tags, and custom fields.
        
        Args:
            per_page: Number of posts per page (max 100)
            page: Page number to fetch
            post_type: WordPress post type (posts, pages, custom types)
            status: Post status filter (publish, draft, private)
            modified_after: Only fetch posts modified after this date
            
        Returns:
            List of resource dictionaries with comprehensive metadata
        """
        if per_page > 100:
            per_page = 100
            self.logger.warning("per_page capped at 100 due to WordPress API limits")
            
        url = f"{self.base_url}/wp-json/wp/v2/{post_type}"
        params = {
            "per_page": per_page,
            "page": page,
            "status": status,
            "_embed": "wp:term,author",
            "_fields": "id,link,title,categories,tags,meta,excerpt,content,date,modified,author,featured_media"
        }
        
        if modified_after:
            params["modified_after"] = modified_after.isoformat()
        
        self.logger.info(f"Fetching {post_type} page {page} (per_page: {per_page})")
        posts = await self._make_request("GET", url, params=params)
        
        if not isinstance(posts, list):
            raise ValueError(f"Expected list of posts, got {type(posts)}")

        resources: List[Dict[str, Any]] = []
        for p in posts:
            try:
                title = self._extract_rendered_content(p.get("title"))
                excerpt = self._extract_rendered_content(p.get("excerpt"))
                content = self._extract_rendered_content(p.get("content"))
                
                # Extract embedded data
                embedded = p.get("_embedded", {})
                categories_data = embedded.get("wp:term", [[]])[0] if embedded.get("wp:term") else []
                author_data = embedded.get("author", [{}])[0] if embedded.get("author") else {}
                
                resource = {
                    "id": p.get("id"),
                    "title": title or "",
                    "link": p.get("link", ""),
                    "excerpt": excerpt or "",
                    "content": content or "",
                    "categories": p.get("categories", []),
                    "tags": p.get("tags", []),
                    "meta": p.get("meta", {}),
                    "date": p.get("date", ""),
                    "modified": p.get("modified", ""),
                    "author_id": p.get("author", 0),
                    "author_name": author_data.get("name", ""),
                    "featured_media": p.get("featured_media", 0),
                    "category_names": [cat.get("name", "") for cat in categories_data if cat.get("taxonomy") == "category"],
                    "tag_names": [tag.get("name", "") for tag in categories_data if tag.get("taxonomy") == "post_tag"],
                }
                
                resources.append(resource)
                
            except Exception as e:
                self.logger.warning(f"Error processing post {p.get('id', 'unknown')}: {str(e)}")
                continue
        
        self.logger.info(f"Successfully fetched {len(resources)} resources")
        return resources

    def _extract_rendered_content(self, content_obj: Union[Dict, str, None]) -> str:
        """Extract rendered content from WordPress content object."""
        if isinstance(content_obj, dict):
            return content_obj.get("rendered", "")
        return content_obj or ""

    async def fetch_all_resources(self, post_type: str = "posts", 
                                modified_after: Optional[datetime] = None,
                                batch_size: int = 100) -> List[Dict[str, Any]]:
        """Fetch all resources with automatic pagination.
        
        Args:
            post_type: WordPress post type to fetch
            modified_after: Only fetch posts modified after this date
            batch_size: Number of posts per API request
            
        Returns:
            List of all resources across all pages
        """
        all_resources = []
        page = 1
        
        while True:
            try:
                resources = await self.fetch_resources(
                    per_page=batch_size, 
                    page=page, 
                    post_type=post_type,
                    modified_after=modified_after
                )
                
                if not resources:
                    break
                    
                all_resources.extend(resources)
                
                if len(resources) < batch_size:
                    break
                    
                page += 1
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 400:  # Bad request, likely no more pages
                    break
                raise
        
        self.logger.info(f"Fetched total of {len(all_resources)} resources")
        return all_resources

    async def fetch_categories(self) -> List[Dict[str, Any]]:
        """Fetch all WordPress categories."""
        url = f"{self.base_url}/wp-json/wp/v2/categories"
        params = {"per_page": 100, "_fields": "id,name,slug,description,count,parent"}
        
        categories = await self._make_request("GET", url, params=params)
        self.logger.info(f"Fetched {len(categories)} categories")
        return categories

    async def fetch_tags(self) -> List[Dict[str, Any]]:
        """Fetch all WordPress tags."""
        url = f"{self.base_url}/wp-json/wp/v2/tags"
        params = {"per_page": 100, "_fields": "id,name,slug,description,count"}
        
        tags = await self._make_request("GET", url, params=params)
        self.logger.info(f"Fetched {len(tags)} tags")
        return tags

    async def fetch_users(self, per_page: int = 100, page: int = 1, 
                         roles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Fetch WordPress users with optional role filtering.
        
        Args:
            per_page: Number of users per page
            page: Page number
            roles: List of user roles to filter by
            
        Returns:
            List of user data dictionaries
        """
        url = f"{self.base_url}/wp-json/wp/v2/users"
        params = {
            "per_page": min(per_page, 100),
            "page": page,
            "_fields": "id,name,email,registered_date,roles,meta"
        }
        
        if roles:
            params["roles"] = ",".join(roles)
        
        users = await self._make_request("GET", url, params=params)
        self.logger.info(f"Fetched {len(users)} users")
        return users

    async def fetch_custom_post_type(self, post_type: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch posts from a custom post type.
        
        Args:
            post_type: Custom post type slug
            **kwargs: Additional parameters for the request
            
        Returns:
            List of custom post type entries
        """
        return await self.fetch_resources(post_type=post_type, **kwargs)

    async def search_posts(self, query: str, per_page: int = 20, 
                          post_type: str = "posts") -> List[Dict[str, Any]]:
        """Search WordPress posts by query string.
        
        Args:
            query: Search query string
            per_page: Number of results per page
            post_type: Post type to search in
            
        Returns:
            List of matching posts
        """
        url = f"{self.base_url}/wp-json/wp/v2/{post_type}"
        params = {
            "search": query,
            "per_page": min(per_page, 100),
            "_fields": "id,title,link,excerpt,date,categories,tags"
        }
        
        results = await self._make_request("GET", url, params=params)
        self.logger.info(f"Search for '{query}' returned {len(results)} results")
        return results

    async def fetch_media(self, media_id: int) -> Dict[str, Any]:
        """Fetch WordPress media item by ID.
        
        Args:
            media_id: WordPress media ID
            
        Returns:
            Media item data
        """
        url = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
        params = {"_fields": "id,source_url,alt_text,caption,title,media_type,mime_type"}
        
        media = await self._make_request("GET", url, params=params)
        self.logger.debug(f"Fetched media item {media_id}")
        return media

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on WordPress API.
        
        Returns:
            Health status information
        """
        try:
            # Test basic API connectivity
            url = f"{self.base_url}/wp-json"
            response = await self._make_request("GET", url)
            
            # Test authentication if configured
            auth_status = "not_configured"
            if self.auth_type != "none":
                try:
                    auth_url = f"{self.base_url}/wp-json/wp/v2/users/me"
                    await self._make_request("GET", auth_url)
                    auth_status = "authenticated"
                except:
                    auth_status = "authentication_failed"
            
            return {
                "status": "healthy",
                "wordpress_version": response.get("description", ""),
                "api_version": response.get("gmt_offset", ""),
                "auth_type": self.auth_type,
                "auth_status": auth_status,
                "base_url": self.base_url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"WordPress health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "auth_type": self.auth_type,
                "base_url": self.base_url,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def get_site_info(self) -> Dict[str, Any]:
        """Get WordPress site information and capabilities."""
        try:
            url = f"{self.base_url}/wp-json"
            info = await self._make_request("GET", url)
            
            return {
                "name": info.get("name", ""),
                "description": info.get("description", ""),
                "url": info.get("url", ""),
                "home": info.get("home", ""),
                "gmt_offset": info.get("gmt_offset", 0),
                "timezone_string": info.get("timezone_string", ""),
                "namespaces": info.get("namespaces", []),
                "authentication": info.get("authentication", {}),
                "routes": list(info.get("routes", {}).keys())[:10]  # Limit for brevity
            }
        except Exception as e:
            self.logger.error(f"Failed to get site info: {str(e)}")
            return {"error": str(e)}