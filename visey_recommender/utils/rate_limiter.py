"""Rate limiting utilities for API endpoints and external calls."""

import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
import structlog
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = structlog.get_logger(__name__)


class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens available
        """
        now = time.time()
        
        # Add tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class SlidingWindowRateLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Args:
            max_requests: Maximum requests allowed in the window
            window_seconds: Size of the sliding window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key.
        
        Args:
            key: Identifier for the rate limit (e.g., IP address, user ID)
            
        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Remove old requests outside the window
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        # Check if we're under the limit
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            return True
        
        return False
    
    def get_reset_time(self, key: str) -> Optional[float]:
        """Get the time when the rate limit will reset for the key."""
        if not self.requests[key]:
            return None
        return self.requests[key][0] + self.window_seconds


class RateLimitManager:
    """Centralized rate limit management."""
    
    def __init__(self):
        self.limiters: Dict[str, SlidingWindowRateLimiter] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
    
    def add_rate_limit(self, name: str, max_requests: int, window_seconds: int):
        """Add a sliding window rate limiter."""
        self.limiters[name] = SlidingWindowRateLimiter(max_requests, window_seconds)
        logger.info("rate_limiter_added", name=name, max_requests=max_requests, window_seconds=window_seconds)
    
    def add_token_bucket(self, name: str, capacity: int, refill_rate: float):
        """Add a token bucket rate limiter."""
        self.token_buckets[name] = TokenBucket(capacity, refill_rate)
        logger.info("token_bucket_added", name=name, capacity=capacity, refill_rate=refill_rate)
    
    def check_rate_limit(self, limiter_name: str, key: str) -> tuple[bool, Optional[float]]:
        """Check if request is allowed by the specified rate limiter.
        
        Returns:
            Tuple of (is_allowed, reset_time)
        """
        if limiter_name in self.limiters:
            limiter = self.limiters[limiter_name]
            is_allowed = limiter.is_allowed(key)
            reset_time = limiter.get_reset_time(key)
            
            if not is_allowed:
                logger.warning("rate_limit_exceeded", 
                             limiter=limiter_name, key=key, reset_time=reset_time)
            
            return is_allowed, reset_time
        
        return True, None
    
    def consume_tokens(self, bucket_name: str, tokens: int = 1) -> bool:
        """Try to consume tokens from the specified bucket."""
        if bucket_name in self.token_buckets:
            bucket = self.token_buckets[bucket_name]
            success = bucket.consume(tokens)
            
            if not success:
                logger.warning("token_bucket_exhausted", bucket=bucket_name, tokens_requested=tokens)
            
            return success
        
        return True


# Global rate limit manager
rate_limit_manager = RateLimitManager()

# Default rate limits
rate_limit_manager.add_rate_limit("api_general", max_requests=100, window_seconds=60)  # 100 req/min
rate_limit_manager.add_rate_limit("api_recommend", max_requests=20, window_seconds=60)  # 20 req/min
rate_limit_manager.add_rate_limit("api_feedback", max_requests=50, window_seconds=60)  # 50 req/min
rate_limit_manager.add_token_bucket("wp_api", capacity=10, refill_rate=2.0)  # 2 tokens/sec, burst of 10


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    client_ip = get_client_ip(request)
    path = request.url.path
    
    # Determine which rate limiter to use based on path
    limiter_name = "api_general"
    if "/recommend" in path:
        limiter_name = "api_recommend"
    elif "/feedback" in path:
        limiter_name = "api_feedback"
    
    # Check rate limit
    is_allowed, reset_time = rate_limit_manager.check_rate_limit(limiter_name, client_ip)
    
    if not is_allowed:
        headers = {}
        if reset_time:
            headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": reset_time},
            headers=headers
        )
    
    response = await call_next(request)
    return response


def rate_limit(limiter_name: str):
    """Decorator for rate limiting specific functions."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # For API endpoints, we'll use IP-based limiting
            # For internal functions, we can use a generic key
            key = "internal"
            
            is_allowed, reset_time = rate_limit_manager.check_rate_limit(limiter_name, key)
            if not is_allowed:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded for {limiter_name}",
                    headers={"X-RateLimit-Reset": str(int(reset_time)) if reset_time else None}
                )
            
            return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            key = "internal"
            
            is_allowed, reset_time = rate_limit_manager.check_rate_limit(limiter_name, key)
            if not is_allowed:
                raise Exception(f"Rate limit exceeded for {limiter_name}")
            
            return func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator