from typing import Any, Dict

from ..database import SessionLocal
from ..rq_conn import crawl_queue
from ..services.risk_service import evaluate_risk
from ..models.products import Products


def enqueue_risk_score(product_id: int) -> str:
    job = crawl_queue.enqueue(
        run_risk_score,
        product_id,
        job_timeout=300,
    )
    return job.id


def run_risk_score(product_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        product = db.query(Products).filter(Products.Product_ID == product_id).first()
        if not product:
            return {"product_id": product_id, "status": "not_found"}
        risk = evaluate_risk(product, db)
        return {"product_id": product_id, **risk}
    finally:
        db.close()
