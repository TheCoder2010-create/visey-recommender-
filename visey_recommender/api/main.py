from __future__ import annotations
from typing import List, Dict, Any
import time

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from ..clients.wp_client import WPClient
from ..config import settings
from ..data.models import Resource, UserProfile
from ..recommender.baseline import BaselineRecommender
from ..storage.feedback_store import FeedbackStore
from ..utils.logging import setup_logging, get_logger
from ..utils.metrics import metrics, get_metrics
from ..utils.health import health_checker
from ..utils.rate_limiter import rate_limit_middleware, get_client_ip
from ..utils.validation import (
    validate_request_data, 
    RecommendationRequestValidator, 
    FeedbackRequestValidator
)
from .schemas import FeedbackResponse, RecommendResponse, RecommendResponseItem

# Setup logging
setup_logging(
    level="INFO",
    json_logs=True,
    service_name="visey-recommender"
)

logger = get_logger(__name__)

app = FastAPI(
    title="Visey Recommendation Service", 
    version="0.2.0",
    description="AI-powered WordPress resource recommendations for entrepreneurs",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Initialize components
wp = WPClient()
recommender = BaselineRecommender()
feedback_store = FeedbackStore()

# Initialize WordPress service and scheduler
from ..services.wp_service import WordPressService
from ..tasks.scheduler import wp_scheduler
wp_service = WordPressService(wp_client=wp)

logger.info("visey_recommender_started", version="0.2.0")

@app.get("/recommend", response_model=RecommendResponse)
async def recommend(request: Request, user_id: int, top_n: int | None = None):
    """Generate personalized recommendations for a user."""
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    # Validate request parameters
    request_data = {"user_id": user_id, "top_n": top_n}
    validated_data = validate_request_data(request_data, RecommendationRequestValidator)
    
    logger.info("recommendation_request", 
               user_id=user_id, top_n=top_n, client_ip=client_ip)
    
    try:
        if not settings.WP_BASE_URL:
            raise HTTPException(status_code=500, detail="WP_BASE_URL not configured")

        # 1) Fetch profile and resources from WordPress (using cache when possible)
        profile_data = await wp_service.get_user_profile(user_id, use_cache=True)
        if not profile_data:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get cached resources first, fallback to API if needed
        resources_data = await wp_service.get_cached_data("posts")
        if not resources_data:
            # Fallback to real-time API call if no cached data
            logger.warning("No cached posts found, falling back to real-time API call")
            resources_data = await wp.fetch_resources(per_page=200, page=1)

        # 2) Build models
        profile = UserProfile(user_id=user_id, **profile_data)
        resources: List[Resource] = [Resource(**r) for r in resources_data]

        # 3) Generate recommendations
        recs = recommender.recommend(profile, resources, top_n=validated_data.get("top_n"))

        # 4) Build response
        items = [
            RecommendResponseItem(
                resource_id=r.resource_id,
                title=r.title,
                link=r.link,
                score=round(r.score, 4),
                reason=r.reason,
            )
            for r in recs
        ]
        
        response = RecommendResponse(user_id=user_id, items=items)
        
        # Record metrics
        duration = time.time() - start_time
        scores = [item.score for item in items]
        user_type = "returning" if len(scores) > 0 else "new"
        
        metrics.record_request("GET", "/recommend", 200, duration)
        metrics.record_recommendation(user_type, scores)
        
        logger.info("recommendation_success", 
                   user_id=user_id, 
                   recommendations_count=len(items),
                   duration=duration)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        metrics.record_request("GET", "/recommend", 500, duration)
        
        logger.error("recommendation_failed", 
                    user_id=user_id, 
                    error=str(e), 
                    duration=duration)
        
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during recommendation generation"
        )

@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(request: Request, user_id: int, resource_id: int, rating: int | None = None):
    """Record user feedback on a recommendation."""
    start_time = time.time()
    client_ip = get_client_ip(request)
    
    # Validate request parameters
    request_data = {"user_id": user_id, "resource_id": resource_id, "rating": rating}
    validated_data = validate_request_data(request_data, FeedbackRequestValidator)
    
    logger.info("feedback_request", 
               user_id=user_id, resource_id=resource_id, rating=rating, client_ip=client_ip)
    
    try:
        if rating is not None and (rating < 1 or rating > 5):
            raise HTTPException(status_code=400, detail="rating must be 1-5 if provided")
        
        feedback_store.upsert_feedback(
            user_id=validated_data["user_id"], 
            resource_id=validated_data["resource_id"], 
            rating=validated_data.get("rating")
        )
        
        duration = time.time() - start_time
        metrics.record_request("POST", "/feedback", 200, duration)
        
        logger.info("feedback_success", 
                   user_id=user_id, 
                   resource_id=resource_id, 
                   rating=rating,
                   duration=duration)
        
        return FeedbackResponse(ok=True)
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        metrics.record_request("POST", "/feedback", 500, duration)
        
        logger.error("feedback_failed", 
                    user_id=user_id, 
                    resource_id=resource_id, 
                    error=str(e), 
                    duration=duration)
        
        raise HTTPException(
            status_code=500, 
            detail="Internal server error during feedback processing"
        )


# Health and monitoring endpoints
@app.get("/health")
async def health():
    """Comprehensive health check endpoint."""
    try:
        health_result = await health_checker.run_all_checks()
        status_code = 200 if health_result["status"] == "healthy" else 503
        
        return health_result
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


@app.get("/health/ready")
async def readiness():
    """Readiness probe for Kubernetes."""
    try:
        readiness_result = await health_checker.get_readiness()
        status_code = 200 if readiness_result["ready"] else 503
        
        return readiness_result
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {"ready": False, "error": str(e)}


@app.get("/health/live")
async def liveness():
    """Liveness probe for Kubernetes."""
    try:
        liveness_result = await health_checker.get_liveness()
        return liveness_result
    except Exception as e:
        logger.error("liveness_check_failed", error=str(e))
        return {"alive": False, "error": str(e)}


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    try:
        return get_metrics()
    except Exception as e:
        logger.error("metrics_export_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@app.get("/status")
async def status():
    """Service status and information endpoint."""
    from ..data.pipeline import pipeline
    
    try:
        pipeline_status = await pipeline.get_pipeline_status()
        wp_sync_status = await wp_service.get_sync_status()
        
        return {
            "service": "visey-recommender",
            "version": "0.2.0",
            "status": "running",
            "timestamp": time.time(),
            "config": {
                "wp_base_url": settings.WP_BASE_URL[:50] + "..." if len(settings.WP_BASE_URL) > 50 else settings.WP_BASE_URL,
                "cache_backend": settings.CACHE_BACKEND,
                "top_n": settings.TOP_N,
                "weights": {
                    "content": settings.CONTENT_WEIGHT,
                    "collaborative": settings.COLLAB_WEIGHT,
                    "popularity": settings.POP_WEIGHT,
                    "embedding": settings.EMB_WEIGHT
                }
            },
            "pipeline": pipeline_status,
            "wordpress": wp_sync_status
        }
    except Exception as e:
        logger.error("status_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get service status")


# WordPress API endpoints
@app.post("/wordpress/sync")
async def sync_wordpress_data(incremental: bool = True):
    """Trigger WordPress data synchronization."""
    try:
        logger.info("wordpress_sync_triggered", incremental=incremental)
        
        # Use scheduler's force sync for consistency
        sync_result = await wp_scheduler.force_sync(incremental=incremental)
        
        logger.info("wordpress_sync_completed", 
                   users=sync_result.users_synced,
                   posts=sync_result.posts_synced,
                   duration=sync_result.sync_duration)
        
        return {
            "success": True,
            "users_synced": sync_result.users_synced,
            "posts_synced": sync_result.posts_synced,
            "categories_synced": sync_result.categories_synced,
            "tags_synced": sync_result.tags_synced,
            "duration": sync_result.sync_duration,
            "errors": sync_result.errors,
            "last_sync": sync_result.last_sync.isoformat(),
            "triggered_by": "manual"
        }
        
    except Exception as e:
        logger.error("wordpress_sync_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"WordPress sync failed: {str(e)}")


@app.get("/wordpress/scheduler/status")
async def get_scheduler_status():
    """Get WordPress sync scheduler status."""
    try:
        sync_status = await wp_service.get_sync_status()
        
        return {
            "scheduler_running": wp_scheduler.is_running(),
            "sync_interval_minutes": settings.WP_SYNC_INTERVAL,
            "last_sync": sync_status["last_sync"],
            "cache_status": sync_status["cache_status"],
            "data_counts": sync_status["data_counts"],
            "cache_fallback_enabled": settings.WP_CACHE_FALLBACK
        }
        
    except Exception as e:
        logger.error("scheduler_status_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@app.get("/wordpress/health")
async def wordpress_health():
    """Check WordPress API connectivity and health."""
    try:
        health_result = await wp_service.health_check()
        
        status_code = 200 if health_result.get("service_status") == "healthy" else 503
        return health_result
        
    except Exception as e:
        logger.error("wordpress_health_check_failed", error=str(e))
        raise HTTPException(status_code=503, detail=f"WordPress health check failed: {str(e)}")


@app.get("/wordpress/users/{user_id}")
async def get_wordpress_user(user_id: int):
    """Get WordPress user profile by ID."""
    try:
        profile = await wp_service.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="User not found")
            
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("wordpress_user_fetch_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")


@app.get("/wordpress/search")
async def search_wordpress_content(q: str, limit: int = 20):
    """Search WordPress content."""
    try:
        if not q or len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
            
        if limit > 100:
            limit = 100
            
        results = await wp_service.search_content(q.strip(), limit=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("wordpress_search_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/wordpress/categories/{category_id}/posts")
async def get_posts_by_category(category_id: int, limit: int = 50):
    """Get WordPress posts by category ID."""
    try:
        if limit > 100:
            limit = 100
            
        posts = await wp_service.get_content_by_category([category_id], limit=limit)
        
        return {
            "category_id": category_id,
            "posts": posts,
            "count": len(posts)
        }
        
    except Exception as e:
        logger.error("wordpress_category_posts_failed", category_id=category_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")


@app.get("/wordpress/data/{data_type}")
async def get_cached_wordpress_data(data_type: str):
    """Get cached WordPress data by type (users, posts, categories, tags)."""
    try:
        valid_types = ["users", "posts", "categories", "tags"]
        if data_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid data type. Must be one of: {valid_types}")
            
        data = await wp_service.get_cached_data(data_type)
        
        if data is None:
            return {"data": [], "count": 0, "cached": False}
            
        return {
            "data": data,
            "count": len(data),
            "cached": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("wordpress_cached_data_failed", data_type=data_type, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch cached data: {str(e)}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with logging."""
    logger.warning("http_exception", 
                  path=request.url.path, 
                  method=request.method,
                  status_code=exc.status_code, 
                  detail=exc.detail)
    
    return {"error": exc.detail, "status_code": exc.status_code}


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled errors."""
    logger.error("unhandled_exception", 
                path=request.url.path, 
                method=request.method,
                error=str(exc), 
                error_type=type(exc).__name__)
    
    return {"error": "Internal server error", "status_code": 500}


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("application_startup", version="0.2.0")
    
    # Initialize health checker
    await health_checker.run_all_checks()
    
    # Run initial WordPress data sync
    try:
        logger.info("Running initial WordPress data sync...")
        sync_result = await wp_service.sync_all_data(incremental=True)
        logger.info("WordPress sync completed", 
                   posts=sync_result.posts_synced,
                   users=sync_result.users_synced,
                   duration=sync_result.sync_duration)
    except Exception as e:
        logger.warning("startup_wordpress_sync_failed", error=str(e))
    
    # Start background WordPress sync scheduler
    try:
        await wp_scheduler.start(sync_interval_minutes=settings.WP_SYNC_INTERVAL)
        logger.info("WordPress background scheduler started")
    except Exception as e:
        logger.warning("scheduler_start_failed", error=str(e))
    
    # Run data pipeline sync if needed
    try:
        from ..data.pipeline import pipeline
        await pipeline.incremental_sync(max_age_hours=24)
    except Exception as e:
        logger.warning("startup_data_sync_failed", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("application_shutdown")
    
    # Stop background scheduler
    try:
        await wp_scheduler.stop()
        logger.info("WordPress scheduler stopped")
    except Exception as e:
        logger.warning("scheduler_stop_failed", error=str(e))