"""Health check utilities for monitoring service status."""

import asyncio
import time
from typing import Dict, List, Optional, Any
from enum import Enum
import structlog
import httpx
from ..config import settings

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck:
    """Base class for health checks."""
    
    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout
        self.last_check_time = None
        self.last_status = None
        self.last_error = None
    
    async def check(self) -> tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        """Perform the health check.
        
        Returns:
            Tuple of (status, error_message, metadata)
        """
        raise NotImplementedError
    
    async def run_check(self) -> Dict[str, Any]:
        """Run the health check with timeout and error handling."""
        start_time = time.time()
        
        try:
            status, error, metadata = await asyncio.wait_for(
                self.check(), timeout=self.timeout
            )
            
            duration = time.time() - start_time
            self.last_check_time = time.time()
            self.last_status = status
            self.last_error = error
            
            result = {
                "name": self.name,
                "status": status.value,
                "duration_ms": round(duration * 1000, 2),
                "timestamp": self.last_check_time,
                **metadata
            }
            
            if error:
                result["error"] = error
            
            logger.info("health_check_completed", **result)
            return result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.last_check_time = time.time()
            self.last_status = HealthStatus.UNHEALTHY
            self.last_error = f"Health check timed out after {self.timeout}s"
            
            result = {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY.value,
                "duration_ms": round(duration * 1000, 2),
                "timestamp": self.last_check_time,
                "error": self.last_error
            }
            
            logger.error("health_check_timeout", **result)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.last_check_time = time.time()
            self.last_status = HealthStatus.UNHEALTHY
            self.last_error = str(e)
            
            result = {
                "name": self.name,
                "status": HealthStatus.UNHEALTHY.value,
                "duration_ms": round(duration * 1000, 2),
                "timestamp": self.last_check_time,
                "error": self.last_error
            }
            
            logger.error("health_check_failed", **result)
            return result


class WordPressHealthCheck(HealthCheck):
    """Health check for WordPress API connectivity."""
    
    def __init__(self):
        super().__init__("wordpress_api", timeout=10.0)
    
    async def check(self) -> tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        if not settings.WP_BASE_URL:
            return HealthStatus.UNHEALTHY, "WP_BASE_URL not configured", {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.WP_BASE_URL}/wp-json/wp/v2/")
                
                if response.status_code == 200:
                    data = response.json()
                    return HealthStatus.HEALTHY, None, {
                        "wp_version": data.get("description", "unknown"),
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                else:
                    return HealthStatus.UNHEALTHY, f"HTTP {response.status_code}", {
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}


class RedisHealthCheck(HealthCheck):
    """Health check for Redis connectivity."""
    
    def __init__(self):
        super().__init__("redis", timeout=5.0)
    
    async def check(self) -> tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        if not settings.REDIS_URL or settings.CACHE_BACKEND == "sqlite":
            return HealthStatus.HEALTHY, None, {"status": "not_configured"}
        
        try:
            import redis.asyncio as redis
            
            client = redis.from_url(settings.REDIS_URL)
            await client.ping()
            info = await client.info()
            await client.close()
            
            return HealthStatus.HEALTHY, None, {
                "redis_version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown")
            }
            
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}


class DatabaseHealthCheck(HealthCheck):
    """Health check for SQLite database."""
    
    def __init__(self):
        super().__init__("database", timeout=5.0)
    
    async def check(self) -> tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        try:
            import sqlite3
            import os
            
            # Check if feedback database exists and is accessible
            if os.path.exists(settings.SQLITE_FEEDBACK_PATH):
                conn = sqlite3.connect(settings.SQLITE_FEEDBACK_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
                
                return HealthStatus.HEALTHY, None, {
                    "database_path": settings.SQLITE_FEEDBACK_PATH,
                    "table_count": table_count
                }
            else:
                return HealthStatus.DEGRADED, "Database file not found", {
                    "database_path": settings.SQLITE_FEEDBACK_PATH
                }
                
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}


class MemoryHealthCheck(HealthCheck):
    """Health check for memory usage."""
    
    def __init__(self, warning_threshold_mb: int = 500, critical_threshold_mb: int = 1000):
        super().__init__("memory", timeout=2.0)
        self.warning_threshold = warning_threshold_mb * 1024 * 1024  # Convert to bytes
        self.critical_threshold = critical_threshold_mb * 1024 * 1024
    
    async def check(self) -> tuple[HealthStatus, Optional[str], Dict[str, Any]]:
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            metadata = {
                "memory_rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "memory_vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "memory_percent": round(memory_percent, 2)
            }
            
            if memory_info.rss > self.critical_threshold:
                return HealthStatus.UNHEALTHY, f"Memory usage critical: {metadata['memory_rss_mb']}MB", metadata
            elif memory_info.rss > self.warning_threshold:
                return HealthStatus.DEGRADED, f"Memory usage high: {metadata['memory_rss_mb']}MB", metadata
            else:
                return HealthStatus.HEALTHY, None, metadata
                
        except ImportError:
            return HealthStatus.HEALTHY, None, {"status": "psutil_not_available"}
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e), {}


class HealthChecker:
    """Centralized health checking service."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = [
            WordPressHealthCheck(),
            RedisHealthCheck(),
            DatabaseHealthCheck(),
            MemoryHealthCheck()
        ]
        self.last_overall_status = HealthStatus.HEALTHY
        self.startup_time = time.time()
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return aggregated results."""
        start_time = time.time()
        
        # Run all checks concurrently
        tasks = [check.run_check() for check in self.checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        check_results = []
        healthy_count = 0
        unhealthy_count = 0
        degraded_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                check_result = {
                    "name": self.checks[i].name,
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": str(result),
                    "timestamp": time.time()
                }
                unhealthy_count += 1
            else:
                check_result = result
                status = HealthStatus(result["status"])
                if status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif status == HealthStatus.DEGRADED:
                    degraded_count += 1
                else:
                    unhealthy_count += 1
            
            check_results.append(check_result)
        
        # Determine overall status
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        self.last_overall_status = overall_status
        
        duration = time.time() - start_time
        uptime = time.time() - self.startup_time
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "duration_ms": round(duration * 1000, 2),
            "uptime_seconds": round(uptime, 2),
            "checks": {
                "total": len(check_results),
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count
            },
            "details": check_results
        }
    
    async def get_readiness(self) -> Dict[str, Any]:
        """Check if service is ready to handle requests."""
        # For readiness, we only care about critical dependencies
        critical_checks = ["wordpress_api", "database"]
        
        results = await self.run_all_checks()
        critical_results = [
            check for check in results["details"] 
            if check["name"] in critical_checks
        ]
        
        is_ready = all(
            check["status"] in [HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value]
            for check in critical_results
        )
        
        return {
            "ready": is_ready,
            "timestamp": time.time(),
            "critical_checks": critical_results
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """Check if service is alive (basic functionality)."""
        return {
            "alive": True,
            "timestamp": time.time(),
            "uptime_seconds": round(time.time() - self.startup_time, 2)
        }


# Global health checker instance
health_checker = HealthChecker()