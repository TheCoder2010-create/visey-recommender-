# WordPress API Architecture

## Current Implementation: Hybrid Approach

Your project now uses a **hybrid caching + real-time** approach for optimal performance and reliability.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Request  │───▶│  Recommendation  │───▶│   WordPress     │
│  /recommend     │    │     Engine       │    │     Cache       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                        ▼
                                │               ┌─────────────────┐
                                │               │  Background     │
                                │               │   Scheduler     │
                                │               │ (Every 30min)   │
                                │               └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Real-time API  │    │  WordPress API  │
                       │   (Fallback)    │    │   (Batch Sync)  │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 How It Works

### 1. **Recommendation Requests** (Cache-First)
```python
# When user requests recommendations:
profile_data = await wp_service.get_user_profile(user_id, use_cache=True)
resources_data = await wp_service.get_cached_data("posts")
```

**Flow:**
1. **User Profile**: Check cache first, fallback to real-time API if needed
2. **Posts/Resources**: Use cached data only (no real-time fallback)
3. **Fast Response**: ~50-100ms instead of 500-2000ms

### 2. **Background Synchronization** (Every 30 minutes)
```python
# Automatic background sync:
sync_result = await wp_service.sync_all_data(incremental=True)
```

**What gets synced:**
- ✅ User profiles and metadata
- ✅ Posts, pages, custom post types
- ✅ Categories and tags
- ✅ Only changed content (incremental)

### 3. **Manual Sync** (On-demand)
```bash
# CLI
python scripts/wp_manager.py sync

# API
curl -X POST http://localhost:8000/wordpress/sync
```

## 📊 Performance Comparison

| Approach | Latency | WordPress Load | Reliability | Data Freshness |
|----------|---------|----------------|-------------|----------------|
| **Real-time** | 500-2000ms | High | Low | Real-time |
| **Cache-only** | 50-100ms | None | High | 30min delay |
| **Hybrid (Current)** | 50-200ms | Low | High | 30min delay |

## 🔧 Configuration

### Environment Variables
```bash
# WordPress API
WP_BASE_URL=https://your-site.com
WP_AUTH_TYPE=basic
WP_USERNAME=your_user
WP_PASSWORD=your_pass

# Sync Behavior
WP_SYNC_INTERVAL=30          # Background sync every 30 minutes
WP_CACHE_FALLBACK=true       # Use cache-first approach
WP_RATE_LIMIT=60            # API rate limit (req/min)
WP_BATCH_SIZE=100           # Batch size for syncing
```

### Cache TTLs
- **User Profiles**: 1 hour
- **Posts**: 30 minutes  
- **Categories/Tags**: 2 hours
- **Search Results**: 15 minutes

## 🎯 Current Behavior

### ✅ What Uses Cache (Fast)
- **Recommendations** - Uses cached posts + user profiles
- **Search** - Uses cached data when available
- **Category filtering** - Uses cached posts
- **User profiles** - Cache first, API fallback

### ⚡ What Uses Real-time API (Slower)
- **User profile fallback** - If not in cache
- **Manual sync operations**
- **Health checks**
- **New user first-time access**

## 🔄 Data Flow Examples

### Recommendation Request
```
1. User requests recommendations for user_id=123
2. Check cache for user profile → Found ✅
3. Get cached posts → Found 1,200 posts ✅
4. Generate recommendations → 50ms response ✅
```

### New User (Not in Cache)
```
1. User requests recommendations for user_id=999
2. Check cache for user profile → Not found ❌
3. Fetch from WordPress API → 300ms ⚠️
4. Cache the profile → Cached for next time ✅
5. Get cached posts → Found ✅
6. Generate recommendations → 350ms response ⚠️
```

### Background Sync
```
1. Every 30 minutes, scheduler runs
2. Fetch modified posts since last sync
3. Fetch new/updated users
4. Update cache with fresh data
5. Next recommendations use fresh data ✅
```

## 🛠️ Management Commands

### Check Current Status
```bash
python scripts/wp_manager.py status
```
Shows:
- Cache vs real-time mode
- Last sync time
- Data counts
- Health status

### Force Immediate Sync
```bash
python scripts/wp_manager.py sync --full
```

### Test WordPress Connection
```bash
python scripts/wp_manager.py test
```

## 📈 Monitoring

### API Endpoints
```bash
# Check scheduler status
GET /wordpress/scheduler/status

# WordPress health
GET /wordpress/health

# Trigger manual sync
POST /wordpress/sync
```

### Metrics Tracked
- Cache hit/miss rates
- Sync success/failure
- API response times
- Data freshness
- Error rates

## 🚨 Troubleshooting

### Slow Recommendations
**Cause**: Cache miss, falling back to real-time API
**Solution**: 
```bash
# Check cache status
python scripts/wp_manager.py status

# Force sync to populate cache
python scripts/wp_manager.py sync
```

### Stale Data
**Cause**: Background sync failing
**Solution**:
```bash
# Check sync errors
curl http://localhost:8000/wordpress/health

# Manual sync
python scripts/wp_manager.py sync --full
```

### High WordPress Load
**Cause**: Too frequent syncing or large batch sizes
**Solution**:
```bash
# Increase sync interval
export WP_SYNC_INTERVAL=60  # 1 hour

# Reduce batch size
export WP_BATCH_SIZE=50
```

## 🎛️ Tuning for Your Needs

### High-Traffic Sites (Optimize for Speed)
```bash
WP_SYNC_INTERVAL=60        # Sync less frequently
WP_CACHE_FALLBACK=true     # Always use cache
WP_BATCH_SIZE=200          # Larger batches
```

### Content-Heavy Sites (Optimize for Freshness)
```bash
WP_SYNC_INTERVAL=15        # Sync more frequently
WP_CACHE_FALLBACK=true     # Still use cache
WP_BATCH_SIZE=50           # Smaller batches
```

### Development/Testing (Real-time)
```bash
WP_SYNC_INTERVAL=5         # Very frequent sync
WP_CACHE_FALLBACK=false    # Direct API calls
```

## 🔮 Future Enhancements

1. **Webhook Support** - Real-time updates when WordPress content changes
2. **Smart Caching** - Cache popular content longer
3. **Distributed Caching** - Redis cluster for multiple instances
4. **Content Prioritization** - Sync important content first
5. **A/B Testing** - Compare cache vs real-time performance