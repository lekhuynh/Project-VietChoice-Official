from typing import Any, Dict, List

from app.database import SessionLocal  # type: ignore
from app.rq_conn import crawl_queue  # type: ignore
from app.services import crawler_tiki_service as tiki  # type: ignore


def enqueue_crawl_keyword(keyword: str, limit: int = 10) -> str:
    job = crawl_queue.enqueue(
        run_crawl_keyword,
        keyword,
        limit=limit,
        job_timeout=900,
    )
    return job.id


def run_crawl_keyword(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        return tiki.search_and_crawl_tiki_products_fast(db, keyword=keyword, limit=limit)
    finally:
        db.close()


def enqueue_crawl_by_id(product_id: int) -> str:
    job = crawl_queue.enqueue(
        run_crawl_by_id,
        product_id,
        job_timeout=900,
    )
    return job.id


def run_crawl_by_id(product_id: int) -> Dict[str, Any] | None:
    db = SessionLocal()
    try:
        return tiki.crawl_and_save_tiki_product(db, product_id)
    finally:
        db.close()


def enqueue_crawl_barcode(barcode: str) -> str:
    job = crawl_queue.enqueue(
        run_crawl_barcode,
        barcode,
        job_timeout=900,
    )
    return job.id


def run_crawl_barcode(barcode: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    try:
        return tiki.crawl_by_barcode(db, barcode)
    finally:
        db.close()
