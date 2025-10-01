#!/usr/bin/env python3
"""
Local System Test Script for Visey Recommender
Tests all components and endpoints to verify the system is working correctly.
"""

import asyncio
import json
import time
import sys
import os
from pathlib import Path
import httpx
import subprocess
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

class LocalSystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_results = []
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def record_test(self, test_name: str, success: bool, details: str = ""):
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
        
        if success:
            print_success(f"{test_name}: {details}")
        else:
            print_error(f"{test_name}: {details}")

    async def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print_header("BASIC CONNECTIVITY TESTS")
        
        try:
            response = await self.client.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.record_test("Basic API Connection", True, f"Status: {response.status_code}")
            else:
                self.record_test("Basic API Connection", False, f"Status: {response.status_code}")
        except Exception as e:
            self.record_test("Basic API Connection", False, f"Error: {str(e)}")

    async def test_health_endpoints(self):
        """Test all health check endpoints"""
        print_header("HEALTH CHECK TESTS")
        
        health_endpoints = [
            ("/health", "Main Health Check"),
            ("/health/ready", "Readiness Check"),
            ("/health/live", "Liveness Check")
        ]
        
        for endpoint, name in health_endpoints:
            try:
                response = await self.client.get(f"{self.base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown") if isinstance(data, dict) else "ok"
                    self.record_test(name, True, f"Status: {status}")
                else:
                    self.record_test(name, False, f"HTTP {response.status_code}")
            except Exception as e:
                self.record_test(name, False, f"Error: {str(e)}")

    async def test_wordpress_integration(self):
        """Test WordPress API integration"""
        print_header("WORDPRESS INTEGRATION TESTS")
        
        # Test WordPress health
        try:
            response = await self.client.get(f"{self.base_url}/wordpress/health")
            if response.status_code == 200:
                data = response.json()
                wp_status = data.get("wordpress_api", {}).get("status", "unknown")
                self.record_test("WordPress Health", True, f"Status: {wp_status}")
            else:
                self.record_test("WordPress Health", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.record_test("WordPress Health", False, f"Error: {str(e)}")
        
        # Test scheduler status
        try:
            response = await self.client.get(f"{self.base_url}/wordpress/scheduler/status")
            if response.status_code == 200:
                data = response.json()
                scheduler_running = data.get("scheduler_running", False)
                self.record_test("WordPress Scheduler", scheduler_running, 
                               f"Running: {scheduler_running}")
            else:
                self.record_test("WordPress Scheduler", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.record_test("WordPress Scheduler", False, f"Error: {str(e)}")

    async def test_recommendation_system(self):
        """Test the recommendation system"""
        print_header("RECOMMENDATION SYSTEM TESTS")
        
        # Test with a sample user ID
        test_user_id = 1
        
        try:
            response = await self.client.get(f"{self.base_url}/recommend?user_id={test_user_id}")
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                self.record_test("Recommendation Generation", True, 
                               f"Generated {len(items)} recommendations")
            elif response.status_code == 404:
                self.record_test("Recommendation Generation", False, 
                               "User not found - need WordPress data")
            else:
                self.record_test("Recommendation Generation", False, 
                               f"HTTP {response.status_code}")
        except Exception as e:
            self.record_test("Recommendation Generation", False, f"Error: {str(e)}")

    async def test_feedback_system(self):
        """Test the feedback system"""
        print_header("FEEDBACK SYSTEM TESTS")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/feedback?user_id=1&resource_id=1&rating=5"
            )
            if response.status_code == 200:
                data = response.json()
                success = data.get("ok", False)
                self.record_test("Feedback Submission", success, "Feedback recorded")
            else:
                self.record_test("Feedback Submission", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.record_test("Feedback Submission", False, f"Error: {str(e)}")

    async def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        print_header("METRICS TESTS")
        
        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                metrics_data = response.text
                metric_count = len([line for line in metrics_data.split('\n') 
                                  if line and not line.startswith('#')])
                self.record_test("Metrics Export", True, f"{metric_count} metrics exported")
            else:
                self.record_test("Metrics Export", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.record_test("Metrics Export", False, f"Error: {str(e)}")

    async def test_status_endpoint(self):
        """Test status endpoint"""
        print_header("STATUS TESTS")
        
        try:
            response = await self.client.get(f"{self.base_url}/status")
            if response.status_code == 200:
                data = response.json()
                service_status = data.get("status", "unknown")
                version = data.get("version", "unknown")
                self.record_test("Service Status", True, 
                               f"Status: {service_status}, Version: {version}")
            else:
                self.record_test("Service Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.record_test("Service Status", False, f"Error: {str(e)}")

    async def test_performance(self):
        """Test basic performance"""
        print_header("PERFORMANCE TESTS")
        
        # Test response times
        endpoints = [
            "/health/live",
            "/status",
            "/metrics"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = await self.client.get(f"{self.base_url}{endpoint}")
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # Convert to ms
                
                if response.status_code == 200 and response_time < 1000:  # Less than 1 second
                    self.record_test(f"Performance {endpoint}", True, 
                                   f"{response_time:.2f}ms")
                else:
                    self.record_test(f"Performance {endpoint}", False, 
                                   f"{response_time:.2f}ms (too slow or error)")
            except Exception as e:
                self.record_test(f"Performance {endpoint}", False, f"Error: {str(e)}")

    def check_environment(self):
        """Check environment setup"""
        print_header("ENVIRONMENT CHECK")
        
        # Check Python version
        python_version = sys.version.split()[0]
        print_info(f"Python Version: {python_version}")
        
        # Check if server is running
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and any('uvicorn' in str(cmd) for cmd in proc.info['cmdline']):
                    print_success(f"Found running server: PID {proc.info['pid']}")
                    return True
        except ImportError:
            print_warning("psutil not available, cannot check running processes")
        
        print_warning("No running server detected")
        return False

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n{Colors.BOLD}Total Tests: {total_tests}{Colors.END}")
        print(f"{Colors.GREEN}Passed: {passed_tests}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed_tests}{Colors.END}")
        
        if failed_tests > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.END}")
        
        if success_rate >= 80:
            print(f"\n{Colors.GREEN}🎉 System is working well!{Colors.END}")
        elif success_rate >= 60:
            print(f"\n{Colors.YELLOW}⚠️  System has some issues but is functional{Colors.END}")
        else:
            print(f"\n{Colors.RED}❌ System has significant issues{Colors.END}")

async def main():
    """Main test function"""
    print_header("VISEY RECOMMENDER LOCAL SYSTEM TEST")
    print_info("Testing all system components...")
    
    async with LocalSystemTester() as tester:
        # Check environment first
        server_running = tester.check_environment()
        
        if not server_running:
            print_warning("Server may not be running. Start it with:")
            print_info("uvicorn visey_recommender.api.main:app --reload --host 0.0.0.0 --port 8000")
            print_info("Or run: python -m visey_recommender.api.main")
        
        # Run all tests
        await tester.test_basic_connectivity()
        await tester.test_health_endpoints()
        await tester.test_wordpress_integration()
        await tester.test_recommendation_system()
        await tester.test_feedback_system()
        await tester.test_metrics_endpoint()
        await tester.test_status_endpoint()
        await tester.test_performance()
        
        # Print summary
        tester.print_summary()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {str(e)}{Colors.END}")
        sys.exit(1)