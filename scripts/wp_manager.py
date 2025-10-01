#!/usr/bin/env python3
"""WordPress integration management CLI."""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from visey_recommender.clients.wp_client import WPClient
from visey_recommender.services.wp_service import WordPressService
from visey_recommender.config import settings
from visey_recommender.utils.logging import setup_logging, get_logger


async def test_connection():
    """Test WordPress API connection."""
    print("Testing WordPress API connection...")
    
    client = WPClient()
    health = await client.health_check()
    
    print(f"Status: {health['status']}")
    print(f"Base URL: {health['base_url']}")
    print(f"Auth Type: {health['auth_type']}")
    print(f"Auth Status: {health['auth_status']}")
    
    if health['status'] == 'healthy':
        print("✅ WordPress API connection successful!")
        
        # Get site info
        site_info = await client.get_site_info()
        print(f"Site Name: {site_info.get('name', 'N/A')}")
        print(f"Site URL: {site_info.get('url', 'N/A')}")
        print(f"Available Namespaces: {', '.join(site_info.get('namespaces', []))}")
    else:
        print("❌ WordPress API connection failed!")
        if 'error' in health:
            print(f"Error: {health['error']}")
    
    return health['status'] == 'healthy'


async def sync_data(incremental=True, data_type=None):
    """Synchronize WordPress data."""
    print(f"Starting WordPress data sync (incremental: {incremental})...")
    
    service = WordPressService()
    
    if data_type:
        print(f"Syncing {data_type} only...")
        if data_type == "users":
            count = await service._sync_users()
            print(f"✅ Synced {count} users")
        elif data_type == "posts":
            count = await service._sync_posts()
            print(f"✅ Synced {count} posts")
        elif data_type == "categories":
            count = await service._sync_categories()
            print(f"✅ Synced {count} categories")
        elif data_type == "tags":
            count = await service._sync_tags()
            print(f"✅ Synced {count} tags")
        else:
            print(f"❌ Unknown data type: {data_type}")
            return False
    else:
        result = await service.sync_all_data(incremental=incremental)
        
        print(f"✅ Sync completed in {result.sync_duration:.2f} seconds")
        print(f"Users synced: {result.users_synced}")
        print(f"Posts synced: {result.posts_synced}")
        print(f"Categories synced: {result.categories_synced}")
        print(f"Tags synced: {result.tags_synced}")
        
        if result.errors:
            print("⚠️  Errors encountered:")
            for error in result.errors:
                print(f"  - {error}")
    
    return True


async def show_status():
    """Show WordPress integration status."""
    print("WordPress Integration Status")
    print("=" * 40)
    
    service = WordPressService()
    
    # Health check
    health = await service.health_check()
    print(f"Service Status: {health.get('service_status', 'unknown')}")
    print(f"WordPress API: {health['wordpress_api']['status']}")
    print(f"Cache: {'healthy' if health['cache_healthy'] else 'unhealthy'}")
    
    # Sync status
    sync_status = await service.get_sync_status()
    print(f"Last Sync: {sync_status['last_sync'] or 'Never'}")
    print(f"Cache Status: {sync_status['cache_status']}")
    
    print("\nCached Data Counts:")
    for data_type, count in sync_status['data_counts'].items():
        print(f"  {data_type.capitalize()}: {count}")
    
    print(f"\nConfiguration:")
    print(f"  Sync Interval: {settings.WP_SYNC_INTERVAL} minutes")
    print(f"  Cache Fallback: {settings.WP_CACHE_FALLBACK}")
    print(f"  Rate Limit: {settings.WP_RATE_LIMIT} req/min")
    print(f"  Batch Size: {settings.WP_BATCH_SIZE}")
    
    # Show recommendation strategy
    print(f"\nRecommendation Strategy:")
    if settings.WP_CACHE_FALLBACK:
        print("  ✅ Cache-first (recommended for production)")
        print("  - User profiles: cached with real-time fallback")
        print("  - Posts: cached data only")
        print("  - Background sync every", settings.WP_SYNC_INTERVAL, "minutes")
    else:
        print("  ⚠️  Real-time API calls (not recommended for production)")
        print("  - Every recommendation hits WordPress API")
        print("  - Higher latency and WordPress load")


async def search_content(query, limit=10):
    """Search WordPress content."""
    print(f"Searching for: '{query}'")
    print("-" * 40)
    
    service = WordPressService()
    results = await service.search_content(query, limit=limit)
    
    if not results:
        print("No results found.")
        return
    
    for i, post in enumerate(results, 1):
        print(f"{i}. {post['title']}")
        print(f"   URL: {post['link']}")
        print(f"   Date: {post['date']}")
        if post['excerpt']:
            excerpt = post['excerpt'][:100] + "..." if len(post['excerpt']) > 100 else post['excerpt']
            print(f"   Excerpt: {excerpt}")
        print()


async def get_user_profile(user_id):
    """Get WordPress user profile."""
    print(f"Fetching profile for user ID: {user_id}")
    print("-" * 40)
    
    service = WordPressService()
    profile = await service.get_user_profile(user_id)
    
    if not profile:
        print("User not found or error occurred.")
        return
    
    print(f"Name: {profile.get('name', 'N/A')}")
    print(f"Email: {profile.get('email', 'N/A')}")
    print(f"Industry: {profile.get('industry', 'N/A')}")
    print(f"Stage: {profile.get('stage', 'N/A')}")
    print(f"Team Size: {profile.get('team_size', 'N/A')}")
    print(f"Funding: {profile.get('funding', 'N/A')}")
    print(f"Location: {profile.get('location', 'N/A')}")
    print(f"Registered: {profile.get('registered_date', 'N/A')}")


async def export_data(data_type, output_file):
    """Export cached WordPress data to JSON file."""
    print(f"Exporting {data_type} data to {output_file}...")
    
    service = WordPressService()
    data = await service.get_cached_data(data_type)
    
    if not data:
        print(f"No cached {data_type} data found.")
        return
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"✅ Exported {len(data)} {data_type} records to {output_file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="WordPress Integration Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test connection
    subparsers.add_parser('test', help='Test WordPress API connection')
    
    # Sync data
    sync_parser = subparsers.add_parser('sync', help='Synchronize WordPress data')
    sync_parser.add_argument('--full', action='store_true', help='Full sync (not incremental)')
    sync_parser.add_argument('--type', choices=['users', 'posts', 'categories', 'tags'], 
                           help='Sync specific data type only')
    
    # Show status
    subparsers.add_parser('status', help='Show integration status')
    
    # Search content
    search_parser = subparsers.add_parser('search', help='Search WordPress content')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Number of results')
    
    # Get user profile
    user_parser = subparsers.add_parser('user', help='Get user profile')
    user_parser.add_argument('user_id', type=int, help='WordPress user ID')
    
    # Export data
    export_parser = subparsers.add_parser('export', help='Export cached data')
    export_parser.add_argument('type', choices=['users', 'posts', 'categories', 'tags'],
                              help='Data type to export')
    export_parser.add_argument('output', help='Output JSON file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging(level="INFO", json_logs=False)
    
    # Check configuration
    if not settings.WP_BASE_URL:
        print("❌ WP_BASE_URL not configured. Please set the environment variable.")
        sys.exit(1)
    
    # Run command
    try:
        if args.command == 'test':
            success = asyncio.run(test_connection())
            sys.exit(0 if success else 1)
        elif args.command == 'sync':
            success = asyncio.run(sync_data(
                incremental=not args.full,
                data_type=args.type
            ))
            sys.exit(0 if success else 1)
        elif args.command == 'status':
            asyncio.run(show_status())
        elif args.command == 'search':
            asyncio.run(search_content(args.query, args.limit))
        elif args.command == 'user':
            asyncio.run(get_user_profile(args.user_id))
        elif args.command == 'export':
            asyncio.run(export_data(args.type, args.output))
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()