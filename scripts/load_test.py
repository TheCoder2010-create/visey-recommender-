#!/usr/bin/env python3
"""Load testing script for the recommendation API."""

import asyncio
import aiohttp
import time
import json
import statistics
import argparse
from typing import List, Dict, Any
from datetime import datetime


class LoadTester:
    """Load testing utility for the recommendation API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
    
    async def single_request(self, session: aiohttp.ClientSession, endpoint: str, 
                           method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make a single request and measure performance."""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    response_data = await response.text()
                    status_code = response.status
            else:
                async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    response_data = await response.text()
                    status_code = response.status
            
            response_time = time.time() - start_time
            
            return {
                "success": True,
                "status_code": status_code,
                "response_time": response_time,
                "response_size": len(response_data),
                "error": None
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "success": False,
                "status_code": None,
                "response_time": response_time,
                "response_size": 0,
                "error": str(e)
            }
    
    async def health_check_test(self, concurrent_users: int = 10, 
                               requests_per_user: int = 10) -> Dict[str, Any]:
        """Test health check endpoint."""
        print(f"🏥 Testing health check endpoint ({concurrent_users} users, {requests_per_user} requests each)")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.single_request(session, "/health")
                    tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            return self._analyze_results(results, total_time, "health_check")
    
    async def recommendation_test(self, concurrent_users: int = 5, 
                                 requests_per_user: int = 5) -> Dict[str, Any]:
        """Test recommendation endpoint."""
        print(f"🎯 Testing recommendation endpoint ({concurrent_users} users, {requests_per_user} requests each)")
        
        # Sample request data
        request_data = {
            "user_profile": {
                "industry": "Technology",
                "stage": "Growth",
                "team_size": "10-50",
                "funding": "Series A",
                "location": "San Francisco"
            },
            "limit": 10
        }
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.single_request(session, "/recommendations", "POST", request_data)
                    tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            return self._analyze_results(results, total_time, "recommendations")
    
    async def metrics_test(self, concurrent_users: int = 10, 
                          requests_per_user: int = 10) -> Dict[str, Any]:
        """Test metrics endpoint."""
        print(f"📊 Testing metrics endpoint ({concurrent_users} users, {requests_per_user} requests each)")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.single_request(session, "/metrics")
                    tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            return self._analyze_results(results, total_time, "metrics")
    
    async def stress_test(self, max_users: int = 50, ramp_up_time: int = 30) -> Dict[str, Any]:
        """Gradually increase load to find breaking point."""
        print(f"💪 Running stress test (max {max_users} users, {ramp_up_time}s ramp-up)")
        
        results_by_load = {}
        
        for users in range(1, max_users + 1, 5):  # Increase by 5 users each step
            print(f"  Testing with {users} concurrent users...")
            
            result = await self.health_check_test(concurrent_users=users, requests_per_user=5)
            results_by_load[users] = result
            
            # Stop if error rate is too high or response time is too slow
            if result["error_rate"] > 0.1 or result["avg_response_time"] > 5.0:
                print(f"  Breaking point reached at {users} users")
                break
            
            # Small delay between load levels
            await asyncio.sleep(2)
        
        return {
            "test_type": "stress_test",
            "max_users_tested": max(results_by_load.keys()),
            "results_by_load": results_by_load,
            "breaking_point": self._find_breaking_point(results_by_load)
        }
    
    def _analyze_results(self, results: List[Dict], total_time: float, test_name: str) -> Dict[str, Any]:
        """Analyze test results."""
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            response_sizes = [r["response_size"] for r in successful_requests]
            
            analysis = {
                "test_name": test_name,
                "timestamp": datetime.now().isoformat(),
                "total_requests": len(results),
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": len(successful_requests) / len(results),
                "error_rate": len(failed_requests) / len(results),
                "total_time": total_time,
                "requests_per_second": len(results) / total_time,
                "avg_response_time": statistics.mean(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "median_response_time": statistics.median(response_times),
                "p95_response_time": self._percentile(response_times, 95),
                "p99_response_time": self._percentile(response_times, 99),
                "avg_response_size": statistics.mean(response_sizes) if response_sizes else 0,
                "total_data_transferred": sum(response_sizes),
                "errors": [r["error"] for r in failed_requests if r["error"]]
            }
        else:
            analysis = {
                "test_name": test_name,
                "timestamp": datetime.now().isoformat(),
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed_requests),
                "success_rate": 0,
                "error_rate": 1,
                "total_time": total_time,
                "requests_per_second": 0,
                "errors": [r["error"] for r in failed_requests if r["error"]]
            }
        
        self.results.append(analysis)
        return analysis
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile value."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _find_breaking_point(self, results_by_load: Dict[int, Dict]) -> Dict[str, Any]:
        """Find the breaking point from stress test results."""
        for users, result in results_by_load.items():
            if result["error_rate"] > 0.05 or result["avg_response_time"] > 2.0:
                return {
                    "users": users,
                    "error_rate": result["error_rate"],
                    "avg_response_time": result["avg_response_time"]
                }
        
        return {"users": max(results_by_load.keys()), "status": "no_breaking_point_found"}
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*80)
        print("📈 LOAD TEST SUMMARY")
        print("="*80)
        
        for result in self.results:
            print(f"\n{result['test_name'].upper()}:")
            print(f"  Total requests: {result['total_requests']}")
            print(f"  Success rate: {result['success_rate'] * 100:.1f}%")
            print(f"  Requests/second: {result['requests_per_second']:.2f}")
            
            if 'avg_response_time' in result:
                print(f"  Avg response time: {result['avg_response_time']:.3f}s")
                print(f"  95th percentile: {result['p95_response_time']:.3f}s")
                print(f"  99th percentile: {result['p99_response_time']:.3f}s")
            
            if result['failed_requests'] > 0:
                print(f"  ❌ Failed requests: {result['failed_requests']}")
                if result.get('errors'):
                    unique_errors = list(set(result['errors']))
                    for error in unique_errors[:3]:  # Show first 3 unique errors
                        print(f"    - {error}")
        
        print("\n" + "="*80)
    
    def save_results(self, filename: str):
        """Save results to JSON file."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"💾 Results saved to {filename}")


async def main():
    parser = argparse.ArgumentParser(description="Load testing for recommendation API")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="Base URL of the API")
    parser.add_argument("--health", action="store_true",
                       help="Test health check endpoint")
    parser.add_argument("--recommendations", action="store_true",
                       help="Test recommendations endpoint")
    parser.add_argument("--metrics", action="store_true",
                       help="Test metrics endpoint")
    parser.add_argument("--stress", action="store_true",
                       help="Run stress test")
    parser.add_argument("--all", action="store_true",
                       help="Run all tests")
    parser.add_argument("--users", type=int, default=10,
                       help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=10,
                       help="Requests per user")
    parser.add_argument("--output", type=str,
                       help="Save results to file")
    
    args = parser.parse_args()
    
    if not any([args.health, args.recommendations, args.metrics, args.stress, args.all]):
        args.all = True
    
    tester = LoadTester(base_url=args.url)
    
    try:
        print(f"🚀 Starting load tests against {args.url}")
        
        if args.health or args.all:
            await tester.health_check_test(args.users, args.requests)
        
        if args.recommendations or args.all:
            await tester.recommendation_test(args.users, args.requests)
        
        if args.metrics or args.all:
            await tester.metrics_test(args.users, args.requests)
        
        if args.stress or args.all:
            await tester.stress_test(max_users=50)
        
        tester.print_summary()
        
        if args.output:
            tester.save_results(args.output)
        
        print("\n✅ Load testing completed!")
        
    except Exception as e:
        print(f"❌ Load testing failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())