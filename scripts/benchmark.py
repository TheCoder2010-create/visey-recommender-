#!/usr/bin/env python3
"""Script to run performance benchmarks."""

import asyncio
import sys
import argparse
import json
import time
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from visey_recommender.utils.benchmarks import recommender_benchmark
from visey_recommender.clients.wp_client import WPClient
from visey_recommender.data.models import UserProfile, Resource
from visey_recommender.recommender.baseline import BaselineRecommender
from visey_recommender.storage.cache import Cache


async def create_sample_data():
    """Create sample data for benchmarking."""
    profile = UserProfile(
        user_id=123,
        industry="Technology",
        stage="Growth",
        team_size="10-50",
        funding="Series A",
        location="San Francisco"
    )
    
    resources = [
        Resource(
            id=i,
            title=f"Resource {i}",
            link=f"https://example.com/resource-{i}",
            excerpt=f"This is resource {i} for testing",
            categories=["Business", "Technology"],
            tags=["test", "resource", f"tag-{i}"],
            meta={"difficulty": "intermediate"}
        )
        for i in range(1, 101)  # 100 resources
    ]
    
    return profile, resources


async def benchmark_recommendation_system():
    """Benchmark the recommendation system."""
    print("🚀 Starting recommendation system benchmarks...")
    
    # Create sample data
    profile, resources = await create_sample_data()
    
    # Initialize components
    recommender = BaselineRecommender()
    
    # Benchmark recommendation generation
    print("\n📊 Benchmarking recommendation generation...")
    result = await recommender_benchmark.benchmark_recommendation_generation(
        recommender, profile, resources, iterations=50
    )
    
    print(f"Average time: {result.avg_time:.4f}s")
    print(f"Throughput: {result.throughput:.2f} recommendations/second")
    print(f"Success rate: {result.success_rate * 100:.1f}%")
    
    # Benchmark feature engineering
    print("\n🔧 Benchmarking feature engineering...")
    result = recommender_benchmark.benchmark_feature_engineering(
        profile, resources, iterations=100
    )
    
    print(f"Average time: {result.avg_time:.4f}s")
    print(f"Throughput: {result.throughput:.2f} operations/second")
    
    return recommender_benchmark.get_all_results()


async def benchmark_cache_operations():
    """Benchmark cache operations."""
    print("\n💾 Benchmarking cache operations...")
    
    cache = Cache()
    result = await recommender_benchmark.benchmark_cache_operations(
        cache, iterations=100
    )
    
    print(f"Average time: {result.avg_time:.4f}s")
    print(f"Throughput: {result.throughput:.2f} operations/second")
    print(f"Success rate: {result.success_rate * 100:.1f}%")


async def benchmark_data_loading():
    """Benchmark data loading (mock)."""
    print("\n📥 Benchmarking data loading...")
    
    # Mock WP client for benchmarking
    class MockWPClient:
        async def fetch_user_profile(self, user_id):
            await asyncio.sleep(0.01)  # Simulate network delay
            return {
                "industry": "Technology",
                "stage": "Growth",
                "team_size": "10-50",
                "funding": "Series A",
                "location": "San Francisco"
            }
        
        async def fetch_resources(self, per_page=100, page=1):
            await asyncio.sleep(0.05)  # Simulate network delay
            return [
                {
                    "id": i,
                    "title": f"Resource {i}",
                    "link": f"https://example.com/resource-{i}",
                    "excerpt": f"Resource {i} excerpt",
                    "categories": ["Business"],
                    "tags": ["test"],
                    "meta": {}
                }
                for i in range(1, per_page + 1)
            ]
    
    wp_client = MockWPClient()
    result = await recommender_benchmark.benchmark_data_loading(
        wp_client, user_id=123, iterations=20
    )
    
    print(f"Average time: {result.avg_time:.4f}s")
    print(f"Throughput: {result.throughput:.2f} operations/second")
    print(f"Success rate: {result.success_rate * 100:.1f}%")


def generate_report(results: Dict[str, List], output_format: str = "console") -> Dict[str, Any]:
    """Generate a benchmark report."""
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "benchmarks": {},
        "summary": {}
    }
    
    total_benchmarks = 0
    total_operations = 0
    avg_throughput = 0
    
    for benchmark_name, benchmark_results in results.items():
        if benchmark_results:
            latest = benchmark_results[-1]
            total_benchmarks += 1
            total_operations += latest.iterations
            avg_throughput += latest.throughput
            
            report_data["benchmarks"][benchmark_name] = {
                "iterations": latest.iterations,
                "avg_time": latest.avg_time,
                "min_time": latest.min_time,
                "max_time": latest.max_time,
                "throughput": latest.throughput,
                "success_rate": latest.success_rate,
                "errors": len(latest.errors) if hasattr(latest, 'errors') and latest.errors else 0
            }
    
    report_data["summary"] = {
        "total_benchmarks": total_benchmarks,
        "total_operations": total_operations,
        "avg_throughput": avg_throughput / max(total_benchmarks, 1)
    }
    
    if output_format == "json":
        print(json.dumps(report_data, indent=2))
    else:
        print("\n" + "="*80)
        print("📈 BENCHMARK REPORT")
        print("="*80)
        
        for benchmark_name, data in report_data["benchmarks"].items():
            print(f"\n{benchmark_name.upper()}:")
            print(f"  Iterations: {data['iterations']}")
            print(f"  Average time: {data['avg_time']:.4f}s")
            print(f"  Min time: {data['min_time']:.4f}s")
            print(f"  Max time: {data['max_time']:.4f}s")
            print(f"  Throughput: {data['throughput']:.2f} ops/sec")
            print(f"  Success rate: {data['success_rate'] * 100:.1f}%")
            
            if data['errors'] > 0:
                print(f"  Errors: {data['errors']}")
        
        print(f"\nSUMMARY:")
        print(f"  Total benchmarks: {report_data['summary']['total_benchmarks']}")
        print(f"  Total operations: {report_data['summary']['total_operations']}")
        print(f"  Average throughput: {report_data['summary']['avg_throughput']:.2f} ops/sec")
        print("\n" + "="*80)
    
    return report_data


async def benchmark_memory_usage():
    """Benchmark memory usage during operations."""
    print("\n🧠 Benchmarking memory usage...")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create sample data and run operations
        profile, resources = await create_sample_data()
        recommender = BaselineRecommender()
        
        # Run multiple recommendation cycles
        for _ in range(10):
            await recommender.get_recommendations(profile, resources)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Initial memory: {initial_memory:.2f} MB")
        print(f"Final memory: {final_memory:.2f} MB")
        print(f"Memory increase: {memory_increase:.2f} MB")
        
        return {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase
        }
        
    except ImportError:
        print("psutil not available, skipping memory benchmark")
        return None


async def benchmark_concurrent_requests():
    """Benchmark concurrent request handling."""
    print("\n🔄 Benchmarking concurrent requests...")
    
    profile, resources = await create_sample_data()
    recommender = BaselineRecommender()
    
    async def single_request():
        start_time = time.time()
        try:
            await recommender.get_recommendations(profile, resources)
            return time.time() - start_time, True
        except Exception as e:
            return time.time() - start_time, False
    
    # Test different concurrency levels
    concurrency_levels = [1, 5, 10, 20]
    results = {}
    
    for concurrency in concurrency_levels:
        print(f"  Testing {concurrency} concurrent requests...")
        
        tasks = [single_request() for _ in range(concurrency)]
        start_time = time.time()
        task_results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        times = [result[0] for result in task_results]
        successes = [result[1] for result in task_results]
        
        results[f"concurrency_{concurrency}"] = {
            "total_time": total_time,
            "avg_response_time": statistics.mean(times),
            "min_response_time": min(times),
            "max_response_time": max(times),
            "success_rate": sum(successes) / len(successes),
            "throughput": len(tasks) / total_time
        }
        
        print(f"    Avg response time: {results[f'concurrency_{concurrency}']['avg_response_time']:.4f}s")
        print(f"    Throughput: {results[f'concurrency_{concurrency}']['throughput']:.2f} req/sec")
    
    return results


async def main():
    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument("--recommendations", action="store_true", 
                       help="Benchmark recommendation generation")
    parser.add_argument("--cache", action="store_true", 
                       help="Benchmark cache operations")
    parser.add_argument("--data-loading", action="store_true", 
                       help="Benchmark data loading")
    parser.add_argument("--memory", action="store_true",
                       help="Benchmark memory usage")
    parser.add_argument("--concurrent", action="store_true",
                       help="Benchmark concurrent requests")
    parser.add_argument("--all", action="store_true", 
                       help="Run all benchmarks")
    parser.add_argument("--iterations", type=int, default=50,
                       help="Number of iterations per benchmark")
    parser.add_argument("--output-format", choices=["console", "json"], default="console",
                       help="Output format for results")
    parser.add_argument("--save-results", type=str,
                       help="Save results to file")
    
    args = parser.parse_args()
    
    if not any([args.recommendations, args.cache, args.data_loading, 
                args.memory, args.concurrent, args.all]):
        args.all = True
    
    results = {}
    additional_results = {}
    
    try:
        print("🚀 Starting comprehensive performance benchmarks...")
        start_time = time.time()
        
        if args.recommendations or args.all:
            results.update(await benchmark_recommendation_system())
        
        if args.cache or args.all:
            await benchmark_cache_operations()
        
        if args.data_loading or args.all:
            await benchmark_data_loading()
        
        if args.memory or args.all:
            memory_results = await benchmark_memory_usage()
            if memory_results:
                additional_results["memory"] = memory_results
        
        if args.concurrent or args.all:
            concurrent_results = await benchmark_concurrent_requests()
            additional_results["concurrent"] = concurrent_results
        
        # Get final results
        all_results = recommender_benchmark.get_all_results()
        
        # Combine all results
        final_results = {**all_results, **additional_results}
        
        # Generate report
        report_data = generate_report(all_results, args.output_format)
        
        # Add additional results to report
        if additional_results:
            report_data["additional_benchmarks"] = additional_results
        
        # Save results if requested
        if args.save_results:
            with open(args.save_results, 'w') as f:
                json.dump(report_data, f, indent=2)
            print(f"\n💾 Results saved to {args.save_results}")
        
        total_time = time.time() - start_time
        print(f"\n✅ All benchmarks completed in {total_time:.2f}s!")
        
        # Performance thresholds (can be configured)
        if args.output_format == "console":
            print("\n🎯 Performance Analysis:")
            for benchmark_name, data in report_data.get("benchmarks", {}).items():
                if data["throughput"] < 10:
                    print(f"  ⚠️  {benchmark_name}: Low throughput ({data['throughput']:.2f} ops/sec)")
                elif data["throughput"] > 100:
                    print(f"  ✅ {benchmark_name}: Excellent throughput ({data['throughput']:.2f} ops/sec)")
                else:
                    print(f"  ✅ {benchmark_name}: Good throughput ({data['throughput']:.2f} ops/sec)")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())