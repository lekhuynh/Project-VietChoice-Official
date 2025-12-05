from typing import Any, Dict, Optional

from ..database import SessionLocal
from ..rq_conn import crawl_queue
from ..services import crawler_tiki_service as tiki
from ..crud import products as product_crud


def enqueue_update_sentiment(product_id: int) -> str:
    job = crawl_queue.enqueue(
        run_update_sentiment,
        product_id,
        job_timeout=600,
    )
    return job.id


def run_update_sentiment(product_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        product = product_crud.get_by_id(db, product_id)
        if not product or not product.External_ID:
            return {"product_id": product_id, "status": "not_found_or_missing_external_id"}
        score = tiki.update_sentiment_from_tiki_reviews(db, int(product.External_ID))
        return {"product_id": product_id, "external_id": product.External_ID, "sentiment_score": score}
    finally:
        db.close()
