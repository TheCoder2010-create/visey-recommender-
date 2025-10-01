"""Background task scheduler for WordPress data synchronization."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from ..services.wp_service import WordPressService
from ..utils.metrics import track_operation


class WordPressScheduler:
    """Scheduler for periodic WordPress data synchronization."""

    def __init__(self, wp_service: Optional[WordPressService] = None):
        self.wp_service = wp_service or WordPressService()
        self.logger = logging.getLogger(__name__)
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self, sync_interval_minutes: int = 30):
        """Start the background sync scheduler.
        
        Args:
            sync_interval_minutes: How often to sync data (default: 30 minutes)
        """
        if self._running:
            self.logger.warning("Scheduler already running")
            return

        self._running = True
        self.logger.info(f"Starting WordPress sync scheduler (interval: {sync_interval_minutes}m)")
        
        self._task = asyncio.create_task(
            self._sync_loop(sync_interval_minutes)
        )

    async def stop(self):
        """Stop the background sync scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        self.logger.info("WordPress sync scheduler stopped")

    async def _sync_loop(self, interval_minutes: int):
        """Main sync loop."""
        interval_seconds = interval_minutes * 60
        
        while self._running:
            try:
                await self._perform_sync()
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Sync loop error: {str(e)}")
                # Wait a bit before retrying on error
                await asyncio.sleep(60)

    @track_operation("wp_scheduled_sync")
    async def _perform_sync(self):
        """Perform the actual sync operation."""
        try:
            self.logger.info("Starting scheduled WordPress sync")
            
            # Check if sync is needed (avoid too frequent syncs)
            last_sync = await self.wp_service._get_last_sync_time()
            if last_sync:
                time_since_sync = datetime.now().replace(tzinfo=last_sync.tzinfo) - last_sync
                if time_since_sync < timedelta(minutes=15):
                    self.logger.debug("Skipping sync - too recent")
                    return

            # Perform incremental sync
            result = await self.wp_service.sync_all_data(incremental=True)
            
            self.logger.info(
                "Scheduled WordPress sync completed",
                posts=result.posts_synced,
                users=result.users_synced,
                categories=result.categories_synced,
                tags=result.tags_synced,
                duration=result.sync_duration,
                errors=len(result.errors)
            )
            
            if result.errors:
                self.logger.warning("Sync completed with errors", errors=result.errors)

        except Exception as e:
            self.logger.error(f"Scheduled sync failed: {str(e)}")

    async def force_sync(self, incremental: bool = True):
        """Force an immediate sync operation.
        
        Args:
            incremental: Whether to perform incremental sync
            
        Returns:
            Sync result
        """
        self.logger.info(f"Force sync triggered (incremental: {incremental})")
        return await self.wp_service.sync_all_data(incremental=incremental)

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._running


# Global scheduler instance
wp_scheduler = WordPressScheduler()