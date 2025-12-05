from typing import Any, Dict, Optional

from app.database import SessionLocal  # type: ignore
from app.rq_conn import auto_update_queue  # type: ignore
from app.services.auto_update_service import auto_update_products  # type: ignore


def enqueue_auto_update(
    older_than_hours: int = 24,
    limit: Optional[int] = 50,
    workers: int = 4,
) -> str:
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
