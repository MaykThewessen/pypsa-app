"""Celery configuration and in-memory task queue fallback"""

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from pypsa_app.backend.settings import settings

logger = logging.getLogger(__name__)

_tasks = {}
_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="task")


class InMemoryAsyncResult:
    def __init__(self, task_id):
        self.id = task_id

    @property
    def state(self):
        with _lock:
            return _tasks.get(self.id, {}).get("state", "PENDING")

    @property
    def result(self):
        with _lock:
            t = _tasks.get(self.id, {})
            return t.get("result") if t.get("state") == "SUCCESS" else None

    @property
    def info(self):
        with _lock:
            t = _tasks.get(self.id, {})
            if t.get("state") == "FAILURE":
                return t.get("exception")
            if t.get("state") == "PROGRESS":
                return t.get("meta", {})
            return None


class InMemoryTaskQueue:
    def task(self, *args, **kwargs):
        bind = kwargs.get("bind", False)

        def decorator(func):
            def apply_async(args=(), kwargs=None, **options):
                tid = str(uuid.uuid4())
                now = datetime.now(timezone.utc)

                with _lock:
                    _tasks[tid] = {"state": "PENDING", "created_at": now}
                    cutoff = now - timedelta(hours=24)
                    for k in list(_tasks.keys()):
                        if _tasks[k].get("created_at", cutoff) < cutoff:
                            del _tasks[k]

                class Task:
                    request = type("Request", (), {"id": tid})()

                    @staticmethod
                    def update_state(state=None, meta=None):
                        with _lock:
                            if tid in _tasks and state:
                                _tasks[tid]["state"] = state
                            if tid in _tasks and meta:
                                _tasks[tid]["meta"] = meta

                def run():
                    try:
                        res = (
                            func(Task(), *args, **(kwargs or {}))
                            if bind
                            else func(*args, **(kwargs or {}))
                        )
                        with _lock:
                            _tasks[tid].update({"state": "SUCCESS", "result": res})
                    except Exception as e:
                        with _lock:
                            _tasks[tid].update(
                                {"state": "FAILURE", "exception": str(e)}
                            )
                        logger.error(
                            "Task failed",
                            extra={"task_id": tid, "error": str(e)},
                            exc_info=True,
                        )

                _pool.submit(run)
                return InMemoryAsyncResult(tid)

            func.apply_async = apply_async
            func.name = kwargs.get("name", func.__name__)
            return func

        return decorator


# Try to use Celery with Redis, fall back to in-memory task queue
try:
    from celery import Celery

    # Only use real Celery if Redis URL is configured
    if not settings.redis_url:
        logger.warning(
            "Redis URL not configured - using in-memory task queue",
            extra={"backend": "in-memory", "background_tasks_enabled": True},
        )
        task_app = InMemoryTaskQueue()
    else:
        task_app = Celery(
            "pypsa_app",
            broker=settings.redis_url,
            backend=settings.redis_url,
            include=["pypsa_app.backend.tasks"],
        )

        task_app.conf.update(
            accept_content=["json"],
            result_expires=86400,
            worker_prefetch_multiplier=1,
            worker_max_tasks_per_child=10,
            task_soft_time_limit=3600,
            task_time_limit=7200,
            task_acks_late=True,
        )

        logger.info(
            "Initialized Celery with Redis backend",
            extra={"redis_url": settings.redis_url, "backend": "celery"},
        )

except ImportError:
    logger.warning(
        "Celery not installed - using in-memory task queue",
        extra={"backend": "in-memory", "background_tasks_enabled": True},
    )
    task_app = InMemoryTaskQueue()
