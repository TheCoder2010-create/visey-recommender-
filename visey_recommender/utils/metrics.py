"""Metrics collection for monitoring and observability."""

import time
from typing import Dict, Optional
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import structlog

logger = structlog.get_logger(__name__)

# Create a custom registry for our metrics
REGISTRY = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    'visey_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'visey_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

RECOMMENDATION_COUNT = Counter(
    'visey_recommendations_total',
    'Total number of recommendations generated',
    ['user_type'],
    registry=REGISTRY
)

CACHE_OPERATIONS = Counter(
    'visey_cache_operations_total',
    'Cache operations',
    ['operation', 'result'],
    registry=REGISTRY
)

WP_API_CALLS = Counter(
    'visey_wp_api_calls_total',
    'WordPress API calls',
    ['endpoint', 'status'],
    registry=REGISTRY
)

ACTIVE_USERS = Gauge(
    'visey_active_users',
    'Number of active users',
    registry=REGISTRY
)

RECOMMENDATION_SCORES = Histogram(
    'visey_recommendation_scores',
    'Distribution of recommendation scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=REGISTRY
)


class MetricsCollector:
    """Centralized metrics collection."""
    
    def __init__(self):
        self.active_requests = 0
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        logger.info("request_completed", 
                   method=method, endpoint=endpoint, status=status, duration=duration)
    
    def record_recommendation(self, user_type: str, scores: list[float]):
        """Record recommendation generation metrics."""
        RECOMMENDATION_COUNT.labels(user_type=user_type).inc()
        for score in scores:
            RECOMMENDATION_SCORES.observe(score)
        logger.info("recommendations_generated", 
                   user_type=user_type, count=len(scores), avg_score=sum(scores)/len(scores) if scores else 0)
    
    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        CACHE_OPERATIONS.labels(operation=operation, result=result).inc()
    
    def record_wp_api_call(self, endpoint: str, status: int):
        """Record WordPress API call metrics."""
        WP_API_CALLS.labels(endpoint=endpoint, status=str(status)).inc()
    
    def update_active_users(self, count: int):
        """Update active users gauge."""
        ACTIVE_USERS.set(count)


# Global metrics collector instance
metrics = MetricsCollector()


def track_time(metric_name: str = None):
    """Decorator to track execution time of functions."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info("function_completed", 
                           function=func.__name__, duration=duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error("function_failed", 
                            function=func.__name__, duration=duration, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info("function_completed", 
                           function=func.__name__, duration=duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error("function_failed", 
                            function=func.__name__, duration=duration, error=str(e))
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator


def get_metrics() -> str:
    """Get current metrics in Prometheus format."""
    return generate_latest(REGISTRY).decode('utf-8')

def track_operation(operation_name: str):
    """Decorator to track operations with custom metrics."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info("operation_completed", 
                           operation=operation_name, duration=duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error("operation_failed", 
                            operation=operation_name, duration=duration, error=str(e))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info("operation_completed", 
                           operation=operation_name, duration=duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error("operation_failed", 
                            operation=operation_name, duration=duration, error=str(e))
                raise
        
        return async_wrapper if hasattr(func, '__code__') and func.__code__.co_flags & 0x80 else sync_wrapper
    return decorator