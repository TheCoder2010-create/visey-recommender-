#!/usr/bin/env python3
"""
Quick Test Script - Tests core functionality without external dependencies
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from visey_recommender.config import settings
        print("✅ Config imported")
        
        from visey_recommender.clients.wp_client import WPClient
        print("✅ WordPress client imported")
        
        from visey_recommender.services.wp_service import WordPressService
        print("✅ WordPress service imported")
        
        from visey_recommender.recommender.baseline import BaselineRecommender
        print("✅ Recommender imported")
        
        from visey_recommender.api.main import app
        print("✅ FastAPI app imported")
        
        from visey_recommender.utils.health import health_checker
        print("✅ Health checker imported")
        
        from visey_recommender.utils.metrics import metrics
        print("✅ Metrics imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality without external dependencies"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test config
        from visey_recommender.config import settings
        print(f"✅ Config loaded - WP_BASE_URL: {settings.WP_BASE_URL[:30]}...")
        
        # Test recommender
        from visey_recommender.recommender.baseline import BaselineRecommender
        from visey_recommender.data.models import UserProfile, Resource
        
        recommender = BaselineRecommender()
        
        # Create test data
        profile = UserProfile(
            user_id=1,
            industry="technology",
            stage="growth",
            team_size="10-50",
            funding="series-a",
            location="San Francisco"
        )
        
        resources = [
            Resource(
                id=1,
                title="AI for Startups",
                link="https://example.com/ai-startups",
                categories=[1, 2],
                tags=[3, 4],
                meta={"difficulty": "intermediate"}
            ),
            Resource(
                id=2,
                title="Funding Guide",
                link="https://example.com/funding",
                categories=[2, 5],
                tags=[6, 7],
                meta={"difficulty": "beginner"}
            )
        ]
        
        # Generate recommendations
        recommendations = recommender.recommend(profile, resources, top_n=5)
        print(f"✅ Generated {len(recommendations)} recommendations")
        
        for rec in recommendations:
            print(f"   - {rec.title} (score: {rec.score:.3f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

async def test_health_checker():
    """Test health checker"""
    print("\n🏥 Testing health checker...")
    
    try:
        from visey_recommender.utils.health import health_checker
        
        # Run basic health checks
        health_result = await health_checker.get_liveness()
        print(f"✅ Liveness check: {health_result.get('alive', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health checker test failed: {e}")
        return False

async def test_wordpress_client():
    """Test WordPress client (without making actual requests)"""
    print("\n🌐 Testing WordPress client...")
    
    try:
        from visey_recommender.clients.wp_client import WPClient
        
        # Test client initialization
        client = WPClient(
            base_url="https://demo.wp-api.org",
            auth_type="none"
        )
        
        print("✅ WordPress client initialized")
        print(f"   Base URL: {client.base_url}")
        print(f"   Auth Type: {client.auth_type}")
        
        # Test auth headers
        headers = client._auth_headers()
        print(f"✅ Auth headers generated: {len(headers)} headers")
        
        return True
        
    except Exception as e:
        print(f"❌ WordPress client test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 VISEY RECOMMENDER QUICK TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Health Checker", test_health_checker),
        ("WordPress Client", test_wordpress_client)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)