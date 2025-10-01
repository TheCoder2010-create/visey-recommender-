"""Performance benchmarking utilities."""

import time
import asyncio
import statistics
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    median_time: float
    std_dev: float
    throughput: float  # operations per second
    success_rate: float
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_seconds": self.total_time,
            "avg_time_seconds": self.avg_time,
            "min_time_seconds": self.min_time,
            "max_time_seconds": self.max_time,
            "median_time_seconds": self.median_time,
            "std_dev_seconds": self.std_dev,
            "throughput_ops_per_second": self.throughput,
            "success_rate_percent": self.success_rate * 100,
            "error_count": len(self.errors)
        }


class Benchmark:
    """Benchmark runner for performance testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.results: List[BenchmarkResult] = []
    
    async def run_async_benchmark(
        self,
        func: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Run an async function benchmark."""
        logger.info("benchmark_started", name=self.name, iterations=iterations)
        
        # Warmup runs
        for _ in range(warmup_iterations):
            try:
                await func(*args, **kwargs)
            except Exception:
                pass  # Ignore warmup errors
        
        # Actual benchmark runs
        times = []
        errors = []
        successful_runs = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            run_start = time.time()
            try:
                await func(*args, **kwargs)
                run_time = time.time() - run_start
                times.append(run_time)
                successful_runs += 1
            except Exception as e:
                run_time = time.time() - run_start
                times.append(run_time)  # Include failed runs in timing
                errors.append(f"Iteration {i}: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        else:
            avg_time = min_time = max_time = median_time = std_dev = 0.0
        
        throughput = successful_runs / total_time if total_time > 0 else 0.0
        success_rate = successful_runs / iterations if iterations > 0 else 0.0
        
        result = BenchmarkResult(
            name=self.name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            success_rate=success_rate,
            errors=errors
        )
        
        self.results.append(result)
        logger.info("benchmark_completed", **result.to_dict())
        
        return result
    
    def run_sync_benchmark(
        self,
        func: Callable,
        iterations: int = 100,
        warmup_iterations: int = 10,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Run a synchronous function benchmark."""
        logger.info("benchmark_started", name=self.name, iterations=iterations)
        
        # Warmup runs
        for _ in range(warmup_iterations):
            try:
                func(*args, **kwargs)
            except Exception:
                pass  # Ignore warmup errors
        
        # Actual benchmark runs
        times = []
        errors = []
        successful_runs = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            run_start = time.time()
            try:
                func(*args, **kwargs)
                run_time = time.time() - run_start
                times.append(run_time)
                successful_runs += 1
            except Exception as e:
                run_time = time.time() - run_start
                times.append(run_time)  # Include failed runs in timing
                errors.append(f"Iteration {i}: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        else:
            avg_time = min_time = max_time = median_time = std_dev = 0.0
        
        throughput = successful_runs / total_time if total_time > 0 else 0.0
        success_rate = successful_runs / iterations if iterations > 0 else 0.0
        
        result = BenchmarkResult(
            name=self.name,
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            success_rate=success_rate,
            errors=errors
        )
        
        self.results.append(result)
        logger.info("benchmark_completed", **result.to_dict())
        
        return result
    
    async def run_concurrent_benchmark(
        self,
        func: Callable,
        iterations: int = 100,
        concurrency: int = 10,
        *args,
        **kwargs
    ) -> BenchmarkResult:
        """Run concurrent async function benchmark."""
        logger.info("concurrent_benchmark_started", 
                   name=self.name, 
                   iterations=iterations, 
                   concurrency=concurrency)
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def run_with_semaphore():
            async with semaphore:
                return await func(*args, **kwargs)
        
        times = []
        errors = []
        successful_runs = 0
        
        start_time = time.time()
        
        # Create tasks
        tasks = []
        for i in range(iterations):
            task = asyncio.create_task(run_with_semaphore())
            tasks.append((i, task))
        
        # Wait for all tasks to complete
        for i, task in tasks:
            run_start = time.time()
            try:
                await task
                run_time = time.time() - run_start
                times.append(run_time)
                successful_runs += 1
            except Exception as e:
                run_time = time.time() - run_start
                times.append(run_time)
                errors.append(f"Task {i}: {str(e)}")
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0.0
        else:
            avg_time = min_time = max_time = median_time = std_dev = 0.0
        
        throughput = successful_runs / total_time if total_time > 0 else 0.0
        success_rate = successful_runs / iterations if iterations > 0 else 0.0
        
        result = BenchmarkResult(
            name=f"{self.name}_concurrent",
            iterations=iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            median_time=median_time,
            std_dev=std_dev,
            throughput=throughput,
            success_rate=success_rate,
            errors=errors
        )
        
        self.results.append(result)
        logger.info("concurrent_benchmark_completed", **result.to_dict())
        
        return result


class RecommenderBenchmark:
    """Specialized benchmark for recommender system components."""
    
    def __init__(self):
        self.benchmarks: Dict[str, Benchmark] = {}
    
    def get_benchmark(self, name: str) -> Benchmark:
        """Get or create a benchmark instance."""
        if name not in self.benchmarks:
            self.benchmarks[name] = Benchmark(name)
        return self.benchmarks[name]
    
    async def benchmark_recommendation_generation(
        self,
        recommender,
        profile,
        resources,
        iterations: int = 50
    ) -> BenchmarkResult:
        """Benchmark recommendation generation."""
        benchmark = self.get_benchmark("recommendation_generation")
        
        async def recommend_wrapper():
            return recommender.recommend(profile, resources, top_n=10)
        
        return await benchmark.run_async_benchmark(
            recommend_wrapper,
            iterations=iterations
        )
    
    async def benchmark_data_loading(
        self,
        wp_client,
        user_id: int,
        iterations: int = 20
    ) -> BenchmarkResult:
        """Benchmark WordPress data loading."""
        benchmark = self.get_benchmark("data_loading")
        
        async def load_data_wrapper():
            profile_data = await wp_client.fetch_user_profile(user_id)
            resources_data = await wp_client.fetch_resources(per_page=100, page=1)
            return profile_data, resources_data
        
        return await benchmark.run_async_benchmark(
            load_data_wrapper,
            iterations=iterations
        )
    
    async def benchmark_cache_operations(
        self,
        cache,
        iterations: int = 100
    ) -> BenchmarkResult:
        """Benchmark cache operations."""
        benchmark = self.get_benchmark("cache_operations")
        
        async def cache_wrapper():
            # Test set and get operations
            await cache.set("benchmark_key", {"test": "data"}, ttl=60)
            result = await cache.get("benchmark_key")
            await cache.delete("benchmark_key")
            return result
        
        return await benchmark.run_async_benchmark(
            cache_wrapper,
            iterations=iterations
        )
    
    def benchmark_feature_engineering(
        self,
        profile,
        resources,
        iterations: int = 100
    ) -> BenchmarkResult:
        """Benchmark feature engineering."""
        from ..features.engineer import build_user_vector, build_resource_vector, cosine_similarity
        
        benchmark = self.get_benchmark("feature_engineering")
        
        def feature_wrapper():
            user_vector = build_user_vector(profile, [])
            for resource in resources[:10]:  # Limit to first 10 resources
                resource_vector = build_resource_vector(resource)
                similarity = cosine_similarity(user_vector, resource_vector)
            return similarity
        
        return benchmark.run_sync_benchmark(
            feature_wrapper,
            iterations=iterations
        )
    
    def get_all_results(self) -> Dict[str, List[BenchmarkResult]]:
        """Get all benchmark results."""
        return {name: bench.results for name, bench in self.benchmarks.items()}
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive benchmark report."""
        report = {
            "timestamp": time.time(),
            "benchmarks": {},
            "summary": {
                "total_benchmarks": len(self.benchmarks),
                "total_runs": 0,
                "avg_throughput": 0.0,
                "avg_success_rate": 0.0
            }
        }
        
        total_runs = 0
        total_throughput = 0.0
        total_success_rate = 0.0
        
        for name, benchmark in self.benchmarks.items():
            if benchmark.results:
                latest_result = benchmark.results[-1]
                report["benchmarks"][name] = latest_result.to_dict()
                
                total_runs += latest_result.iterations
                total_throughput += latest_result.throughput
                total_success_rate += latest_result.success_rate
        
        if self.benchmarks:
            report["summary"]["total_runs"] = total_runs
            report["summary"]["avg_throughput"] = total_throughput / len(self.benchmarks)
            report["summary"]["avg_success_rate"] = total_success_rate / len(self.benchmarks)
        
        return report


# Global benchmark instance
recommender_benchmark = RecommenderBenchmark()