"""Cron scheduler for automated tasks"""
import asyncio
from typing import Callable, Awaitable, Optional
from datetime import datetime
from croniter import croniter
from app.core.logging import get_logger

logger = get_logger(__name__)


class CronScheduler:
    """Simple cron-based task scheduler"""

    def __init__(self):
        self.tasks = []
        self._running = False
        self._task = None

    def add_task(
        self,
        name: str,
        cron_expression: str,
        func: Callable[[], Awaitable[None]],
    ) -> None:
        """
        Add a scheduled task

        Args:
            name: Task name
            cron_expression: Cron expression (e.g., "0 2 * * *" for 2 AM daily)
            func: Async function to execute
        """
        self.tasks.append({
            "name": name,
            "cron": cron_expression,
            "func": func,
            "last_run": None,
        })
        logger.info(f"Scheduled task: {name} ({cron_expression})")

    async def run(self) -> None:
        """Start the scheduler"""
        self._running = True
        logger.info("Cron scheduler started")

        while self._running:
            now = datetime.now()

            for task in self.tasks:
                cron = croniter(task["cron"], now)
                next_run = cron.get_next(datetime)

                # Check if it's time to run
                if task["last_run"] is None or now >= next_run:
                    try:
                        logger.info(f"Running scheduled task: {task['name']}")
                        await task["func"]()
                        task["last_run"] = now
                    except Exception as e:
                        logger.error(f"Error in scheduled task {task['name']}: {str(e)}")

            # Sleep for 60 seconds
            await asyncio.sleep(60)

    def start(self) -> None:
        """Start scheduler in background"""
        if not self._running:
            self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        """Stop the scheduler"""
        self._running = False
        if self._task:
            await self._task


# Global scheduler instance
_scheduler: Optional[CronScheduler] = None


def get_scheduler() -> CronScheduler:
    """Get global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CronScheduler()
    return _scheduler
