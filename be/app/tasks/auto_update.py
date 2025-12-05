from typing import Any, Dict, Optional

from ..database import SessionLocal
from ..rq_conn import auto_update_queue
from ..services.auto_update_service import auto_update_products


def enqueue_auto_update(
    older_than_hours: int = 24,
    limit: Optional[int] = 50,
    workers: int = 4,
) -> str:
    """Push an auto-update batch into the background queue."""
    job = auto_update_queue.enqueue(
        run_auto_update,
        older_than_hours=older_than_hours,
        limit=limit,
        workers=workers,
        job_timeout=1800,
    )
    return job.id


def run_auto_update(
    older_than_hours: int = 24,
    limit: Optional[int] = 50,
    workers: int = 4,
) -> Dict[str, Any]:
    """Job body executed by the worker process."""
    db = SessionLocal()
    try:
        return auto_update_products(
            db,
            older_than_hours=older_than_hours,
            limit=limit,
            workers=workers,
        )
    finally:
        db.close()
