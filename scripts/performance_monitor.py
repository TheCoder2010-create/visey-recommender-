#!/usr/bin/env python3
"""Continuous performance monitoring script."""

import asyncio
import time
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not available, some metrics will be unavailable")

from visey_recommender.utils.metrics import MetricsCollector


class PerformanceMonitor:
    """Continuous performance monitoring."""
    
    def __init__(self, interval: int = 60):
        self.interval = interval
        self.metrics_collector = MetricsCollector()
        self.running = False
        self.data_points = []
    
    async def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": None,
            "memory_percent": None,
            "memory_used_mb": None,
            "disk_usage_percent": None,
            "network_io": None
        }
        
        if HAS_PSUTIL:
            # CPU usage
            metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics["memory_percent"] = memory.percent
            metrics["memory_used_mb"] = memory.used / 1024 / 1024
            
            # Disk usage
            disk = psutil.disk_usage('/')
            metrics["disk_usage_percent"] = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics["network_io"] = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
        
        return metrics
    
    async def collect_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics."""
        # Get metrics from the metrics collector
        app_metrics = self.metrics_collector.get_all_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations_generated": app_metrics.get("recommendations_generated", 0),
            "cache_hits": app_metrics.get("cache_hits", 0),
            "cache_misses": app_metrics.get("cache_misses", 0),
            "api_requests": app_metrics.get("api_requests", 0),
            "errors": app_metrics.get("errors", 0),
            "avg_response_time": app_metrics.get("avg_response_time", 0),
            "active_users": app_metrics.get("active_users", 0)
        }
    
    async def analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends from collected data."""
        if len(self.data_points) < 2:
            return {"status": "insufficient_data"}
        
        recent_points = self.data_points[-10:]  # Last 10 data points
        
        # Calculate trends
        cpu_trend = self._calculate_trend([p["system"]["cpu_percent"] for p in recent_points if p["system"]["cpu_percent"]])
        memory_trend = self._calculate_trend([p["system"]["memory_percent"] for p in recent_points if p["system"]["memory_percent"]])
        response_time_trend = self._calculate_trend([p["application"]["avg_response_time"] for p in recent_points])
        
        # Detect anomalies
        anomalies = []
        latest = recent_points[-1]
        
        if latest["system"]["cpu_percent"] and latest["system"]["cpu_percent"] > 80:
            anomalies.append("high_cpu_usage")
        
        if latest["system"]["memory_percent"] and latest["system"]["memory_percent"] > 85:
            anomalies.append("high_memory_usage")
        
        if latest["application"]["avg_response_time"] > 2.0:
            anomalies.append("slow_response_time")
        
        error_rate = latest["application"]["errors"] / max(latest["application"]["api_requests"], 1)
        if error_rate > 0.05:  # 5% error rate
            anomalies.append("high_error_rate")
        
        return {
            "trends": {
                "cpu": cpu_trend,
                "memory": memory_trend,
                "response_time": response_time_trend
            },
            "anomalies": anomalies,
            "health_score": self._calculate_health_score(latest),
            "recommendations": self._generate_recommendations(anomalies, recent_points)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from a list of values."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_health_score(self, latest_data: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0
        
        # CPU penalty
        if latest_data["system"]["cpu_percent"]:
            if latest_data["system"]["cpu_percent"] > 80:
                score -= 20
            elif latest_data["system"]["cpu_percent"] > 60:
                score -= 10
        
        # Memory penalty
        if latest_data["system"]["memory_percent"]:
            if latest_data["system"]["memory_percent"] > 85:
                score -= 20
            elif latest_data["system"]["memory_percent"] > 70:
                score -= 10
        
        # Response time penalty
        if latest_data["application"]["avg_response_time"] > 2.0:
            score -= 15
        elif latest_data["application"]["avg_response_time"] > 1.0:
            score -= 5
        
        # Error rate penalty
        error_rate = latest_data["application"]["errors"] / max(latest_data["application"]["api_requests"], 1)
        if error_rate > 0.05:
            score -= 25
        elif error_rate > 0.01:
            score -= 10
        
        return max(0.0, score)
    
    def _generate_recommendations(self, anomalies: List[str], recent_points: List[Dict]) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if "high_cpu_usage" in anomalies:
            recommendations.append("Consider scaling horizontally or optimizing CPU-intensive operations")
        
        if "high_memory_usage" in anomalies:
            recommendations.append("Review memory usage patterns and consider increasing available memory")
        
        if "slow_response_time" in anomalies:
            recommendations.append("Optimize database queries and consider implementing caching")
        
        if "high_error_rate" in anomalies:
            recommendations.append("Investigate error logs and improve error handling")
        
        # Cache efficiency
        if recent_points:
            latest = recent_points[-1]["application"]
            cache_hit_rate = latest["cache_hits"] / max(latest["cache_hits"] + latest["cache_misses"], 1)
            if cache_hit_rate < 0.7:
                recommendations.append("Improve cache hit rate by optimizing cache keys and TTL")
        
        return recommendations
    
    async def start_monitoring(self, duration_minutes: int = None):
        """Start continuous monitoring."""
        self.running = True
        start_time = time.time()
        
        print(f"🔍 Starting performance monitoring (interval: {self.interval}s)")
        if duration_minutes:
            print(f"   Duration: {duration_minutes} minutes")
        
        try:
            while self.running:
                # Collect metrics
                system_metrics = await self.collect_system_metrics()
                app_metrics = await self.collect_application_metrics()
                
                data_point = {
                    "system": system_metrics,
                    "application": app_metrics
                }
                
                self.data_points.append(data_point)
                
                # Keep only last 100 data points
                if len(self.data_points) > 100:
                    self.data_points = self.data_points[-100:]
                
                # Analyze trends
                analysis = await self.analyze_performance_trends()
                
                # Print status
                self._print_status(data_point, analysis)
                
                # Check duration
                if duration_minutes and (time.time() - start_time) > (duration_minutes * 60):
                    break
                
                await asyncio.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        finally:
            self.running = False
    
    def _print_status(self, data_point: Dict[str, Any], analysis: Dict[str, Any]):
        """Print current status."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        system = data_point["system"]
        app = data_point["application"]
        
        print(f"\n[{timestamp}] Performance Status:")
        
        if system["cpu_percent"]:
            print(f"  CPU: {system['cpu_percent']:.1f}%")
        if system["memory_percent"]:
            print(f"  Memory: {system['memory_percent']:.1f}% ({system['memory_used_mb']:.0f} MB)")
        
        print(f"  API Requests: {app['api_requests']}")
        print(f"  Avg Response Time: {app['avg_response_time']:.3f}s")
        print(f"  Cache Hit Rate: {app['cache_hits'] / max(app['cache_hits'] + app['cache_misses'], 1) * 100:.1f}%")
        
        if analysis.get("health_score"):
            health_score = analysis["health_score"]
            health_emoji = "🟢" if health_score > 80 else "🟡" if health_score > 60 else "🔴"
            print(f"  Health Score: {health_emoji} {health_score:.1f}/100")
        
        if analysis.get("anomalies"):
            print(f"  ⚠️  Anomalies: {', '.join(analysis['anomalies'])}")
    
    def save_report(self, filename: str):
        """Save monitoring report to file."""
        report = {
            "monitoring_period": {
                "start": self.data_points[0]["system"]["timestamp"] if self.data_points else None,
                "end": self.data_points[-1]["system"]["timestamp"] if self.data_points else None,
                "data_points": len(self.data_points)
            },
            "data": self.data_points,
            "final_analysis": asyncio.run(self.analyze_performance_trends()) if self.data_points else {}
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Monitoring report saved to {filename}")


async def main():
    parser = argparse.ArgumentParser(description="Performance monitoring")
    parser.add_argument("--interval", type=int, default=60,
                       help="Monitoring interval in seconds")
    parser.add_argument("--duration", type=int,
                       help="Monitoring duration in minutes")
    parser.add_argument("--output", type=str,
                       help="Save report to file")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(interval=args.interval)
    
    try:
        await monitor.start_monitoring(duration_minutes=args.duration)
        
        if args.output:
            monitor.save_report(args.output)
            
    except Exception as e:
        print(f"❌ Monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())