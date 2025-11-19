"""
Celery configuration for PyPSA App
"""

import logging

from pypsa_app.backend.settings import settings

logger = logging.getLogger(__name__)

try:
    from celery import Celery

    celery_app = Celery(
        "pypsa_app",
        broker=settings.redis_url,
        backend=settings.redis_url,
        include=["pypsa_app.backend.tasks"],
    )

    celery_app.conf.update(
        accept_content=["json"],
        result_expires=86400,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=10,
        task_soft_time_limit=3600,
        task_time_limit=7200,
        task_acks_late=True,
    )
except ImportError:
    logger.warning(
        "Celery not available - background tasks disabled",
        extra={
            "celery_available": False,
            "background_tasks_enabled": False,
        },
    )

    # DummyCelery that won't crash imports
    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    celery_app = DummyCelery()
