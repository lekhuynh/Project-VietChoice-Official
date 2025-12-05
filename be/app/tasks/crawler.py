import os
from typing import Any, Dict, List

from ..database import SessionLocal
from ..rq_conn import crawl_queue
from ..services import crawler_tiki_service as tiki


def enqueue_crawl_keyword(keyword: str, limit: int = 10) -> str:
    """Push a crawl-by-keyword task to the queue."""
    job = crawl_queue.enqueue(
        run_crawl_keyword,
        keyword,
        limit=limit,
        job_timeout=900,
    )
    return job.id


def run_crawl_keyword(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Job body: reuse existing crawler logic with its own DB session."""
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


def enqueue_scan_image(tmp_path: str, filename: str | None = None) -> str:
    job = crawl_queue.enqueue(
        run_scan_image,
        tmp_path,
        filename,
        job_timeout=900,
    )
    return job.id


def run_scan_image(tmp_path: str, filename: str | None = None) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        results = tiki.crawl_by_image(db, tmp_path)
        return {
            "input_type": "image",
            "query": filename or os.path.basename(tmp_path),
            "count": len(results or []),
            "results": results or [],
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        db.close()


def enqueue_scan_barcode_image(tmp_path: str) -> str:
    job = crawl_queue.enqueue(
        run_scan_barcode_image,
        tmp_path,
        job_timeout=900,
    )
    return job.id


def run_scan_barcode_image(tmp_path: str) -> Dict[str, Any]:
    from ..services import barcode_service

    db = SessionLocal()
    try:
        codes = barcode_service.decode_barcodes(tmp_path) or []
        best = codes[0] if codes else None
        results: list[dict] = []
        if best:
            results = tiki.crawl_by_barcode(db, best) or []
        return {
            "input_type": "barcode_image",
            "codes": codes,
            "best_code": best,
            "count": len(results),
            "results": results,
        }
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        db.close()
