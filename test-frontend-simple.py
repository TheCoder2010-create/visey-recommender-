#!/usr/bin/env python3
"""
Simple test script for Visey Recommender Frontend
Starts a minimal API server for testing the frontend
"""

import os
import sys
import asyncio
import uvicorn
from pathlib import Path

# Set environment variables for testing
os.environ['WP_BASE_URL'] = 'https://demo.wp-api.org'
os.environ['WP_AUTH_TYPE'] = 'none'
os.environ['CACHE_BACKEND'] = 'sqlite'

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

# Create a simple test API
app = FastAPI(
    title="Visey Recommender Test API", 
    version="0.1.0",
    description="Simplified API for frontend testing"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test data
TEST_USERS = {
    1: {
        "id": 1,
        "name": "Test User",
        "email": "test@example.com",
        "industry": "technology",
        "stage": "growth",
        "team_size": "10-50",
        "funding": "series-a",
        "location": "San Francisco",
        "bio": "Test user for demo",
        "registered_date": "2023-01-15T00:00:00"
    }
}

TEST_POSTS = [
    {
        "id": 1,
        "title": "Building Scalable Systems",
        "link": "https://example.com/scalable-systems",
        "excerpt": "Learn how to build scalable systems for your startup",
        "categories": [1, 2],
        "tags": [1, 2],
        "category_names": ["Technology", "Startup"],
        "tag_names": ["Scalability", "Architecture"]
    },
    {
        "id": 2,
        "title": "Fundraising Guide",
        "link": "https://example.com/fundraising",
        "excerpt": "Complete guide to startup fundraising",
        "categories": [2, 3],
        "tags": [3, 4],
        "category_names": ["Startup", "Funding"],
        "tag_names": ["Investment", "Pitch"]
    }
]

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "visey-recommender-test"
    }

@app.get("/recommend")
async def recommend(user_id: int, top_n: int = 10):
    """Get recommendations for a user."""
    if user_id not in TEST_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Simulate processing time
    await asyncio.sleep(0.1)
    
    recommendations = [
        {
            "resource_id": 1,
            "title": "Building Scalable Systems",
            "link": "https://example.com/scalable-systems",
            "score": 0.95,
            "reason": "Matches your technology interests"
        },
        {
            "resource_id": 2,
            "title": "Fundraising Guide", 
            "link": "https://example.com/fundraising",
            "score": 0.82,
            "reason": "Relevant for your growth stage"
        }
    ]
    
    return {
        "user_id": user_id,
        "items": recommendations[:top_n]
    }

@app.get("/wordpress/health")
async def wordpress_health():
    """WordPress health check."""
    return {
        "wordpress_api": {
            "status": "healthy",
            "auth_status": "test_mode",
            "base_url": "https://demo.wp-api.org"
        },
        "cache_healthy": True,
        "last_sync": "2024-01-15T10:30:00Z",
        "sync_status": "recent",
        "service_status": "healthy"
    }

@app.get("/wordpress/users/{user_id}")
async def get_user(user_id: int):
    """Get user profile."""
    if user_id not in TEST_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    return TEST_USERS[user_id]

@app.get("/wordpress/search")
async def search_content(q: str, limit: int = 10):
    """Search content."""
    # Simple search in test data
    results = [post for post in TEST_POSTS if q.lower() in post["title"].lower()]
    
    return {
        "query": q,
        "results": results[:limit],
        "count": len(results)
    }

@app.get("/wordpress/data/{data_type}")
async def get_cached_data(data_type: str):
    """Get cached data."""
    data_counts = {
        "posts": len(TEST_POSTS),
        "users": len(TEST_USERS),
        "categories": 5,
        "tags": 10
    }
    
    if data_type == "posts":
        data = TEST_POSTS
    elif data_type == "users":
        data = list(TEST_USERS.values())
    else:
        data = []
    
    return {
        "data": data,
        "count": data_counts.get(data_type, 0),
        "cached": True
    }

@app.post("/wordpress/sync")
async def sync_wordpress():
    """Sync WordPress data."""
    # Simulate sync process
    await asyncio.sleep(1)
    
    return {
        "success": True,
        "users_synced": 1,
        "posts_synced": 2,
        "categories_synced": 5,
        "tags_synced": 10,
        "duration": 1.2,
        "errors": [],
        "last_sync": "2024-01-15T10:30:00Z",
        "triggered_by": "manual"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return "# Test metrics\ntest_metric 1.0\n"

if __name__ == "__main__":
    print("🚀 Starting Visey Recommender Test API...")
    print("📊 API will be available at: http://localhost:8000")
    print("📋 Test endpoints:")
    print("   - Health: http://localhost:8000/health")
    print("   - Docs: http://localhost:8000/docs")
    print("   - Recommend: http://localhost:8000/recommend?user_id=1")
    print("⏹️  Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )