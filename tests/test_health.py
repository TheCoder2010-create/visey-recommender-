"""Tests for health check utilities."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import time

from visey_recommender.utils.health import (
    HealthStatus,
    HealthCheck,
    WordPressHealthCheck,
    RedisHealthCheck,
    DatabaseHealthCheck,
    MemoryHealthCheck,
    HealthChecker
)


class TestHealthCheck:
    """Tests for base HealthCheck class."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check."""
        class TestHealthCheck(HealthCheck):
            async def check(self):
                return HealthStatus.HEALTHY, None, {"test": "data"}
        
        health_check = TestHealthCheck("test")
        result = await health_check.run_check()
        
        assert result["name"] == "test"
        assert result["status"] == "healthy"
        assert "duration_ms" in result
        assert "timestamp" in result
        assert result["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check."""
        class TestHealthCheck(HealthCheck):
            async def check(self):
                raise Exception("Test error")
        
        health_check = TestHealthCheck("test")
        result = await health_check.run_check()
        
        assert result["status"] == "unhealthy"
        assert "Test error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check timeout."""
        class TestHealthCheck(HealthCheck):
            async def check(self):
                import asyncio
                await asyncio.sleep(10)  # Longer than timeout
                return HealthStatus.HEALTHY, None, {}
        
        health_check = TestHealthCheck("test", timeout=0.1)
        result = await health_check.run_check()
        
        assert result["status"] == "unhealthy"
        assert "timed out" in result["error"]


class TestWordPressHealthCheck:
    """Tests for WordPress health check."""
    
    @pytest.mark.asyncio
    async def test_wp_health_check_success(self):
        """Test successful WordPress health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"description": "WordPress 6.0"}
        mock_response.elapsed.total_seconds.return_value = 0.5
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with patch('visey_recommender.config.settings.WP_BASE_URL', 'https://example.com'):
                health_check = WordPressHealthCheck()
                status, error, metadata = await health_check.check()
                
                assert status == HealthStatus.HEALTHY
                assert error is None
                assert "wp_version" in metadata
    
    @pytest.mark.asyncio
    async def test_wp_health_check_no_url(self):
        """Test WordPress health check with no URL configured."""
        with patch('visey_recommender.config.settings.WP_BASE_URL', ''):
            health_check = WordPressHealthCheck()
            status, error, metadata = await health_check.check()
            
            assert status == HealthStatus.UNHEALTHY
            assert "not configured" in error
    
    @pytest.mark.asyncio
    async def test_wp_health_check_http_error(self):
        """Test WordPress health check with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            with patch('visey_recommender.config.settings.WP_BASE_URL', 'https://example.com'):
                health_check = WordPressHealthCheck()
                status, error, metadata = await health_check.check()
                
                assert status == HealthStatus.UNHEALTHY
                assert "HTTP 500" in error


class TestRedisHealthCheck:
    """Tests for Redis health check."""
    
    @pytest.mark.asyncio
    async def test_redis_health_check_success(self):
        """Test successful Redis health check."""
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.info.return_value = {
            "redis_version": "6.0.0",
            "connected_clients": 5,
            "used_memory_human": "1.5M"
        }
        
        with patch('redis.asyncio.from_url', return_value=mock_client):
            with patch('visey_recommender.config.settings.REDIS_URL', 'redis://localhost:6379'):
                with patch('visey_recommender.config.settings.CACHE_BACKEND', 'redis'):
                    health_check = RedisHealthCheck()
                    status, error, metadata = await health_check.check()
                    
                    assert status == HealthStatus.HEALTHY
                    assert error is None
                    assert metadata["redis_version"] == "6.0.0"
    
    @pytest.mark.asyncio
    async def test_redis_health_check_not_configured(self):
        """Test Redis health check when not configured."""
        with patch('visey_recommender.config.settings.REDIS_URL', None):
            health_check = RedisHealthCheck()
            status, error, metadata = await health_check.check()
            
            assert status == HealthStatus.HEALTHY
            assert metadata["status"] == "not_configured"


class TestDatabaseHealthCheck:
    """Tests for database health check."""
    
    @pytest.mark.asyncio
    async def test_database_health_check_success(self, temp_db):
        """Test successful database health check."""
        import sqlite3
        
        # Create a test database
        conn = sqlite3.connect(temp_db)
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.close()
        
        with patch('visey_recommender.config.settings.SQLITE_FEEDBACK_PATH', temp_db):
            health_check = DatabaseHealthCheck()
            status, error, metadata = await health_check.check()
            
            assert status == HealthStatus.HEALTHY
            assert error is None
            assert metadata["table_count"] >= 1
    
    @pytest.mark.asyncio
    async def test_database_health_check_missing_file(self):
        """Test database health check with missing file."""
        with patch('visey_recommender.config.settings.SQLITE_FEEDBACK_PATH', '/nonexistent/path.db'):
            health_check = DatabaseHealthCheck()
            status, error, metadata = await health_check.check()
            
            assert status == HealthStatus.DEGRADED
            assert "not found" in error


class TestMemoryHealthCheck:
    """Tests for memory health check."""
    
    @pytest.mark.asyncio
    async def test_memory_health_check_success(self):
        """Test successful memory health check."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=100*1024*1024, vms=200*1024*1024)  # 100MB RSS
        mock_process.memory_percent.return_value = 5.0
        
        with patch('psutil.Process', return_value=mock_process):
            health_check = MemoryHealthCheck(warning_threshold_mb=500, critical_threshold_mb=1000)
            status, error, metadata = await health_check.check()
            
            assert status == HealthStatus.HEALTHY
            assert error is None
            assert metadata["memory_rss_mb"] == 100.0
    
    @pytest.mark.asyncio
    async def test_memory_health_check_high_usage(self):
        """Test memory health check with high usage."""
        mock_process = MagicMock()
        mock_process.memory_info.return_value = MagicMock(rss=800*1024*1024, vms=1000*1024*1024)  # 800MB RSS
        mock_process.memory_percent.return_value = 80.0
        
        with patch('psutil.Process', return_value=mock_process):
            health_check = MemoryHealthCheck(warning_threshold_mb=500, critical_threshold_mb=1000)
            status, error, metadata = await health_check.check()
            
            assert status == HealthStatus.DEGRADED
            assert "high" in error


class TestHealthChecker:
    """Tests for HealthChecker."""
    
    @pytest.mark.asyncio
    async def test_health_checker_all_healthy(self):
        """Test health checker with all checks healthy."""
        health_checker = HealthChecker()
        
        # Mock all checks to return healthy
        for check in health_checker.checks:
            check.run_check = AsyncMock(return_value={
                "name": check.name,
                "status": "healthy",
                "timestamp": time.time(),
                "duration_ms": 10.0
            })
        
        result = await health_checker.run_all_checks()
        
        assert result["status"] == "healthy"
        assert result["checks"]["healthy"] == len(health_checker.checks)
        assert result["checks"]["unhealthy"] == 0
    
    @pytest.mark.asyncio
    async def test_health_checker_some_unhealthy(self):
        """Test health checker with some checks unhealthy."""
        health_checker = HealthChecker()
        
        # Mock first check as unhealthy, rest as healthy
        for i, check in enumerate(health_checker.checks):
            status = "unhealthy" if i == 0 else "healthy"
            check.run_check = AsyncMock(return_value={
                "name": check.name,
                "status": status,
                "timestamp": time.time(),
                "duration_ms": 10.0
            })
        
        result = await health_checker.run_all_checks()
        
        assert result["status"] == "unhealthy"
        assert result["checks"]["unhealthy"] == 1
        assert result["checks"]["healthy"] == len(health_checker.checks) - 1
    
    @pytest.mark.asyncio
    async def test_readiness_check(self):
        """Test readiness check."""
        health_checker = HealthChecker()
        
        # Mock critical checks
        for check in health_checker.checks:
            if check.name in ["wordpress_api", "database"]:
                status = "healthy"
            else:
                status = "degraded"
            
            check.run_check = AsyncMock(return_value={
                "name": check.name,
                "status": status,
                "timestamp": time.time(),
                "duration_ms": 10.0
            })
        
        # Mock run_all_checks to return the expected structure
        health_checker.run_all_checks = AsyncMock(return_value={
            "details": [
                {"name": "wordpress_api", "status": "healthy"},
                {"name": "database", "status": "healthy"},
                {"name": "redis", "status": "degraded"},
                {"name": "memory", "status": "degraded"}
            ]
        })
        
        result = await health_checker.get_readiness()
        
        assert result["ready"] is True
        assert len(result["critical_checks"]) == 2
    
    @pytest.mark.asyncio
    async def test_liveness_check(self):
        """Test liveness check."""
        health_checker = HealthChecker()
        result = await health_checker.get_liveness()
        
        assert result["alive"] is True
        assert "uptime_seconds" in result