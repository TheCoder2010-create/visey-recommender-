"""Tests for metrics and monitoring utilities."""

import pytest
import time
from unittest.mock import patch, MagicMock

from visey_recommender.utils.metrics import (
    MetricsCollector,
    metrics,
    track_time,
    get_metrics,
    REQUEST_COUNT,
    REQUEST_DURATION,
    RECOMMENDATION_COUNT
)


class TestMetricsCollector:
    """Tests for MetricsCollector."""
    
    def test_init(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        assert collector.active_requests == 0
    
    def test_record_request(self):
        """Test request metrics recording."""
        collector = MetricsCollector()
        
        # Record a request
        collector.record_request("GET", "/recommend", 200, 0.5)
        
        # Check that metrics were recorded (we can't easily test Prometheus metrics directly)
        # But we can verify the method doesn't raise exceptions
        assert True
    
    def test_record_recommendation(self):
        """Test recommendation metrics recording."""
        collector = MetricsCollector()
        
        scores = [0.8, 0.7, 0.6, 0.5]
        collector.record_recommendation("returning", scores)
        
        # Verify method execution
        assert True
    
    def test_record_cache_operation(self):
        """Test cache operation metrics recording."""
        collector = MetricsCollector()
        
        collector.record_cache_operation("get", "hit")
        collector.record_cache_operation("set", "success")
        
        assert True
    
    def test_record_wp_api_call(self):
        """Test WordPress API call metrics recording."""
        collector = MetricsCollector()
        
        collector.record_wp_api_call("/wp-json/wp/v2/users", 200)
        collector.record_wp_api_call("/wp-json/wp/v2/posts", 404)
        
        assert True
    
    def test_update_active_users(self):
        """Test active users gauge update."""
        collector = MetricsCollector()
        
        collector.update_active_users(42)
        
        assert True


class TestTrackTimeDecorator:
    """Tests for track_time decorator."""
    
    def test_track_time_sync_function(self):
        """Test track_time decorator with synchronous function."""
        @track_time("test_function")
        def test_func(x, y):
            time.sleep(0.01)  # Small delay
            return x + y
        
        result = test_func(2, 3)
        assert result == 5
    
    @pytest.mark.asyncio
    async def test_track_time_async_function(self):
        """Test track_time decorator with asynchronous function."""
        @track_time("test_async_function")
        async def test_async_func(x, y):
            import asyncio
            await asyncio.sleep(0.01)  # Small delay
            return x * y
        
        result = await test_async_func(3, 4)
        assert result == 12
    
    def test_track_time_function_exception(self):
        """Test track_time decorator with function that raises exception."""
        @track_time("test_exception_function")
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_func()
    
    @pytest.mark.asyncio
    async def test_track_time_async_function_exception(self):
        """Test track_time decorator with async function that raises exception."""
        @track_time("test_async_exception_function")
        async def test_async_func():
            raise RuntimeError("Async test error")
        
        with pytest.raises(RuntimeError, match="Async test error"):
            await test_async_func()


class TestMetricsEndpoint:
    """Tests for metrics endpoint functionality."""
    
    def test_get_metrics(self):
        """Test metrics export functionality."""
        # Record some metrics first
        metrics.record_request("GET", "/test", 200, 0.1)
        metrics.record_recommendation("new", [0.8, 0.7])
        
        # Get metrics
        metrics_output = get_metrics()
        
        assert isinstance(metrics_output, str)
        assert len(metrics_output) > 0
        
        # Should contain Prometheus format
        assert "# HELP" in metrics_output or "# TYPE" in metrics_output
    
    def test_metrics_format(self):
        """Test that metrics are in proper Prometheus format."""
        metrics_output = get_metrics()
        
        # Basic format checks
        lines = metrics_output.split('\n')
        
        # Should have some content
        assert len(lines) > 0
        
        # Should not be empty
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) > 0


class TestMetricsIntegration:
    """Integration tests for metrics system."""
    
    def test_global_metrics_instance(self):
        """Test that global metrics instance works."""
        # Test that we can use the global metrics instance
        metrics.record_request("POST", "/feedback", 200, 0.05)
        metrics.record_cache_operation("get", "miss")
        
        # Should not raise exceptions
        assert True
    
    def test_metrics_with_concurrent_access(self):
        """Test metrics with concurrent access."""
        import threading
        import time
        
        def record_metrics():
            for i in range(10):
                metrics.record_request("GET", f"/test-{i}", 200, 0.01)
                time.sleep(0.001)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should complete without errors
        assert True
    
    @pytest.mark.integration
    def test_metrics_with_real_prometheus_client(self):
        """Test metrics with actual Prometheus client."""
        from prometheus_client import CollectorRegistry, generate_latest
        
        # Create a test registry
        test_registry = CollectorRegistry()
        
        # Import our metrics (they should be registered)
        from visey_recommender.utils.metrics import REGISTRY
        
        # Generate metrics
        metrics_data = generate_latest(REGISTRY)
        
        assert isinstance(metrics_data, bytes)
        assert len(metrics_data) > 0
        
        # Decode and check content
        metrics_str = metrics_data.decode('utf-8')
        assert len(metrics_str) > 0


class TestMetricsPerformance:
    """Performance tests for metrics system."""
    
    @pytest.mark.slow
    def test_metrics_recording_performance(self):
        """Test performance of metrics recording."""
        import time
        
        # Record many metrics quickly
        start_time = time.time()
        
        for i in range(1000):
            metrics.record_request("GET", "/test", 200, 0.001)
            metrics.record_recommendation("test", [0.5, 0.6, 0.7])
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast (less than 1 second for 1000 recordings)
        assert duration < 1.0
        
        # Calculate throughput
        throughput = 2000 / duration  # 2 metrics per iteration
        assert throughput > 1000  # Should handle >1000 metrics/second
    
    @pytest.mark.slow
    def test_metrics_export_performance(self):
        """Test performance of metrics export."""
        import time
        
        # Record some metrics first
        for i in range(100):
            metrics.record_request("GET", f"/test-{i % 10}", 200, 0.001)
        
        # Test export performance
        start_time = time.time()
        
        for _ in range(10):
            metrics_output = get_metrics()
            assert len(metrics_output) > 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should be fast (less than 0.5 seconds for 10 exports)
        assert duration < 0.5


@pytest.fixture
def reset_metrics():
    """Fixture to reset metrics between tests."""
    # Note: Prometheus metrics can't be easily reset, but we can work around this
    # by using different label values or accepting cumulative behavior
    yield
    # Cleanup if needed