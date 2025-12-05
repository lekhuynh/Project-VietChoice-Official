from typing import Any, Dict, Optional, List

from ..database import SessionLocal
from ..rq_conn import auto_update_queue
from ..services.auto_update_service import auto_update_products
from ..crud import products as product_crud


def enqueue_auto_update_chunked(chunk_size: int = 50, older_than_hours: int = 24, workers: int = 4) -> str:
    job = auto_update_queue.enqueue(
        run_auto_update_chunked,
        chunk_size,
        older_than_hours,
        workers,
        job_timeout=1800,
    )
    return job.id


def run_auto_update_chunked(chunk_size: int = 50, older_than_hours: int = 24, workers: int = 4) -> Dict[str, Any]:
    """
    Enqueue auto update in smaller chunks to reduce load per job.
    """
    db = SessionLocal()
    try:
        products = product_crud.get_tiki_products_older_than(db, hours=older_than_hours)
        ids: List[int] = [int(p.External_ID) for p in products if p.External_ID]
        chunks = [ids[i:i + chunk_size] for i in range(0, len(ids), chunk_size)]
        stats: Dict[str, Any] = {"total_chunks": len(chunks), "submitted": len(chunks)}
        for chunk in chunks:
            auto_update_queue.enqueue(
                run_auto_update_subset,
                chunk,
                workers,
                job_timeout=1800,
            )
        return stats
    finally:
        db.close()


def run_auto_update_subset(external_ids: list[int], workers: int = 4) -> Dict[str, Any]:
    """
    Update a subset of products by External_ID list.
    """
    db = SessionLocal()
    try:
        return auto_update_products(
            db,
            older_than_hours=0,
            limit=None,
            workers=workers,
            only_external_ids=external_ids,
        )
    finally:
        db.close()
