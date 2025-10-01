# WordPress API Integration

This document describes the WordPress REST API integration for the Visey Recommender system.

## Overview

The WordPress integration provides:
- Automatic data synchronization from WordPress sites
- User profile management
- Content fetching and caching
- Search capabilities
- Health monitoring
- Rate limiting and retry logic

## Configuration

### Environment Variables

```bash
# WordPress API Configuration
WP_BASE_URL=https://your-wordpress-site.com
WP_AUTH_TYPE=none  # Options: none, basic, jwt, application_password
WP_USERNAME=your_username  # For basic auth
WP_PASSWORD=your_password  # For basic auth
WP_JWT_TOKEN=your_jwt_token  # For JWT auth
WP_APP_PASSWORD=your_app_password  # For application password auth
WP_RATE_LIMIT=60  # Requests per minute
WP_TIMEOUT=30  # Request timeout in seconds
WP_BATCH_SIZE=100  # Default batch size for pagination
```

### Authentication Methods

#### 1. No Authentication (Public API)
```bash
WP_AUTH_TYPE=none
```
Only public data will be accessible.

#### 2. Basic Authentication
```bash
WP_AUTH_TYPE=basic
WP_USERNAME=your_username
WP_PASSWORD=your_password
```

#### 3. JWT Authentication
```bash
WP_AUTH_TYPE=jwt
WP_JWT_TOKEN=your_jwt_token
```
Requires JWT Authentication plugin.

#### 4. Application Password
```bash
WP_AUTH_TYPE=application_password
WP_APP_PASSWORD=your_app_password
```
WordPress 5.6+ application passwords.

## API Endpoints

### WordPress Data Management

#### Sync WordPress Data
```http
POST /wordpress/sync?incremental=true
```

Response:
```json
{
  "success": true,
  "users_synced": 150,
  "posts_synced": 1200,
  "categories_synced": 25,
  "tags_synced": 180,
  "duration": 45.2,
  "errors": [],
  "last_sync": "2023-12-01T10:30:00Z"
}
```

#### WordPress Health Check
```http
GET /wordpress/health
```

Response:
```json
{
  "wordpress_api": {
    "status": "healthy",
    "auth_status": "authenticated",
    "base_url": "https://example.com"
  },
  "cache_healthy": true,
  "last_sync": "2023-12-01T10:30:00Z",
  "sync_status": "recent",
  "service_status": "healthy"
}
```

#### Get User Profile
```http
GET /wordpress/users/{user_id}
```

Response:
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "industry": "technology",
  "stage": "growth",
  "team_size": "10-50",
  "funding": "series-a",
  "location": "San Francisco",
  "bio": "Entrepreneur and tech enthusiast",
  "registered_date": "2023-01-15T00:00:00"
}
```

#### Search Content
```http
GET /wordpress/search?q=artificial%20intelligence&limit=20
```

Response:
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "id": 456,
      "title": "AI in Business",
      "link": "https://example.com/ai-in-business",
      "excerpt": "How AI is transforming business...",
      "date": "2023-11-15T10:00:00"
    }
  ],
  "count": 1
}
```

#### Get Posts by Category
```http
GET /wordpress/categories/{category_id}/posts?limit=50
```

#### Get Cached Data
```http
GET /wordpress/data/{data_type}
```
Where `data_type` is one of: `users`, `posts`, `categories`, `tags`

## CLI Management

Use the WordPress manager CLI for administrative tasks:

```bash
# Test connection
python scripts/wp_manager.py test

# Sync all data (incremental)
python scripts/wp_manager.py sync

# Full sync (not incremental)
python scripts/wp_manager.py sync --full

# Sync specific data type
python scripts/wp_manager.py sync --type posts

# Show status
python scripts/wp_manager.py status

# Search content
python scripts/wp_manager.py search "artificial intelligence" --limit 10

# Get user profile
python scripts/wp_manager.py user 123

# Export cached data
python scripts/wp_manager.py export posts posts_export.json
```

## WordPress Client Usage

### Basic Usage

```python
from visey_recommender.clients.wp_client import WPClient

# Initialize client
client = WPClient(
    base_url="https://your-site.com",
    auth_type="basic",
    rate_limit=60,
    timeout=30
)

# Test connection
health = await client.health_check()
print(f"Status: {health['status']}")

# Fetch user profile
profile = await client.fetch_user_profile(user_id=123)

# Fetch posts
posts = await client.fetch_resources(per_page=50, page=1)

# Search posts
results = await client.search_posts("AI technology", per_page=20)

# Fetch all posts with pagination
all_posts = await client.fetch_all_resources(post_type="posts")
```

### Service Layer Usage

```python
from visey_recommender.services.wp_service import WordPressService

# Initialize service
service = WordPressService()

# Sync all data
result = await service.sync_all_data(incremental=True)

# Get cached user profile
profile = await service.get_user_profile(user_id=123, use_cache=True)

# Search content
results = await service.search_content("startup funding", limit=20)

# Get posts by category
posts = await service.get_content_by_category([1, 2, 3], limit=50)
```

## Data Models

### User Profile
```python
{
    "id": int,
    "name": str,
    "email": str,
    "industry": str,
    "stage": str,
    "team_size": str,
    "funding": str,
    "location": str,
    "bio": str,
    "registered_date": str,
    "roles": List[str],
    "last_updated": str
}
```

### Post/Resource
```python
{
    "id": int,
    "title": str,
    "content": str,
    "excerpt": str,
    "link": str,
    "categories": List[int],
    "tags": List[int],
    "category_names": List[str],
    "tag_names": List[str],
    "author_id": int,
    "author_name": str,
    "date": str,
    "modified": str,
    "featured_media": int,
    "meta": Dict[str, Any],
    "last_updated": str
}
```

## Error Handling

The WordPress integration includes comprehensive error handling:

- **Connection Errors**: Automatic retries with exponential backoff
- **Rate Limiting**: Built-in rate limiting to respect API limits
- **Authentication Errors**: Clear error messages for auth issues
- **Data Validation**: Input validation and sanitization
- **Timeout Handling**: Configurable timeouts for requests

## Monitoring and Metrics

### Health Checks
- WordPress API connectivity
- Authentication status
- Cache health
- Data freshness

### Metrics Tracked
- Request success/failure rates
- Response times
- Data sync statistics
- Cache hit rates
- Error rates by type

## Performance Optimization

### Caching Strategy
- User profiles: 1 hour TTL
- Posts: 30 minutes TTL
- Categories/Tags: 2 hours TTL
- Search results: 15 minutes TTL

### Batch Operations
- Automatic pagination for large datasets
- Configurable batch sizes
- Parallel processing where possible

### Rate Limiting
- Configurable requests per minute
- Automatic backoff on rate limit hits
- Request queuing and throttling

## Troubleshooting

### Common Issues

#### Connection Failed
```bash
# Test connection
python scripts/wp_manager.py test
```
Check:
- WP_BASE_URL is correct
- WordPress site is accessible
- Firewall/network issues

#### Authentication Failed
Check:
- Credentials are correct
- Authentication method is supported
- User has necessary permissions

#### Slow Performance
- Increase WP_BATCH_SIZE for faster syncing
- Reduce WP_RATE_LIMIT if hitting limits
- Check network latency

#### Data Not Syncing
- Check last sync time: `python scripts/wp_manager.py status`
- Run manual sync: `python scripts/wp_manager.py sync --full`
- Check error logs

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger("visey_recommender.clients.wp_client").setLevel(logging.DEBUG)
```

## WordPress Plugin Requirements

For full functionality, consider installing these WordPress plugins:

1. **JWT Authentication for WP REST API** - For JWT auth
2. **Advanced Custom Fields (ACF)** - For custom user/post fields
3. **WP REST API Controller** - Enhanced REST API features
4. **Application Passwords** - Built into WordPress 5.6+

## Security Considerations

- Use HTTPS for all WordPress API calls
- Store credentials securely (environment variables)
- Implement proper authentication
- Regular security updates
- Monitor for suspicious activity
- Use application passwords instead of user passwords when possible

## Best Practices

1. **Incremental Syncing**: Use incremental sync for regular updates
2. **Error Monitoring**: Monitor sync errors and failures
3. **Cache Management**: Implement appropriate cache TTLs
4. **Rate Limiting**: Respect WordPress API rate limits
5. **Data Validation**: Validate all incoming data
6. **Logging**: Comprehensive logging for debugging
7. **Testing**: Regular testing of API connectivity
8. **Backup**: Regular backups of cached data