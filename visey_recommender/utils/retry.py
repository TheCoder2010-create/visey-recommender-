"""Retry utilities with exponential backoff and circuit breaker pattern."""

import asyncio
import time
from typing import Any, Callable, Optional, Type, Union
from functools import wraps
import structlog

logger = structlog.get_logger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """Circuit breaker implementation to prevent cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def _can_attempt(self) -> bool:
        """Check if we can attempt the operation."""
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = 'CLOSED'
        logger.info("circuit_breaker_closed", state=self.state)
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning("circuit_breaker_opened", 
                          failure_count=self.failure_count, state=self.state)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if not self._can_attempt():
            raise CircuitBreakerError(f"Circuit breaker is {self.state}")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None
):
    """Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Whether to add random jitter to delays
        exceptions: Tuple of exceptions to retry on
        circuit_breaker: Optional circuit breaker instance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if circuit_breaker:
                        return await circuit_breaker.call(func, *args, **kwargs)
                    else:
                        return await func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error("retry_exhausted", 
                                   function=func.__name__, 
                                   attempts=max_attempts, 
                                   error=str(e))
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    if jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
                    
                    logger.warning("retry_attempt", 
                                 function=func.__name__, 
                                 attempt=attempt + 1, 
                                 delay=delay, 
                                 error=str(e))
                    
                    await asyncio.sleep(delay)
            
            raise RetryError(f"Failed after {max_attempts} attempts: {last_exception}")
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    if circuit_breaker:
                        return asyncio.run(circuit_breaker.call(func, *args, **kwargs))
                    else:
                        return func(*args, **kwargs)
                        
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error("retry_exhausted", 
                                   function=func.__name__, 
                                   attempts=max_attempts, 
                                   error=str(e))
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    if jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning("retry_attempt", 
                                 function=func.__name__, 
                                 attempt=attempt + 1, 
                                 delay=delay, 
                                 error=str(e))
                    
                    time.sleep(delay)
            
            raise RetryError(f"Failed after {max_attempts} attempts: {last_exception}")
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator