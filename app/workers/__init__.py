"""Background workers for the automation pipeline."""

from app.workers.automation_worker import AutomationWorker

__all__ = [
    "AutomationWorker",
]
